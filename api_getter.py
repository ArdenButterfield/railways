import overpy

api = overpy.Overpass()
# fetch all ways and nodes
result = api.query("""{{geocodeArea:"United States"}}->.searchArea;
way[railway=preserved](area.searchArea)->.a;
foreach .a (
  way.a(around:400);
  way._(if:count(ways) == 1);
  out center;
);
    """)
print(result)
"""
for way in result.ways:
    print("Name: %s" % way.tags.get("name", "n/a"))
    print("  Highway: %s" % way.tags.get("highway", "n/a"))
    print("  Nodes:")
    for node in way.nodes:
        print("    Lat: %f, Lon: %f" % (node.lat, node.lon))"""