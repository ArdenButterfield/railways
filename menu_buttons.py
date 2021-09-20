import pygame

# Name, track id, index, direction
yard_buttons = [
    ["Seattle", 334242083, 0, True],
    ["Spokane", 93178066, 16, False],
    ["Portland", 5518741, 0, False],
    ["Eugene", 47472443, 57, True],
    ["La Grande",222664295, 0, True],
    ["San Francisco", 37311641, 0, True],
    ["Los Angeles", 907208132, 2, False],
    ["San Diego",95489049, 34, False]
]

side_buttons = [
    [pygame.K_UP, "UP", "Speed up"],
    [pygame.K_DOWN, "DOWN", "Slow down"],
    [pygame.K_LEFT, "LEFT", "Set turn signal"],
    [pygame.K_RIGHT, "RIGHT", ""],
    [pygame.K_SPACE, "SPACE", "Stop/start, turn around"],
    [pygame.K_z, "Z", "Change zoom level"],
    [pygame.K_RETURN, "RETURN", "Toggle menu screen"]
]