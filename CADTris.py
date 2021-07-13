from collections import deque
import random

import fusion_addin_framework as faf
from cuber import VoxelWorld

import adsk.core, adsk.fusion, adsk.cam, traceback


class Figure:
    #   y
    #   ^
    # 3 | (0,3) (1,3) (2,3) (3,3)
    # 2 | (0,2) (1,2) (2,2) (3,2)
    # 1 | (0,1) (1,1) (2,1) (3,1)
    # 0 | (0,0) (1,0) (2,0) (3,0)
    #     ------------------------> x
    #      0     1     2     3

    I = deque([{(1, 3), (1, 2), (1, 1), (1, 0)}, {(0, 2), (1, 2), (2, 2), (3, 2)}])
    Z = deque([{(0, 2), (1, 2), (1, 1), (2, 1)}, {(2, 3), (2, 2), (1, 2), (1, 1)}])
    S = deque([{(2, 2), (3, 2), (1, 1), (2, 1)}, {(1, 3), (1, 2), (2, 2), (2, 1)}])
    L = deque(
        [
            {(1, 3), (2, 3), (1, 2), (1, 1)},
            {(0, 3), (0, 2), (1, 2), (2, 2)},
            {(1, 3), (1, 2), (1, 1), (0, 1)},
            {(0, 2), (1, 2), (2, 2), (2, 1)},
        ]
    )
    J = deque(
        [
            {(1, 3), (2, 3), (2, 2), (2, 1)},
            {(1, 2), (2, 2), (3, 2), (1, 1)},
            {(2, 3), (2, 2), (2, 1), (3, 1)},
            {(3, 3), (1, 2), (2, 2), (3, 2)},
        ]
    )
    T = deque(
        [
            {(1, 3), (0, 2), (1, 2), (2, 2)},
            {(1, 3), (0, 2), (1, 2), (1, 1)},
            {(0, 2), (1, 2), (2, 2), (1, 1)},
            {(1, 3), (1, 2), (2, 2), (1, 1)},
        ]
    )
    O = deque([{(1, 3), (2, 3), (1, 2), (2, 2)}])
    all_figures = [I, Z, S, L, J, T, O]

    figure_colors = [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
        (0, 255, 255, 255),
        (255, 0, 255, 255),
    ]

    def __init__(self, x, y):
        self._x = x
        self._y = y

        self._figure_coords = random.choice(self.all_figures)
        self.color = random.choice(self.figure_colors)

    @property
    def coords(self):
        return [(c[0] + self._x, c[1] + self._y) for c in self._figure_coords]

    def rotate(self, n=1):
        self._figure_coords.rotate(n)

    def move_vertical(self, n):
        self._y += n

    def move_horizontal(self, n):
        self._x += n


class Game:
    def __init__(self, height, width):
        pass

    def start(self):
        se

    def stop(self):
        pass

    def pause(self):
        pass

    def down(self):
        pass

    def drop(self):
        pass

    def left(self):
        pass

    def right(self):
        pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox("Hello addin")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox("Stop addin")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
