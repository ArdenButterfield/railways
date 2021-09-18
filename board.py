# TODO:
# Make the music volume do the thing
# Make the buttons for jumping to specific towns
# Make the buttons on the menu screen light up when you hit them
# Make a credits screen
# Tidy up the code, maybe break up the board class?
# Finish the music
# Write a README
# Keep turn when spacebar start
# swap turn buttons when train going down
# And that's about it.

import pygame
import sys
from utils import *
from pygame.locals import RESIZABLE
from music import Music


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
        self.music = Music()

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

        pygame.font.init()
        self.text_font = pygame.font.Font('fonts/oswald.light.ttf',20)
        self.keyname_font = pygame.font.Font('fonts/OstrichSans-Black.otf',25)
        self.menu_title_font = pygame.font.Font('fonts/OstrichSans-Bold.otf',60)
        self.logo_font = pygame.font.Font('fonts/OstrichSans-Bold.otf',200)
        self.town_font = pygame.font.Font('fonts/OstrichSans-Black.otf', 40)
        self.menu_init()

    def menu_init(self):
        self.div_line = (self.width * 4) // 7
        self.right_panel = pygame.Rect((self.div_line, 0),
                                  (self.width - self.div_line, self.height))
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
            x = self.div_line + side_button_margin
            y = i * (side_buttons_size[
                         1] + 2 * side_button_margin) + side_button_margin
            start = x, y
            button_rect = pygame.Rect(start, side_buttons_size)
            side_buttons[i].append(button_rect)

            text = self.keyname_font.render(side_buttons[i][1], True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = button_rect.center
            side_buttons[i].append(text)
            side_buttons[i].append(text_rect)
            # side_buttons[i].append(start)

            description = self.text_font.render(side_buttons[i][2], True,
                                                (0, 0, 0))
            description_rect = description.get_rect()
            x = start[0] + side_buttons_size[0] + 10
            description_rect.left = x
            description_rect.centery = text_rect.centery
            if side_buttons[i][1] == "LEFT":
                description_rect.y += (side_buttons_size[
                                           1] + side_button_margin) // 2
            side_buttons[i].append(description)
            side_buttons[i].append(description_rect)
        self.side_buttons = side_buttons

        self.top_box = pygame.Rect((0, 0), (self.div_line, 80))
        self.title_text = self.menu_title_font.render("Pacific Railroad", True,
                                                 (255, 255, 255))
        self.title_text_box = self.title_text.get_rect()
        self.title_text_box.center = self.top_box.center

    def change_scale_level(self):
        self.scale = 1 if self.scale == 0.1 else 0.1
        self.zone_size = 1000 * self.scale
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale

    def set_active_zones(self):
        self.active_zones = []
        centerx, centery = self.train_pos
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
            img = self.town_font.render(ZONE_NAMES[curr_zone], True, (255, 255, 255))
            box = img.get_rect()
            box.bottomright = pygame.Vector2(self.width - 20, self.height - 20)
            self.screen.blit(img, box)

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
        self.town_name()
        # pygame.display.update(bounding_boxes)
        pygame.display.flip()
        self.clock.tick(30)

    def resize(self, w, h):
        self.size = self.width, self.height = w, h
        self.center = pygame.Vector2(self.width / 2, self.height / 2)
        self.beam_len = self.center.magnitude()
        self.beam_rad = self.beam_len * 0.6
        self.screen = pygame.display.set_mode(self.size)
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale
        self.menu_init()

    def menu(self):
        leave_reason = None

        while not leave_reason:
            self.screen.fill((100,0,0))
            pygame.draw.rect(self.screen, (180,180,180), self.right_panel, 0)
            for i in range(len(self.side_buttons)):
                pygame.draw.rect(self.screen, (250,250,250),
                                 self.side_buttons[i][3], 0, 3)
                # key text:
                self.screen.blit(self.side_buttons[i][4],self.side_buttons[i][5])
                # description text:
                self.screen.blit(self.side_buttons[i][6], self.side_buttons[i][7])
            pygame.draw.rect(self.screen, (0, 0, 0), self.top_box)
            self.screen.blit(self.title_text, self.title_text_box)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        leave_reason = "return"
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)
                    leave_reason = "resize"
        return leave_reason

    def logo(self):
        track_1 = (0,self.height / 2 - 2), (self.width, self.height / 2 - 2)
        track_2 = (0, self.height / 2 + 2), (self.width, self.height / 2 + 2)

        horiz_start = -self.width * 0.5
        vert = (self.width - horiz_start) * 3 // 5
        mid = self.height//2
        headlight_shape = [pygame.Vector2(horiz_start, mid),
                           pygame.Vector2(self.width, mid - vert),
                           pygame.Vector2(self.width, mid + vert)]
        shift = pygame.Vector2(25,0)
        fade = [80, 50, 0]

        top_text = self.logo_font.render("Pacific", True, (80, 50, 0))
        bottom_text = self.logo_font.render("Railroad", True, (80, 50, 0))
        top_rect = top_text.get_rect()
        top_rect.bottomright = (self.width - 20, self.height // 2 - 20)
        bottom_rect = bottom_text.get_rect()
        bottom_rect.topright = (self.width - 20, self.height // 2 + 20)

        while headlight_shape[0][0] < self.width + 700:
            self.screen.fill((100,0,0))

            for i in range(len(headlight_shape)):
                headlight_shape[i] += shift
            if headlight_shape[0][0] > self.width - 300:
                fade = [min(255,i + 5) for i in fade]
                top_text = self.logo_font.render("Pacific", True, fade)
                bottom_text = self.logo_font.render("Railroad", True, fade)
            self.screen.blit(top_text, top_rect)
            self.screen.blit(bottom_text, bottom_rect)
            pygame.draw.polygon(
                self.screen, (80, 50, 0), headlight_shape, width=0)
            pygame.draw.line(
                self.screen, (255, 255, 255), track_1[0], track_1[1])
            pygame.draw.line(
                self.screen, (255, 255, 255), track_2[0], track_2[1])
            pygame.draw.circle(
                self.screen, (255, 255, 0), headlight_shape[0], 4)
            pygame.display.flip()
            self.clock.tick(30)