# TODO: make headlight movement smoother- that is, taking several frames to

# Also, change the annoying coordinate stuff to pygame 2dvector.
# (did some, could stand to use lerp() for offset stuff.

# Then, implement zooming in and out?

# Make a menu screen?

# Soundtrack??? (do it in a day or something idk. Keep it simple, unobtrusive)

# Do the things with the radio voices?

import pygame
from pygame import gfxdraw
import sys
from utils import *
from train import Train

clock = pygame.time.Clock()





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
        self.center = pygame.Vector2(self.width / 2, self.height / 2)
        self.beam_len = self.center.magnitude()
        self.beam_rad = self.beam_len * 0.6
        self.screen = screen
        self.scale = scale # coord distance * scale = pixel distance
        self.zone_size = 1000 * scale # How many pixels across is a zone?
        self.headlight_direction = None
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale
        self.active_zones = []
        self.set_active_zones()
        self.prev_headlight_bounding_box = None
        self.base_indicator = (pygame.Vector2(15,10),pygame.Vector2(25,0),pygame.Vector2(15,-10))

        # print(self.active_zones)

    def set_active_zones(self):

        centerx, centery = self.train.current_position()
        # print(f"trainpos: {centerx} {centery}")
        minx, miny = get_zone((centerx - (self.coordwidth // 2),
                              centery - (self.coordheight // 2)))
        maxx, maxy = get_zone((centerx + (self.coordwidth//2),
                              centery + (self.coordheight//2)))
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
        screen.fill((100, 0, 0))
        self.set_active_zones()
        self.set_active_tracks()
        bounding_boxes = []
        if self.train._at_end():
            prev = pygame.Vector2(
                MAP_DATA[self.train.track_id]["coordinates"][self.train.index - 1])
            next = pygame.Vector2(
                MAP_DATA[self.train.track_id]["coordinates"][self.train.index])
        else:
            prev = pygame.Vector2(
                MAP_DATA[self.train.track_id]["coordinates"][self.train.index])
            next = pygame.Vector2(
                MAP_DATA[self.train.track_id]["coordinates"][self.train.index + 1])
        if self.train.direction == BACKWARDS:
            temp = prev
            prev = next
            next = temp
        vector = next - prev
        vector[0] = -vector[0]
        if self.headlight_direction is None:
            self.headlight_direction = vector.normalize()
        else:
            angle = self.headlight_direction.angle_to(vector)
            headlight_rotation = self.train.speed / 5
            self.headlight_direction = self.headlight_direction.rotate(min(headlight_rotation, max(angle,-headlight_rotation)))

        headlight = [self.center,
                     self.center - self.beam_len * self.headlight_direction + self.beam_rad * self.headlight_direction.rotate(-90),
                     self.center - self.beam_len * self.headlight_direction - self.beam_rad * self.headlight_direction.rotate(-90)]
        headlight_bounding_box = pygame.draw.polygon(self.screen,(80,50,0),headlight,width=0)

        if self.train.blinker != NO_BLINK:
            if self.train.blinker == LEFT_BLINK:
                indicator_angle = pygame.Vector2(0,-1).angle_to(self.headlight_direction)
            else:
                indicator_angle = pygame.Vector2(0, 1).angle_to(self.headlight_direction)
            indicator = [self.center + i.rotate(indicator_angle) for i in self.base_indicator]
            indicator_bounding_box = pygame.draw.polygon(self.screen,(255,255,0),indicator,width=0)
            bounding_boxes.append(indicator_bounding_box)

        bounding_boxes.append(headlight_bounding_box)
        bounding_boxes.append(self.prev_headlight_bounding_box)
        self.prev_headlight_bounding_box = headlight_bounding_box
        for track in self.active_tracks:
            lines = [self._coord_to_pos(c) for c in MAP_DATA[track]["coordinates"]]
            for coord in range(len(lines) - 1):
                pattern = thick_line(lines[coord],lines[coord + 1])
                # pygame.draw.aalines(self.screen, thick_line(lines[coord],lines[coord + 1]), (255, 255, 255))
                bounding_boxes.append(pygame.draw.aaline(self.screen, (255, 255, 255), pattern[0], pattern[1]))
                bounding_boxes.append(pygame.draw.aaline(self.screen, (255, 255, 255), pattern[2], pattern[3]))
        pygame.draw.circle(self.screen,(255,255,0),self.center, 4)
        pygame.display.update(bounding_boxes)

    def take_input(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.train.set_blinker(LEFT_BLINK)
                elif event.key == pygame.K_RIGHT:
                    self.train.set_blinker(RIGHT_BLINK)
                elif event.key == pygame.K_UP:
                    self.train.speed_up()
                elif event.key == pygame.K_DOWN:
                    self.train.slow_down()
                elif event.key == pygame.K_SPACE:
                    self.headlight_direction = None
                    self.train.stop()
            elif event.type == pygame.QUIT:
                sys.exit()

    def play(self):
        while True:
            self.take_input()
            if not self.train.step():
                self.headlight_direction = None
            self.draw_lines()
            clock.tick(30)


"""print('set up')
for i in range(100):
    print('moving')
    if not a.move(10):
        print("end of line")
        break
    a.debugpos()
print("done")"""

pygame.init()
size = width, height = 1000, 500
screen = pygame.display.set_mode(size)

"""while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()"""

train = Train(429099625, direction=FORWARDS, index=8, offset=10)
board = Board(train, size, screen, scale=1)
train.attatch_board(board)
board.play()
"""while True:
    screen.fill((100,0,0))
    board.draw_lines()


    pygame.time.wait(100)
    if not train.move(5):
        print("dead end")
        break
    print(train.track_id, train.index, train.offset)"""