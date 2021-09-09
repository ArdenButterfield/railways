import pickle
import pygame
from pygame import gfxdraw
import sys

FORWARDS = True
BACKWARDS = False
LEFT_BLINK = -1
NO_BLINK = 0
RIGHT_BLINK = 1

with open("data/RedmondOR.pickle", 'rb') as f:
    MAP_DATA, ZONE_DIR = pickle.load(f)

def get_zone(coord):
    return (int(coord[0] // 1000), int(coord[1] // 1000))

def which_side(a,vert,b):
    # Which side is vector from vert to b, relative to vector from vert to a?
    # Uses the dot product, as described here:
    # https://stackoverflow.com/questions/13221873/
    rot_b = (vert[1] - b[1], b[0] - vert[0])
    # Rotated 90 deg counter clockwise, centered at 0
    a = (a[0] - vert[0], a[1] - vert[1]) # centered at 0
    dot_prod = a[0] * rot_b[0] + a[1] * rot_b[1]
    return LEFT_BLINK if dot_prod < 0 else RIGHT_BLINK

def thick_line(start, end):
    # returns a polygon that is effectively a thick line from the start to end
    # points
    radius = 2
    vector = ((end[0] - start[0]), (end[1] - start[1]))
    magnitude = (vector[1] ** 2 + vector[0] ** 2)**0.5
    radx, rady = (radius * vector[0] / magnitude, radius * vector[1] / magnitude)
    return [(start[0] - rady, start[1] + radx), (end[0] - rady, end[1] + radx),
            (end[0] + rady, end[1] - radx), (start[0] + rady, start[1] - radx)]


class Board():
    def __init__(self, train, size, screen, scale=1):
        self.train = train
        self.train_pos = train.current_position()
        self.size = self.width, self.height = size
        self.center = self.width / 2, self.height / 2
        self.screen = screen
        self.scale = scale # coord distance * scale = pixel distance
        self.zone_size = 1000 * scale # How many pixels across is a zone?

        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale
        self.active_zones = []
        self.set_active_zones()
        # print(self.active_zones)

    def set_active_zones(self):

        centerx, centery = self.train.current_position()
        # print(f"trainpos: {centerx} {centery}")
        minx, miny = get_zone((centerx - self.coordwidth,
                              centery - self.coordheight))
        maxx, maxy = get_zone((centerx + self.coordwidth,
                              centery + self.coordheight))
        # print(minx, miny, maxx, maxy)
        for i in range(minx, maxx + 1):
            for j in range(miny, maxy + 1):
                self.active_zones.append((i,j))

    def set_active_tracks(self):
        self.active_tracks = set()
        for zone in self.active_zones:
            if zone in ZONE_DIR:
                for id in ZONE_DIR[zone]:
                    self.active_tracks.add(id)

    def _coord_to_pos(self, coord):
        # Get the screen position of a coordinate
        cx, cy = coord
        offset_x, offset_y = cx - self.train_pos[0], cy - self.train_pos[1]
        offset_x *= self.scale
        offset_y *= self.scale
        return self.center[0] + offset_x, self.center[1] - offset_y

    def update_train_pos(self, pos):
        self.train_pos = pos

    def draw_lines(self):
        self.set_active_zones()
        self.set_active_tracks()
        bounding_boxes = []
        if self.train.direction == FORWARDS:
            prev = MAP_DATA[self.train.track_id]["coordinates"][self.train.index]
            next = MAP_DATA[self.train.track_id]["coordinates"][self.train.index + 1]
        else:
            next = MAP_DATA[self.train.track_id]["coordinates"][self.train.index]
            prev = MAP_DATA[self.train.track_id]["coordinates"][self.train.index + 1]
        # TODO: this might break when at the end of the track?
        vector = ((next[0] - prev[0]), (next[1] - prev[1]))
        magnitude = (vector[1] ** 2 + vector[0] ** 2) ** 0.5
        unit_vector = (vector[0] / magnitude, vector[1] / magnitude)

        for track in self.active_tracks:
            lines = [self._coord_to_pos(c) for c in MAP_DATA[track]["coordinates"]]
            for coord in range(len(lines) - 1):
                pattern = thick_line(lines[coord],lines[coord + 1])
                # pygame.draw.aalines(self.screen, thick_line(lines[coord],lines[coord + 1]), (255, 255, 255))
                bounding_boxes.append(pygame.draw.aaline(self.screen, (255, 255, 255), pattern[0], pattern[1]))
                bounding_boxes.append(pygame.draw.aaline(self.screen, (255, 255, 255), pattern[2], pattern[3]))
        pygame.draw.circle(self.screen,(255,255,0),self.center, 4)
        pygame.display.update(bounding_boxes)


class Train():
    def __init__(self, track_id, index=0, offset=0, direction=FORWARDS):
        self.board = None
        self.track_id = track_id # The id of the track that we're on
        self.index = index # Where along the track it is
        self.offset = offset # How much past the index we are
        self.direction = direction
        # are we currently going forwards or backwards?
        self.velocity = 0
        self.blinker = NO_BLINK

    def attatch_board(self, board):
        self.board = board

    def set_blinker(self, new_blink):
        self.blinker = new_blink

    def _distance_to_next_point(self):
        dist_between_points = MAP_DATA[self.track_id]['distances'][self.index]
        return dist_between_points - self.offset

    def _at_end(self):
        return self.index == len(MAP_DATA[self.track_id]['coordinates']) - 1

    def _at_start(self):
        return self.index == 0 and self.offset == 0

    def _at_junction(self):
        return (self.direction == FORWARDS and self._at_end()) or \
               (self.direction == BACKWARDS and self.offset == 0) or \
               ((self.offset, self.direction) in
                MAP_DATA[self.track_id]['middlejoins'])

    def _at_deadend(self):
        return (self.direction == FORWARDS and self._at_end() and
                not MAP_DATA[self.track_id]['endjoin']) or \
               (self.direction == BACKWARDS and self._at_start() and
                not MAP_DATA[self.track_id]['startjoin'])

    def _get_second_point(self,entry):
        id, index, dir = entry
        if dir == BACKWARDS:
            return MAP_DATA[id]['coordinates'][index-1]
        else:
            return MAP_DATA[id]['coordinates'][index+1]

    def _switch_rail(self):
        # If not at a junction, this function does nothing, and returns False.
        # If we actually switch rails, the function returns True.
        switched = False
        if (self.direction == FORWARDS and self._at_end()) \
                or (self.direction == BACKWARDS and self._at_start()):
            switched = True
            if self.direction == FORWARDS:
                source = 'endjoin'
            else:
                source = 'startjoin'

            if len(MAP_DATA[self.track_id][source]) == 1:
                self.track_id, self.index, self.direction = \
                    MAP_DATA[self.track_id][source][0]
            elif len(MAP_DATA[self.track_id][source]) == 2:
                point0 = self._get_second_point(
                    MAP_DATA[self.track_id][source][0])
                point1 = self._get_second_point(
                    MAP_DATA[self.track_id][source][1])
                vertex = MAP_DATA[self.track_id]['coordinates'][self.index]
                point1dir = which_side(point0,vertex, point1)
                if point1dir == self.blinker:
                    self.track_id, self.index, self.direction = MAP_DATA[self.track_id][source][1]
                else:
                    self.track_id, self.index, self.direction = MAP_DATA[self.track_id][source][0]

        elif ((self.index, self.direction) in
                MAP_DATA[self.track_id]['middlejoins']):
            if self.direction == FORWARDS:
                next_pt = MAP_DATA[self.track_id]['coordinates'][self.index + 1]
            else:
                next_pt = MAP_DATA[self.track_id]['coordinates'][self.index - 1]
            vertex = MAP_DATA[self.track_id]['coordinates'][self.index]
            other = self._get_second_point(
                MAP_DATA[self.track_id]['middlejoins'][
                    (self.index, self.direction)])
            offshoot_dir = point1dir = which_side(next_pt,vertex, other)
            if offshoot_dir == self.blinker:
                self.track_id, self.index, self.direction = \
                    MAP_DATA[self.track_id]['middlejoins'][(self.index, self.direction)]
                switched = True
            # otherwise we don't change track.
        return switched

    def move(self, amount):
        # Move by amount. return False if at dead end, otherwise true.
        # TODO: moving backwards doesnt work
        while amount:
            # print(amount)
            if self.direction == FORWARDS:
                if self._at_deadend():
                    return False
                if self._switch_rail():
                    continue
                segment = self._distance_to_next_point()
                if segment > amount:
                    self.offset += amount
                    amount = 0
                else:
                    self.index += 1
                    self.offset = 0
                    amount -= segment

            else:
                if self.offset:
                    if self.offset > amount:
                        self.offset -= amount
                        amount = 0
                    else:
                        amount -= self.offset
                        self.offset = 0
                else:
                    if self._at_deadend():
                        return False
                    if self._switch_rail():
                        continue
                    distance_to_prev = MAP_DATA[self.track_id]['distances'][self.index - 1]
                    self.index -= 1
                    if distance_to_prev > amount:
                        self.offset = distance_to_prev - amount
                        amount = 0
                    else:
                        amount -= distance_to_prev
        self.board.update_train_pos(self.current_position())
        return True

    def current_position(self):
        if self.offset == 0:
            return MAP_DATA[self.track_id]['coordinates'][self.index]
        x1, y1 = MAP_DATA[self.track_id]['coordinates'][self.index]
        x2, y2 = MAP_DATA[self.track_id]['coordinates'][self.index + 1]
        a = self.offset /  MAP_DATA[self.track_id]['distances'][self.index]
        return (x1 + a * (x2 - x1), y1 + a * (y2 - y1))

    def debugpos(self):
        print(f'{self.index}, {self.track_id}, {self.offset}, [{MAP_DATA[self.track_id]["coordinates"][self.index]}]')


"""print('set up')
for i in range(100):
    print('moving')
    if not a.move(10):
        print("end of line")
        break
    a.debugpos()
print("done")"""

pygame.init()
size = width, height = 500, 300
screen = pygame.display.set_mode(size)

"""while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()"""

train = Train(429099625, direction=FORWARDS, index=8, offset=10)
train.set_blinker(LEFT_BLINK)
board = Board(train, size, screen, scale=1)
train.attatch_board(board)
while True:
    screen.fill((100,0,0))
    board.draw_lines()


    pygame.time.wait(100)
    if not train.move(5):
        print("dead end")
        break
    print(train.track_id, train.index, train.offset)