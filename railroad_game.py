import pickle
import pygame

FORWARDS = True
BACKWARDS = False
LEFT_BLINK = -1
NO_BLINK = 0
RIGHT_BLINK = 1

with open("data/RedmondOR.pickle", 'rb') as f:
    MAP_DATA = pickle.load(f)
print(MAP_DATA)

def which_side(a,vert,b):
    # Which side is vector from vert to b, relative to vector from vert to a?
    # Uses the dot product, as described here:
    # https://stackoverflow.com/questions/13221873/
    rot_b = (vert[1] - b[1], b[0] - vert[0])
    # Rotated 90 deg counter clockwise, centered at 0
    a = (a[0] - vert[0], a[1] - vert[1]) # centered at 0
    dot_prod = a[0] * rot_b[0] + a[1] * rot_b[1]
    return LEFT_BLINK if dot_prod < 0 else RIGHT_BLINK

class Train():
    def __init__(self, track_id, index=0, offset=0, direction=FORWARDS):
        self.track_id = track_id # The id of the track that we're on
        self.index = index # Where along the track it is
        self.offset = offset # How much past the index we are
        self.direction = direction
        # are we currently going forwards or backwards?
        self.velocity = 0
        self.blinker = NO_BLINK

    def set_blinker(self, new_blink):
        self.blinker = new_blink

    def _distance_to_next_point(self):
        dist_between_points = MAP_DATA[self.track_id]['distances'][self.index]
        return dist_between_points - self.offset

    def _at_end(self):
        return self.offset == len(MAP_DATA[self.track_id]['coordinates']) - 1

    def _at_junction(self):
        return (self.direction == FORWARDS and self._at_end()) or \
               (self.direction == BACKWARDS and self.offset == 0) or \
               ((self.offset, self.direction) in
                MAP_DATA[self.track_id]['middlejoins'])

    def _at_deadend(self):
        return (self.direction == FORWARDS and self._at_end() and
                not MAP_DATA[self.track_id]['endjoin']) or \
               (self.direction == BACKWARDS and self.offset == 0 and
                not MAP_DATA[self.track_id]['startjoin'])

    def _get_second_point(self,entry):
        id, index, dir = entry
        if dir == BACKWARDS:
            return MAP_DATA[id]['coordinates'][index-1]
        else:
            return MAP_DATA[id]['coordinates'][index+1]

    def _switch_rail(self):
        # If not at a junction, this function does nothing.
        if (self.direction == FORWARDS and self._at_end()) \
                or (self.direction == BACKWARDS and self.offset == 0):
            if self.direction == FORWARDS:
                source = 'endjoin'
            else:
                source = 'startjoin'

            if len(MAP_DATA[self.track_id][source]) == 1:
                self.track_id, self.offset, self.direction = \
                    MAP_DATA[self.track_id][source]

            elif len(MAP_DATA[self.track_id][source]) == 2:
                point0 = self._get_second_point(
                    MAP_DATA[self.track_id][source][0])
                point1 = self._get_second_point(
                    MAP_DATA[self.track_id][source][1])
                vertex = MAP_DATA[self.track_id]['coordinates'][self.index]
                point1dir = which_side(point0,vertex, point1)
                if point1dir == self.blinker:
                    self.track_id, self.offset, self.direction = MAP_DATA[self.track_id][source][1]
                else:
                    self.track_id, self.offset, self.direction = MAP_DATA[self.track_id][source][0]

        elif ((self.offset, self.direction) in
                MAP_DATA[self.track_id]['middlejoins']):
            if self.direction == FORWARDS:
                next_pt = MAP_DATA[self.track_id]['coordinates'][self.index + 1]
            else:
                next_pt = MAP_DATA[self.track_id]['coordinates'][self.index - 1]
            vertex = MAP_DATA[self.track_id]['coordinates'][self.index]
            other = self._get_second_point(
                MAP_DATA[self.track_id]['middlejoins'][
                    (self.offset, self.direction)])
            offshoot_dir = point1dir = which_side(next_pt,vertex, other)
            if offshoot_dir == self.blinker:
                self.track_id, self.offset, self.direction = \
                    MAP_DATA[self.track_id]['middlejoins'][(self.offset, self.direction)]
            # otherwise we don't change track.

    def move(self, amount):
        # Move by amount. return False if at dead end, otherwise true.
        while amount:
            if self.direction == FORWARDS:
                if self._distance_to_next_point() >= amount:
                    self.index += 1
                    self.offset = 0
                    if self._at_deadend():
                        return False
                    self._switch_rail()

    def debugpos(self):
        print(f'{self.index}, {self.track_id}, {self.offset}, [{MAP_DATA[self.track_id]["coordinates"]}]')

a = Train(441256441)
for i in range(10):
    a.move(1)
    a.debugpos()
print("done")