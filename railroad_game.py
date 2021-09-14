# TODO: make headlight movement smoother- that is, taking several frames to

# Also, change the annoying coordinate stuff to pygame 2dvector.
# (did some, could stand to use lerp() for offset stuff.

# Then, implement zooming in and out?

# Make a menu screen?

# Soundtrack??? (do it in a day or something idk. Keep it simple, unobtrusive)

# Do the things with the radio voices?

import pygame
import sys
from utils import *
from pygame.locals import RESIZABLE


def thick_line(start, end):
    # returns a polygon that is effectively a thick line from the start to end
    # points
    radius = 2
    vector = ((end[0] - start[0]), (end[1] - start[1]))
    magnitude = (vector[1] ** 2 + vector[0] ** 2)**0.5
    radx, rady = radius * vector[0] / magnitude, radius * vector[1] / magnitude
    return [(start[0] - rady, start[1] + radx), (end[0] - rady, end[1] + radx),
            (end[0] + rady, end[1] - radx), (start[0] + rady, start[1] - radx)]

class Board:
    def __init__(self, train, size):
        pygame.init()

        self.train = train
        self.train_pos = train.current_position()
        self.size = self.width, self.height = size
        self.center = pygame.Vector2(self.width / 2, self.height / 2)
        self.beam_len = self.center.magnitude()
        self.beam_rad = self.beam_len * 0.6
        self.screen = pygame.display.set_mode(size, RESIZABLE)
        self.scale = 1  # coord distance * scale = pixel distance
        self.zone_size = 1000 * self.scale  # How many pixels across is a zone?
        self.headlight_direction = None
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale
        self.active_zones = []
        self.active_tracks = None
        self.set_active_zones()
        self.set_active_tracks()
        self.prev_headlight_bounding_box = None
        self.base_indicator = (pygame.Vector2(15, 10),
                               pygame.Vector2(25, 0),
                               pygame.Vector2(15, -10))
        # draws a triange, for "blinker". It can be rotated around

        self.clock = pygame.time.Clock()
        self.on_menu = True

        pygame.font.init()
        self.text_font = pygame.font.Font('fonts/oswald.light.ttf',20)
        self.keyname_font = pygame.font.Font('fonts/OstrichSans-Black.otf',25)
        self.menu_title_font = pygame.font.Font('fonts/OstrichSans-Bold.otf',60)

    def change_scale_level(self):
        self.scale = 1 if self.scale == 0.1 else 0.1
        self.zone_size = 1000 * self.scale
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale

    def set_active_zones(self):
        self.active_zones = []
        centerx, centery = self.train.current_position()
        minx, miny = get_zone((centerx - (self.coordwidth // 2),
                              centery - (self.coordheight // 2)))
        maxx, maxy = get_zone((centerx + (self.coordwidth//2),
                              centery + (self.coordheight//2)))
        for i in range(minx, maxx + 1):
            for j in range(miny, maxy + 1):
                self.active_zones.append((i, j))

    def set_active_tracks(self):
        self.active_tracks = set()
        for zone in self.active_zones:
            if zone in ZONE_DIR:
                for track_id in ZONE_DIR[zone]:
                    self.active_tracks.add(track_id)

    def _coord_to_pos(self, coord):
        # Get the screen position of a coordinate
        cx, cy = coord
        offset_x, offset_y = cx - self.train_pos[0], cy - self.train_pos[1]
        offset_x *= self.scale
        offset_y *= self.scale
        return self.center[0] + offset_x, self.center[1] - offset_y

    def update_train_pos(self, pos):
        # Gets called by train object when the train moves.
        self.train_pos = pos

    def set_headlight_direction(self):
        vector = self.train.train_vector()
        if self.headlight_direction is None:
            self.headlight_direction = vector.normalize()
        else:
            angle = self.headlight_direction.angle_to(vector)
            if angle < -180:
                angle += 360
            elif angle > 180:
                angle -= 360
            rot = 0.2 * angle
            self.headlight_direction = self.headlight_direction.rotate(rot)

    def indicator_polygon(self):
        if self.train.blinker == LEFT_BLINK:
            indicator_angle = pygame.Vector2(0, -1).angle_to(
                self.headlight_direction)
        else:
            indicator_angle = pygame.Vector2(0, 1).angle_to(
                self.headlight_direction)
        return [self.center + i.rotate(indicator_angle)
                for i in self.base_indicator]

    def headlight_polygon(self):
        out_vect = self.center - self.beam_len * self.headlight_direction
        side_vect = self.beam_rad * self.headlight_direction.rotate(-90)
        headlight = [self.center, out_vect + side_vect, out_vect - side_vect]
        return headlight

    def town_name(self):
        curr_zone = get_zone(self.train_pos)
        if curr_zone in ZONE_NAMES:
            img = self.keyname_font.render(ZONE_NAMES[curr_zone], True, (255, 255, 255))
            self.screen.blit(img, (20, 20))

    def draw_lines(self):
        self.screen.fill((100, 0, 0))
        self.set_active_zones()
        self.set_active_tracks()
        self.set_headlight_direction()
        bounding_boxes = []

        headlight_bounding_box = pygame.draw.polygon(
            self.screen, (80, 50, 0), self.headlight_polygon(), width=0)

        if self.train.blinker != NO_BLINK:
            indicator_bounding_box = pygame.draw.polygon(
                self.screen, (255, 255, 0), self.indicator_polygon(), width=0)
            bounding_boxes.append(indicator_bounding_box)

        bounding_boxes.append(headlight_bounding_box)
        bounding_boxes.append(self.prev_headlight_bounding_box)
        self.prev_headlight_bounding_box = headlight_bounding_box
        for track in self.active_tracks:
            coords = MAP_DATA[track]["coordinates"]
            lines = [self._coord_to_pos(c) for c in coords]
            for coord in range(len(lines) - 1):
                pattern = thick_line(lines[coord], lines[coord + 1])
                bbox1 = pygame.draw.aaline(
                    self.screen, (255, 255, 255), pattern[0], pattern[1])
                bbox2 = pygame.draw.aaline(
                    self.screen, (255, 255, 255), pattern[2], pattern[3])
                bounding_boxes.append(bbox1)
                bounding_boxes.append(bbox2)
        pygame.draw.circle(self.screen, (255, 255, 0), self.center, 4)
        pygame.display.update(bounding_boxes)

    def resize(self, w, h):
        self.size = self.width, self.height = w, h
        self.center = pygame.Vector2(self.width / 2, self.height / 2)
        self.beam_len = self.center.magnitude()
        self.beam_rad = self.beam_len * 0.6
        self.screen = pygame.display.set_mode(self.size)
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale

    def take_input(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.on_menu = not self.on_menu
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
                elif event.key == pygame.K_z:
                    self.change_scale_level()
            elif event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.resize(event.w, event.h)

    def play(self):
        while True:
            self.take_input()
            if self.on_menu:
                while True:
                    leave_reason = self.menu()
                    if leave_reason != "resize":
                        break
            else:
                if not self.train.step():
                    self.headlight_direction = None
                self.draw_lines()
            self.clock.tick(30)
            print(self.train_pos[0],self.train_pos[1])

    def menu(self):
        leave_reason = None
        div_line = (self.width * 4) // 7
        right_panel = pygame.Rect((div_line, 0),
                                  (self.width - div_line, self.height))
        side_buttons_size = (110, 30)
        side_buttons = [[pygame.K_UP, "UP", "Speed up"],
                        [pygame.K_DOWN, "DOWN", "Slow down"],
                        [pygame.K_LEFT, "LEFT", "Set turn signal"],
                        [pygame.K_RIGHT, "RIGHT", ""],
                        [pygame.K_SPACE, "SPACE", "Stop/start, turn around"],
                        [pygame.K_z, "Z", "Change zoom level"],
                        [pygame.K_RETURN, "RETURN", "Toggle menu screen"]]
        side_button_margin = 10
        for i in range(len(side_buttons)):
            x = div_line + side_button_margin
            y = i * (side_buttons_size[1] + 2 * side_button_margin) + side_button_margin
            start = x, y
            button_rect = pygame.Rect(start,side_buttons_size)
            side_buttons[i].append(button_rect)

            text = self.keyname_font.render(side_buttons[i][1], True, (0,0,0))
            text_rect = text.get_rect()
            text_rect.center = button_rect.center
            side_buttons[i].append(text)
            side_buttons[i].append(text_rect)
            # side_buttons[i].append(start)

            description = self.text_font.render(side_buttons[i][2], True,(0,0,0))
            description_rect = description.get_rect()
            x = start[0] + side_buttons_size[0] + 10
            description_rect.left = x
            description_rect.centery = text_rect.centery
            if side_buttons[i][1] == "LEFT":
                description_rect.y += (side_buttons_size[1] + side_button_margin) // 2
            side_buttons[i].append(description)
            side_buttons[i].append(description_rect)

        top_box = pygame.Rect((0,0),(div_line, 80))
        title_text = self.menu_title_font.render("Pacific Railroad",True,(255,255,255))
        title_text_box = title_text.get_rect()
        title_text_box.center = top_box.center

        while not leave_reason:
            self.screen.fill((100,0,0))
            pygame.draw.rect(self.screen, (180,180,180), right_panel, 0)
            for i in range(len(side_buttons)):
                pygame.draw.rect(self.screen, (250,250,250),
                                 side_buttons[i][3], 0, 3)
                # key text:
                self.screen.blit(side_buttons[i][4],side_buttons[i][5])
                # description text:
                self.screen.blit(side_buttons[i][6], side_buttons[i][7])
            pygame.draw.rect(self.screen, (0, 0, 0), top_box)
            self.screen.blit(title_text, title_text_box)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.on_menu = False
                        leave_reason = "return"
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)
                    leave_reason = "resize"
        return leave_reason

    def logo(self):
        self.train.track_id = 238911528
        self.train.index = 10
        self.train.direction = BACKWARDS
        self.train.offset = 0
        self.train.speed = 4
        logo_center = pygame.Vector2(-13705413.483923743,5475149.370307351)
        for i in range(100):
            self.train.step()
            self.screen.fill((100, 0, 0))
            self.set_active_zones()
            self.set_active_tracks()
            self.set_headlight_direction()
            bounding_boxes = []
            offset = pygame.Vector2(self.train_pos) - logo_center
            headlight = [i - offset for i in self.headlight_polygon()]
            headlight_bounding_box = pygame.draw.polygon(
                self.screen, (80, 50, 0), headlight, width=0)

            bounding_boxes.append(headlight_bounding_box)
            bounding_boxes.append(self.prev_headlight_bounding_box)
            self.prev_headlight_bounding_box = headlight_bounding_box
            for track in self.active_tracks:
                coords = MAP_DATA[track]["coordinates"]
                lines = [pygame.Vector2(self._coord_to_pos(c)) - offset for c in coords]
                for coord in range(len(lines) - 1):
                    pattern = thick_line(lines[coord], lines[coord + 1])
                    bbox1 = pygame.draw.aaline(
                        self.screen, (255, 255, 255), pattern[0], pattern[1])
                    bbox2 = pygame.draw.aaline(
                        self.screen, (255, 255, 255), pattern[2], pattern[3])
                    bounding_boxes.append(bbox1)
                    bounding_boxes.append(bbox2)
            pygame.draw.circle(self.screen, (255, 255, 0), self.center - offset, 4)
            pygame.display.update(bounding_boxes)
            self.clock.tick(30)