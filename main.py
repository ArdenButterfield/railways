from train import Train
from railroad_game import Board
from utils import *

if __name__ == "__main__":
    size = width, height = 1000, 500
    train = Train(429099625, direction=FORWARDS, index=8, offset=10)
    board = Board(train, size)
    train.attatch_board(board)
    board.play()