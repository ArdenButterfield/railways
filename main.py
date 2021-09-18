from train import Train
from board import Board
from music import Music
from controller import Controller
from utils import *

if __name__ == "__main__":
    size = width, height = 1000, 500
    train = Train(429099625, direction=FORWARDS, index=8, offset=10)
    board = Board(train, size)
    music = Music()
    train.attatch_board(board)
    controller = Controller(board, train, music)
    controller.play()