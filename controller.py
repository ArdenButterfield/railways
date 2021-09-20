import pygame
from utils import *
import sys

class Controller:
    def __init__(self, board, train, music):
        self.board = board
        self.train = train
        self.music = music
        self.on_menu = False
        self.on_credits = False

    def send_blinker(self, blink):
        # This makes the blinker more intuitive: we blink from the user
        # perspective, instead of from the train perspective.
        vect = self.train.train_vector()
        if vect[1] > 0:
            self.train.set_blinker(blink)
        else:
            self.train.set_blinker(-blink)

    def toggle_menu(self):
        print("toggle, on menu prev?", self.on_menu)
        if self.on_menu:
            self.on_menu = False
            self.train.speed = 0
            self.music.game()
        else:
            self.on_menu = True
            self.music.menu()

    def take_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if self.on_credits == True:
                    self.on_credits = False
                    break
                if event.key == pygame.K_RETURN:
                    self.toggle_menu()
                    break
                elif self.on_menu == False:
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
            elif event.type == pygame.VIDEORESIZE:
                self.board.resize(event.w, event.h)
            elif event.type == pygame.MOUSEBUTTONDOWN and self.on_menu:
                if self.board.yard_button_click():
                    self.toggle_menu()
                    break
                elif self.board.credits_button_click():
                    self.on_credits = True
                    break

    def play(self):
        self.board.logo()
        self.toggle_menu()
        while True:
            self.take_input()
            if self.on_credits:
                self.board.credits()
            elif self.on_menu:
                self.board.menu()
            else:
                if not self.train.step():
                    self.board.headlight_direction = None
                self.board.draw_lines()
                self.music.set_volumes(self.train.current_position())