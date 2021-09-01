import json
import pickle
import math
from collections import defaultdict

FORWARDS = True
BACKWARDS = False
EARTH_RADIUS = 6378137.0

def is_acute(a, b, c):
    # a, b, c are lists of lat lon coords each. The angle in question is ABC.
    # Essentially, we are asking, is the dot product positive
    return ((a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1])) > 0

def get_zone(coord):
    return (int(coord[0] // 1000), int(coord[1] // 1000))

def latlon_to_mercator(coord):
    # Adapted from https://wiki.openstreetmap.org/wiki/Mercator
    # this algorithm (pseudo-Mercator) treats the earth as a sphere
    lon, lat = coord
    x = math.radians(lon) * EARTH_RADIUS
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * EARTH_RADIUS
    return (x,y)


def convert(sources, dest):
    """Format of join entries:
    startjoin/endjoin: None or (ID#, point on that ID#, dir)
    middlejoin: {(point, dir): (ID, pt, dir)}
    """

    def is_end(point):
        id, index = point
        return len(dest_structure[id]["coordinates"]) == index + 1

    def is_start(point):
        id, index = point
        return index == 0

    dest_structure = {}
    for source in sources:
        with open(source) as f:
            data = json.load(f)
        for feature in data["features"]:
            if feature["geometry"]["type"] == "LineString":
                id = int(feature["properties"]["@id"][4:])
                # Remove "way/" from start of id number
                dest_structure[id] = {}
                dest_structure[id]["coordinates"] = \
                    [latlon_to_mercator(i) for i in feature["geometry"]["coordinates"]]
                dest_structure[id]["startjoin"] = []
                dest_structure[id]["endjoin"] = []
                dest_structure[id]["middlejoins"] = {}
    intersections = defaultdict(set)
    for id in dest_structure:
        last_point = len(dest_structure[id]["coordinates"]) - 1
        # print(f"{ctr} of {num_ids}")
        start = dest_structure[id]["coordinates"][0]
        end = dest_structure[id]["coordinates"][-1]
        intersections[tuple(start)].add((id,0))
        intersections[tuple(end)].add((id,last_point))
    for test_id in dest_structure:
        i = 0
        for point in dest_structure[test_id]["coordinates"]:
            if tuple(point) in intersections:
                intersections[tuple(point)].add((test_id, i))
            i += 1

    for inter in intersections:
        if len(intersections[inter]) == 1:
            pass
        elif len(intersections[inter]) == 2:
            a, b = list(intersections[inter])
            # Sometimes, there might be two tracks stuck together end to end
            if is_start(a) and is_start(b):
                dest_structure[a[0]]["startjoin"].append((b[0],b[1], FORWARDS))
                dest_structure[b[0]]["startjoin"].append((a[0], a[1], FORWARDS))
            elif is_start(a) and is_end(b):
                dest_structure[a[0]]["startjoin"].append((b[0], b[1], BACKWARDS))
                dest_structure[b[0]]["endjoin"].append((a[0], a[1], FORWARDS))
            elif is_end(a) and is_start(b):
                dest_structure[a[0]]["endjoin"].append((b[0], b[1], FORWARDS))
                dest_structure[b[0]]["startjoin"].append((a[0], a[1], BACKWARDS))
            elif is_end(a) and is_end(b):
                dest_structure[a[0]]["endjoin"].append((b[0], b[1], BACKWARDS))
                dest_structure[b[0]]["endjoin"].append((a[0], b[1], BACKWARDS))
            # But normally, if there are two tracks it's because one of them is
            # sticking to the middle of the other one.
            elif is_start(a):
                vertex = dest_structure[a[0]]["coordinates"][0]
                next_on_a = dest_structure[a[0]]["coordinates"][1]
                next_on_b = dest_structure[b[0]]["coordinates"][b[1] + 1]
                if is_acute(next_on_a, vertex, next_on_b):
                    # Case A
                    dest_structure[a[0]]["startjoin"].append((b[0],b[1],BACKWARDS))
                    dest_structure[b[0]]["middlejoins"][(b[1], FORWARDS)] = \
                        (a[0],a[1],FORWARDS)
                else:
                    # Case D
                    dest_structure[a[0]]["startjoin"].append((b[0], b[1], FORWARDS))
                    dest_structure[b[0]]["middlejoins"][(b[1], BACKWARDS)] = \
                        (a[0], a[1], FORWARDS)
            elif is_start(b):
                vertex = dest_structure[b[0]]["coordinates"][0]
                next_on_a = dest_structure[b[0]]["coordinates"][1]
                next_on_b = dest_structure[a[0]]["coordinates"][a[1] + 1]
                if is_acute(next_on_a, vertex, next_on_b):
                    # Case A
                    dest_structure[b[0]]["startjoin"].append((a[0], a[1], BACKWARDS))
                    dest_structure[a[0]]["middlejoins"][(a[1], FORWARDS)] = \
                        (b[0], b[1], FORWARDS)
                else:
                    # Case D
                    dest_structure[b[0]]["startjoin"].append((a[0], a[1], FORWARDS))
                    dest_structure[a[0]]["middlejoins"][(a[1], BACKWARDS)] = \
                        (b[0], b[1], FORWARDS)
            elif is_end(a):
                vertex = dest_structure[a[0]]["coordinates"][-1]
                prev_on_a = dest_structure[a[0]]["coordinates"][-2]
                prev_on_b = dest_structure[b[0]]["coordinates"][b[1] - 1]
                if is_acute(prev_on_a, vertex, prev_on_b):
                    # Case C
                    dest_structure[a[0]]["endjoin"] = (b[0], b[1], FORWARDS)
                    dest_structure[b[0]]["middlejoins"][(b[1], BACKWARDS)] = \
                        (a[0], a[1], BACKWARDS)
                else:
                    # Case B
                    dest_structure[a[0]]["endjoin"] = (b[0], b[1], BACKWARDS)
                    dest_structure[b[0]]["middlejoins"][(b[1], FORWARDS)] = \
                        (a[0], a[1], BACKWARDS)
            elif is_end(b):
                vertex = dest_structure[b[0]]["coordinates"][-1]
                prev_on_b = dest_structure[b[0]]["coordinates"][-2]
                prev_on_a = dest_structure[a[0]]["coordinates"][a[1] - 1]
                if is_acute(prev_on_a, vertex, prev_on_b):
                    # Case C
                    dest_structure[b[0]]["endjoin"] = (a[0], a[1], FORWARDS)
                    dest_structure[a[0]]["middlejoins"][(a[1], BACKWARDS)] = \
                        (b[0], b[1], BACKWARDS)
                else:
                    # Case B
                    dest_structure[b[0]]["endjoin"] = (a[0], a[1], BACKWARDS)
                    dest_structure[a[0]]["middlejoins"][(a[1], FORWARDS)] = \
                        (b[0], b[1], BACKWARDS)
            else:
                raise ValueError("Somehow the join is wrong")
        elif len(intersections[inter]) == 3:
            # do stuff
            a, b, c = list(intersections[inter])
            if not ((is_start(a) or is_end(a))
                    and (is_start(b) or is_end(b))
                    and (is_start(c) or is_end(c))):
                print(
                    f"3 way intersection with some of the lines not at their endpoints, {inter}: {intersections[inter]}")
            vertex = dest_structure[a[0]]["coordinates"][a[1]]
            next_on_a = dest_structure[a[0]]["coordinates"][a[1] + 1] \
                if is_start(a) \
                else dest_structure[a[0]]["coordinates"][a[1] - 1]
            next_on_b = dest_structure[b[0]]["coordinates"][b[1] + 1] \
                if is_start(b) \
                else dest_structure[b[0]]["coordinates"][b[1] - 1]
            next_on_c = dest_structure[c[0]]["coordinates"][c[1] + 1] \
                if is_start(c) \
                else dest_structure[c[0]]["coordinates"][c[1] - 1]
            ab_acute = is_acute(next_on_a, vertex, next_on_b)
            ac_acute = is_acute(next_on_a, vertex, next_on_c)
            bc_acute = is_acute(next_on_b, vertex, next_on_c)
            if (ab_acute and (not ac_acute) and (not bc_acute)):
                opp = c
                sp1 = a
                sp2 = b
            elif (ac_acute and (not ab_acute) and (not bc_acute)):
                opp = b
                sp1 = a
                sp2 = c
            elif (bc_acute and (not ab_acute) and (not ac_acute)):
                opp = a
                sp1 = b
                sp2 = c
            else:
                print(f"2 acute angles: {inter}: {intersections[inter]}")
            if is_end(opp):
                opp_joiner = (opp[0], opp[1], BACKWARDS)
                opp_place = "endjoin"
            else:
                opp_joiner = (opp[0], opp[1], FORWARDS)
                opp_place = "startjoin"
            if is_end(sp1):
                sp1_joiner = (sp1[0], sp1[1], BACKWARDS)
                sp1_place = "endjoin"
            else:
                sp1_joiner = (sp1[0], sp1[1], FORWARDS)
                sp1_place = "startjoin"
            if is_end(sp2):
                sp2_joiner = (sp2[0], sp2[1], BACKWARDS)
                sp2_place = "endjoin"
            else:
                sp2_joiner = (sp2[0], sp2[1], FORWARDS)
                sp2_place = "startjoin"

            dest_structure[opp[0]][opp_place].append(sp1_joiner)
            dest_structure[opp[0]][opp_place].append(sp2_joiner)
            dest_structure[sp1[0]][sp1_place].append(opp_joiner)
            dest_structure[sp2[0]][sp2_place].append(opp_joiner)
        else:
            print(f"There should only be 2 or three rails at an intersection: {inter}: {intersections[inter]}")
    for id in dest_structure:
        zones = set()
        for point in dest_structure[id]["coordinates"]:
            zones.add(get_zone(point))
        dest_structure[id]["zones"] = zones
    for id in dest_structure:
        dest_structure[id]["distances"] = \
            [0 for _ in range(len(dest_structure[id]["coordinates"]))]
        for j in range(len(dest_structure[id]["coordinates"]) - 1):
            dest_structure[id]["distances"][j] = math.dist(
                dest_structure[id]["coordinates"][j],
                dest_structure[id]["coordinates"][j + 1])
    print(dest_structure)
    with open(dest, 'wb') as dest_file:
        pickle.dump(dest_structure, dest_file)
convert(["California.geojson","Oregon.geojson","Washington.geojson"], "PNW.pickle")