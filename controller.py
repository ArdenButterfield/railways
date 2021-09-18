import pygame
from utils import *
import sys

class Controller:
    def __init__(self, board, train, music):
        self.board = board
        self.train = train
        self.music = music
        self.on_menu = False

    def send_blinker(self, blink):
        vect = self.train.train_vector()
        if vect[1] > 0:
            self.train.set_blinker(blink)
        else:
            self.train.set_blinker(-blink)

    def toggle_menu(self):
        if self.on_menu:
            self.on_menu = False
            self.music.game()
        else:
            self.on_menu = True
            self.music.menu()

    def take_input(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.toggle_menu()
                if event.key == pygame.K_LEFT:
                    self.send_blinker(LEFT_BLINK)
                elif event.key == pygame.K_RIGHT:
                    self.send_blinker(RIGHT_BLINK)
                elif event.key == pygame.K_UP:
                    self.train.speed_up()
                elif event.key == pygame.K_DOWN:
                    self.train.slow_down()
                elif event.key == pygame.K_SPACE:
                    self.headlight_direction = None
                    self.train.stop()
                elif event.key == pygame.K_z:
                    self.board.change_scale_level()
            elif event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.board.resize(event.w, event.h)

    def play(self):
        self.board.logo()
        self.toggle_menu()
        while True:
            self.take_input()
            if self.on_menu:
                leave_reason = None
                while not leave_reason:
                    leave_reason = self.board.menu()
                    if leave_reason == "return":
                        self.toggle_menu()
            else:
                if not self.train.step():
                    self.board.headlight_direction = None
                self.board.draw_lines()