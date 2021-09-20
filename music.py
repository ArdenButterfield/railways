from pygame import mixer
from utils import *

class Music:
    def __init__(self):
        mixer.init()
        self.menu_music = mixer.Sound("gameaudio/menu.wav")
        self.top_music = mixer.Sound("gameaudio/Ramblin Railroad TEST TOP.wav")
        self.bottom_music = mixer.Sound("gameaudio/Ramblin Railroad TEST BOTTOM.wav")
        self.left_music = mixer.Sound("gameaudio/Ramblin Railroad TEST L.wav")
        self.right_music = mixer.Sound("gameaudio/Ramblin Railroad TEST R.wav")

    def set_volumes(self, point):
        x,y = point
        x_offset = (x - MIN_X) / (MAX_X - MIN_X)
        y_offset = (y - MIN_Y) / (MAX_Y - MIN_Y)
        self.top_music.set_volume(y_offset)
        self.bottom_music.set_volume(1 - y_offset)
        self.left_music.set_volume(1 - x_offset)
        self.right_music.set_volume(x_offset)

    def menu(self):
        print("start menu")
        self.menu_music.play(fade_ms=5000)
        self.top_music.stop()
        self.bottom_music.stop()
        self.left_music.stop()
        self.right_music.stop()

    def game(self):
        self.menu_music.stop()
        self.top_music.play(fade_ms=5000)
        self.bottom_music.play(fade_ms=5000)
        self.left_music.play(fade_ms=5000)
        self.right_music.play(fade_ms=5000)