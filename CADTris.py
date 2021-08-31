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
    def __init__(self, world, height, width):
        self._world = world

        self._height = height
        self._width = width

        self._active_figure = None
        self._field = {}  # {(x,y):(r,g,b)}
        # self._state = "start"  # "running" "pause", "gameover"

    def _intersects(self):
        for x, y in self._active_figure.coords:
            if x >= self._width or x < 0 or y < 0 or (x, y) in self._field:
                return True
        return False

    def _freeze(self):
        for p in self._active_figure.coords:
            self._field[p] = self._active_figure.color
        broken_lines = 0
        for y in range(self._height, -1, -1):  # from top to botton
            if all((x, y) in self._field for x in range(self._width)):  # full line
                for p in set(self._field.keys()):  # remove row
                    if p.y == y:
                        self._field.pop(p)
                new_field = {}
                for (x_new, y_new), c in self._field.items():  # lower all points above
                    new_field[(x_new, y_new - 1 if y_new > y else y_new)] = c
                self._field = new_field
                broken_lines += 1

    # def start(self):
    #     # TODO
    #     if self._state in ["start", "paused"]:
    #         self._state = "running"
    #         self._active_figure = Figure(self.width // 2 - 1, self.height - 3)

    # def pause(self):
    #     # TODO
    #     if self._state == "running":
    #         pass

    # def reset(self):
    #     # TODO
    #     # you can always reset a game
    #     pass

    def down(self):
        self._active_figure.move_vertical(-1)
        if self._intersects():
            self._active_figure.move_vertical(1)
            self._freeze()

    def drop(self):
        pass

    def drop(self):
        if self.state == "running":
            while not self._intersects():
                self.figure.move_vertical(-1)
            self.figure.move_vertical(1)
            self._freeze()
            self.go_down_timer.reset()
            self.screen.draw_field(self)

    def move_down(self, n):
        if self._state == "running":
            self._active_figure.move_vertical(-n)
            if self._intersects():
                self._active_figure.move_vertical(n)
                self._freeze()
            self.go_down_timer.reset()
            self.screen.draw_field(self)

    def move_side(self, n):
        if self.state == "running":
            self.figure.move_horizontal(n)
            if self._intersects():
                self.figure.move_horizontal(-n)
            self.screen.draw_field(self)

    def rotate(self, n):
        if self.state == "running":
            self.figure.rotate(n)
            if self._intersects():
                self.figure.rotate(-n)
            self.screen.draw_field(self)

    def update_world(self):
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
