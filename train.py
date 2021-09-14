from utils import *
import pygame


class Train:
    def __init__(self, track_id, index=0, offset=0, direction=FORWARDS):
        self.board = None
        self.track_id = track_id  # The id of the track that we're on
        self.index = index  # Where along the track it is
        self.offset = offset  # How much past the index we are
        self.direction = direction
        # are we currently going forwards or backwards?
        self.speed = 0
        self.blinker = NO_BLINK
        self.slowing = False

    def speed_up(self):
        if self.speed < 2:
            self.speed = 2
        elif self.speed <= 100:
            self.speed *= 1.5

    def slow_down(self):
        if self.speed >= 2:
            self.speed /= 1.5
        else:
            self.speed = 0

    def stop(self):
        self.blinker = NO_BLINK
        if self.speed == 0:
            self.speed_up()
        else:
            self.slowing = True

    def attatch_board(self, board):
        self.board = board

    def set_blinker(self, new_blink):
        if new_blink == self.blinker:
            self.blinker = NO_BLINK
        else:
            self.blinker = new_blink
        print(self.blinker)

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
                point0 = get_second_point(MAP_DATA[self.track_id][source][0])
                point1 = get_second_point(MAP_DATA[self.track_id][source][1])
                vertex = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index])
                point1dir = which_side(point0, vertex, point1)
                if point1dir == self.blinker:
                    self.track_id, self.index, self.direction = MAP_DATA[self.track_id][source][1]
                else:
                    self.track_id, self.index, self.direction = MAP_DATA[self.track_id][source][0]

        elif ((self.index, self.direction) in
                MAP_DATA[self.track_id]['middlejoins']):
            if self.direction == FORWARDS:
                next_pt = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index + 1])
            else:
                next_pt = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index - 1])
            vertex = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index])
            other = get_second_point(MAP_DATA[self.track_id]['middlejoins'][(self.index, self.direction)])
            offshoot_dir = which_side(next_pt, vertex, other)
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
                    self.index -= 1
                    self.offset = MAP_DATA[self.track_id]['distances'][self.index]
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

    def step(self):
        if self.slowing == True:
            if self.speed > 5:
                self.speed *= 0.9
            elif self.speed > 0:
                self.speed -= 1
            else:
                self.speed = 0
                self.slowing = False
                self.direction = not self.direction
        if not self.move(self.speed):
            self.speed = 0
            self.direction = not self.direction
            return False
        return True

    def current_position(self):
        if self.offset == 0:
            return MAP_DATA[self.track_id]['coordinates'][self.index]
        prev_coord = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index])
        next_coord = pygame.Vector2(MAP_DATA[self.track_id]['coordinates'][self.index + 1])
        percent = self.offset / MAP_DATA[self.track_id]['distances'][self.index]
        return prev_coord + percent * (next_coord - prev_coord)

    def debugpos(self):
        print(f'{self.index}, {self.track_id}, {self.offset}, [{MAP_DATA[self.track_id]["coordinates"][self.index]}]')
