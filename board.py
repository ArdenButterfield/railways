# TODO:
# Make the buttons on the menu screen light up when you hit them
# Tidy up the code, maybe break up the board class?
# Finish the music
# Write a READMErm
# And that's about it.

import pygame
import sys
from utils import *
from pygame.locals import RESIZABLE
from music import Music
from menu_buttons import yard_buttons, side_buttons

BUTTON_COLOR = (250, 250, 250)
BUTTON_HOVER_COLOR = (150, 150, 150)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_COLOR = (100, 0, 0)
HEADLIGHT_COLOR = (80, 50, 0)
TRAIN_COLOR = (250, 250, 0)
SIDE_PANEL_COLOR = (180, 180, 180)

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
    """
    Responsible for drawing to the screen.
    """
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

    def side_buttons_init(self):
        side_buttons_size = (110, 30)

        side_button_margin = 10
        for i in range(len(side_buttons)):
            side_buttons[i] = side_buttons[i][:3]
            x = self.div_line + side_button_margin
            y = i * (side_buttons_size[
                         1] + 2 * side_button_margin) + side_button_margin
            start = x, y
            button_rect = pygame.Rect(start, side_buttons_size)
            side_buttons[i].append(button_rect)

            text = self.keyname_font.render(side_buttons[i][1], True, BLACK)
            text_rect = text.get_rect()
            text_rect.center = button_rect.center
            side_buttons[i].append(text)
            side_buttons[i].append(text_rect)
            # side_buttons[i].append(start)

            description = self.text_font.render(side_buttons[i][2], True,
                                                BLACK)
            description_rect = description.get_rect()
            x = start[0] + side_buttons_size[0] + 10
            description_rect.left = x
            description_rect.centery = text_rect.centery
            if side_buttons[i][1] == "LEFT":
                description_rect.y += (side_buttons_size[
                                           1] + side_button_margin) // 2
            side_buttons[i].append(description)
            side_buttons[i].append(description_rect)

    def yard_buttons_init(self):
        cols = 2
        rows = len(yard_buttons) // 2 # Assuming even number of yard buttons.
        button_space_w = self.left_panel.width // cols
        button_space_h = self.left_panel.height // rows
        button_margin = 15
        i = 0
        w = button_space_w - 2 * button_margin
        h = button_space_h - 2 * button_margin
        for row in range(rows):
            for col in range(cols):
                yard_buttons[i] = yard_buttons[i][:4]
                x = self.left_panel.left + col * button_space_w + button_margin
                y = self.left_panel.top + row * button_space_h + button_margin
                button_rect = pygame.Rect((x, y), (w, h))
                yard_buttons[i].append(button_rect)
                text = self.town_font.render(yard_buttons[i][0], True, BLACK)
                text_rect = text.get_rect()
                text_rect.center = button_rect.center
                yard_buttons[i].append(BUTTON_COLOR)
                yard_buttons[i].append(text)
                yard_buttons[i].append(text_rect)
                i += 1

    def menu_init(self):
        self.div_line = (self.width * 4) // 7
        self.right_panel = pygame.Rect((self.div_line, 0),
                                  (self.width - self.div_line, self.height))

        self.top_box = pygame.Rect((0, 0), (self.div_line, 80))
        self.left_panel = pygame.Rect((0,80),(self.div_line - 0,self.height - 80))
        self.title_text = self.menu_title_font.render("Pacific Railroad", True,
                                                 WHITE)
        self.title_text_box = self.title_text.get_rect()
        self.title_text_box.center = self.top_box.center

        self.credits_button = pygame.Rect((self.width - 100, self.height - 40),(90,30))
        self.credits_text = self.keyname_font.render("CREDITS", True, BLACK)
        self.credits_box = self.credits_text.get_rect()
        self.credits_box.center = self.credits_button.center
        self.credits_box_color = BUTTON_COLOR

        self.side_buttons_init()
        self.yard_buttons_init()
        self.credits_init()

    def credits_init(self):
        with open("credits.txt", "r") as f:
            credits_text = f.readlines()
        credits_text.append("Press any key to return to the menu.")
        self.credits_lines = []
        y = 30
        for line in credits_text:
            line = line.strip()
            t = self.text_font.render(line, True, BLACK)
            tbox = t.get_rect()
            tbox.topleft = (30,y)
            self.credits_lines.append([t,tbox])
            y += 30


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
            img = self.town_font.render(ZONE_NAMES[curr_zone], True, WHITE)
            box = img.get_rect()
            box.bottomright = pygame.Vector2(self.width - 20, self.height - 20)
            self.screen.blit(img, box)

    def draw_lines(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.set_active_zones()
        self.set_active_tracks()
        self.set_headlight_direction()
        bounding_boxes = []

        headlight_bounding_box = pygame.draw.polygon(
            self.screen, HEADLIGHT_COLOR, self.headlight_polygon(), width=0)

        if self.train.blinker != NO_BLINK:
            indicator_bounding_box = pygame.draw.polygon(
                self.screen, TRAIN_COLOR, self.indicator_polygon(), width=0)
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
                    self.screen, WHITE, pattern[0], pattern[1])
                bbox2 = pygame.draw.aaline(
                    self.screen, WHITE, pattern[2], pattern[3])
                bounding_boxes.append(bbox1)
                bounding_boxes.append(bbox2)
        pygame.draw.circle(self.screen, TRAIN_COLOR, self.center, 4)
        self.town_name()
        # pygame.display.update(bounding_boxes)
        pygame.display.flip()
        self.clock.tick(30)

    def resize(self, w, h):
        self.size = self.width, self.height = w, h
        self.center = pygame.Vector2(self.width / 2, self.height / 2)
        self.beam_len = self.center.magnitude()
        self.beam_rad = self.beam_len * 0.6
        self.screen = pygame.display.set_mode(self.size, RESIZABLE)
        self.coordwidth = self.width / self.scale
        self.coordheight = self.height / self.scale
        self.menu_init()

    def set_button_colors(self):
        mousepos = pygame.mouse.get_pos()
        hover = False
        for i in range(len(yard_buttons)):
            if yard_buttons[i][4].collidepoint(mousepos):
                yard_buttons[i][5] = BUTTON_HOVER_COLOR
                hover = True
            else:
                yard_buttons[i][5] = BUTTON_COLOR
        if self.credits_button.collidepoint(mousepos):
            self.credits_box_color = BUTTON_HOVER_COLOR
            hover = True
        else:
            self.credits_box_color = BUTTON_COLOR
        if hover:
            pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def yard_button_click(self):
        mousepos = pygame.mouse.get_pos()
        clicked = False
        for i in range(len(yard_buttons)):
            if yard_buttons[i][4].collidepoint(mousepos):
                self.train.track_id = yard_buttons[i][1]
                self.train.index = yard_buttons[i][2]
                self.train.direction = yard_buttons[i][3]
                clicked = True
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)
        return clicked

    def credits_button_click(self):
        mousepos = pygame.mouse.get_pos()
        if self.credits_button.collidepoint(mousepos):
            pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)
            return True
        return False

    def menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, SIDE_PANEL_COLOR, self.right_panel, 0)
        self.set_button_colors()
        for i in range(len(side_buttons)):
            pygame.draw.rect(self.screen, BUTTON_COLOR,
                             side_buttons[i][3], 0, 3)
            # key text:
            self.screen.blit(side_buttons[i][4],side_buttons[i][5])
            # description text:
            self.screen.blit(side_buttons[i][6], side_buttons[i][7])
        for i in range(len(yard_buttons)):
            pygame.draw.rect(self.screen, yard_buttons[i][5],yard_buttons[i][4],0,3)
            self.screen.blit(yard_buttons[i][6], yard_buttons[i][7])
        pygame.draw.rect(self.screen, BLACK, self.top_box)
        self.screen.blit(self.title_text, self.title_text_box)
        pygame.draw.rect(self.screen, self.credits_box_color, self.credits_button,0,3)
        self.screen.blit(self.credits_text, self.credits_box)
        pygame.display.flip()
        self.clock.tick(30)

    def credits(self):
        self.screen.fill(BUTTON_COLOR)
        for line in self.credits_lines:
            self.screen.blit(line[0], line[1])
        pygame.display.flip()
        self.clock.tick(30)


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

        top_text = self.logo_font.render("Pacific", True, HEADLIGHT_COLOR)
        bottom_text = self.logo_font.render("Railroad", True, HEADLIGHT_COLOR)
        top_rect = top_text.get_rect()
        top_rect.bottomright = (self.width - 20, self.height // 2 - 20)
        bottom_rect = bottom_text.get_rect()
        bottom_rect.topright = (self.width - 20, self.height // 2 + 20)

        while headlight_shape[0][0] < self.width + 700:
            self.screen.fill(BACKGROUND_COLOR)

            for i in range(len(headlight_shape)):
                headlight_shape[i] += shift
            if headlight_shape[0][0] > self.width - 300:
                fade = [min(255,i + 5) for i in fade]
                top_text = self.logo_font.render("Pacific", True, fade)
                bottom_text = self.logo_font.render("Railroad", True, fade)
            self.screen.blit(top_text, top_rect)
            self.screen.blit(bottom_text, bottom_rect)
            pygame.draw.polygon(
                self.screen, HEADLIGHT_COLOR, headlight_shape, width=0)
            pygame.draw.line(
                self.screen, WHITE, track_1[0], track_1[1])
            pygame.draw.line(
                self.screen, WHITE, track_2[0], track_2[1])
            pygame.draw.circle(
                self.screen, TRAIN_COLOR, headlight_shape[0], 4)
            pygame.display.flip()
            self.clock.tick(30)