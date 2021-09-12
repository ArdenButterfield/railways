import pickle
from pygame import Vector2

with open("data/PNW.pickle", 'rb') as f:
    MAP_DATA, ZONE_DIR = pickle.load(f)

FORWARDS = True
BACKWARDS = False
LEFT_BLINK = -1
NO_BLINK = 0
RIGHT_BLINK = 1

def get_zone(coord):
    return (int(coord[0] // 1000), int(coord[1] // 1000))

def which_side(a,vert,b):
    # Which side is vector from vert to b, relative to vector from vert to a?
    # Uses the dot product, as described here:
    # https://stackoverflow.com/questions/13221873/
    rot_b = (b - vert).rotate(90)
    # Rotated 90 deg counter clockwise, centered at 0
    a -= vert # centered at 0
    dot_prod = a.dot(rot_b)
    return LEFT_BLINK if dot_prod < 0 else RIGHT_BLINK