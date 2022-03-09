from collections import deque
import random
from typing import Dict, List, Tuple
from copy import deepcopy

try:
    from ..fusion_addin_framework.fusion_addin_framework.utils import PeriodicExecuter
except:
    # this import is used when tested without a Fusion instance from the "main_test.py" file
    # the fusion_addin_framework must be pip installed to the current venv therefore
    from fusion_addin_framework.utils import PeriodicExecuter

from .ui import TetrisDisplay


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
    Z = deque([{(2, 3), (2, 2), (1, 2), (1, 1)}, {(0, 2), (1, 2), (1, 1), (2, 1)}])
    S = deque([{(1, 3), (1, 2), (2, 2), (2, 1)}, {(2, 2), (3, 2), (1, 1), (2, 1)}])
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

    # figure_colors = [
    #     (255, 0, 0, 255),
    #     (0, 255, 0, 255),
    #     (0, 0, 255, 255),
    #     (255, 255, 0, 255),
    #     (0, 255, 255, 255),
    #     (255, 0, 255, 255),
    # ]
    n_colors = 6

    def __init__(self, x: int, y: int):
        """Creates a figure instance with a random shape and color. The initial
        position of the figure coordinate system is set according to the x and y
        values.

        Args:
            x (int): Initial x position of the figure.
            y (int): Initial x position of the figure.
        """
        self._x = x
        self._y = y

        self._figure_coords = random.choice(self.all_figures)
        self._actual_coords = None
        self._update_actual_coords()
        self._color_code = random.randint(1, self.n_colors)

    def serialize(self) -> Dict:
        """Creates a serialized version of the figure. This serialization contains
        only primitive datatype but contains all information to visualize or rebuild it.

        Returns:
            Dict: The serialized game.
        """
        return {
            "coordinates": deepcopy(self._actual_coords),
            "color_code": self._color_code,
        }

    def _update_actual_coords(self):
        self._actual_coords = [
            (c[0] + self._x, c[1] + self._y) for c in self._figure_coords[0]
        ]

    @property
    def coords(self) -> List[Tuple[int]]:
        """Returns a list of all coordinates of the elements of the figure. The
        coordinates are relative to the nivenebt of figure and the initial coordinate.

        Returns:
            List[Tuple[int]]: The coordinates of the elements of the figure.
        """
        return self._actual_coords

    def rotate(self, n: int) -> None:
        """Rotates the figure n times by 90 degress clockwise by updates its coordinates accordingly.
        A value <1 means rotating it conunterclockwise.

        Args:
            n (int): The number of 90 degree rotations.
        """
        self._figure_coords.rotate(n)
        self._update_actual_coords()

    def move_vertical(self, n: int):
        """Moves the figure n steps in y direction.

        Args:
            n (int): Number of steps to move the figure
        """
        self._y += n
        self._update_actual_coords()

    def move_horizontal(self, n: int):
        """Moves the figure n steps in x direction.

        Args:
            n (int): Number of steps to move the figure
        """
        self._x += n
        self._update_actual_coords()


# region
# state pattern is a overkill but its a nice example to practice so heres the state base class, just in case ....
# class GameState(ABC):
#     @abstractmethod
#     def start(self):
#         pass

#     @abstractmethod
#     def pause(self):
#         pass

#     @abstractmethod
#     def reset(self):
#         pass

#     @abstractmethod
#     def drop(self):
#         pass

#     @abstractmethod
#     def move_vertical(self,n):
#         pass

#     @abstractmethod
#     def move_horizontal(self, n):
#         pass

#     @abstractmethod
#     def rotate(self, n):
#         pass
# endregion


class TetrisGame:
    width_range = (9, 50)
    height_range = (9, 100)
    max_level = 5
    lines_per_level = 6
    speed_range = (0.8, 0.35)

    ## all public methods will update the display after they have executed
    def __init__(self, display: TetrisDisplay, height: int, width: int):
        """Creates a game according to passed parameters. Sets the initial state to "start"
        and calls the displays upate function once.

        Args:
            display (TetrisDisplay): The display which controls how the game is visualized.
            height (int): The height of the tetris field (only the inner, fillable area).
            width (int): The width of the tetris field (only the inner, fillable area).
        """
        self._display = display

        assert self.height_range[0] <= height <= self.height_range[1]
        assert self.width_range[0] <= width <= self.width_range[1]
        self._height = height
        self._width = width

        self._active_figure = None
        self._field = {}  # {(x,y):(r,g,b)} x=[0...width-1] y=[0...height-1]
        self._state = "start"  # "running" "pause", "gameover"
        self._go_down_scheduler = PeriodicExecuter(1, lambda: self._move_vertical(-1))

        self._score = 0
        self._lines = 0
        self._level = 1

        self._display.update(self._serialize())

    def _serialize(self) -> Dict:
        """Creates a serialized version of the current game state. This serialization contains
        only primitive datatype but contains all information to visualize the game or rebuild it.
        All containers are deepcopied to avoid a manipulation of the game state from "outside".

        Returns:
            Dict: The serialized game.
        """
        return {
            "height": self._height,
            "width": self._width,
            "field": deepcopy(self._field),
            "state": self._state,
            "figure": self._active_figure.serialize()
            if self._active_figure is not None
            else None,
        }

    def _update_display(self):
        """Calls the update function of the display with the serialized game."""
        self._display.update(self._serialize())

    def _intersects(self) -> bool:
        """Returns whether the _activae_figure intersects with the frame, a other tetromino or is
        below the bottom.

        Returns:
            bool: True if intersects, False if valid position.
        """
        for x, y in self._active_figure.coords:
            if x >= self._width or x < 0 or y < 0 or (x, y) in self._field:
                return True
        return False

    def _full_row(self, y: int) -> bool:
        """Gets if all fields in the line y are occupied by blocks.

        Args:
            y (int): The y coordinate of the line to check.

        Returns:
            bool: Wheteher the line is fully occupied.
        """
        return all((x, y) in self._field for x in range(self._width))

    def _remove_row(self, y: int) -> None:
        """Removes all elements of the given row by popping the coords from the field_dict.

        Args:
            y (int): The y coorinate of the row to remove.
        """
        for p in set(self._field.keys()):
            if p[1] == y:
                self._field.pop(p)

    def _lower_rows_above(self, y: int) -> None:
        """Lowers the y coordinate of all filed coordinates by 1 if their y coordiante is
        above the given y.

        Args:
            y (int): The y coordiante above which all other coordiantes get lowered.
        """
        new_field = {}
        for (x_new, y_new), c in self._field.items():  # lower all points above
            if y_new > y:
                new_coords = (x_new, y_new - 1)
            else:
                new_coords = (x_new, y_new)
            new_field[new_coords] = c
        self._field = new_field

    def _add_figure_to_field(self):
        """Adds the elements of the active_figure to the field and sets the active figure to None."""
        for p in self._active_figure.coords:
            self._field[p] = self._active_figure._color_code
        self._active_figure = None

    def _new_figure(self):
        """Creates a mew figure at the initial top middle position"""
        self._active_figure = Figure(self._width // 2 - 1, self._height - 4)

    def _update_score(self, broken_lines: int):
        self._lines += broken_lines
        self._score += broken_lines**2
        self._level = min(self._lines // self.lines_per_level + 1, self.max_level)
        max_interval, min_interval = self.speed_range
        self._go_down_scheduler.interval = max_interval - (
            max_interval - min_interval
        ) * (self._level / self.max_level)

    def _freeze(self) -> int:
        """Updates the field according to the current state of the active figure.
        Therfore should only be called when active figure has reached its final position
        in the field.

        Returns:
            int: How many rows got destroyed due to the location of the figure.
        """
        self._add_figure_to_field()

        broken_lines = 0

        for y in range(self._height - 1, -1, -1):  # from top to botton
            if self._full_row(y):
                self._remove_row(y)
                self._lower_rows_above(y)
                broken_lines += 1

        self._update_score(broken_lines)

        self._new_figure()
        if self._intersects():
            self._set_state("gameover")
            self._active_figure = None

    def _set_state(self, new_state):
        if new_state == "pause":
            self._go_down_scheduler.pause()
        elif new_state == "running":
            self._go_down_scheduler.start()
        elif new_state == "start":
            self._go_down_scheduler.pause()
            self._go_down_scheduler.reset()
            # self._go_down_scheduler.interval = self._interval # TODO
        elif new_state == "gameover":
            self._go_down_scheduler.pause()
        else:
            raise ValueError("Invalid state.")
        self._state = new_state

    def start(self):
        """Starts or continues the game when the game state is either "start" or "pause".
        Otherwise nothing happens.
        This sets the gamestate to running.
        Updates the dsiplay.
        """
        if self._state in ["start", "pause"]:
            if self._state == "start":
                assert self._active_figure is None
                self._new_figure()
            self._set_state("running")
            self._display.update(self._serialize())

    def pause(self):
        """Pauses the gane if its currently in state "running".
        Otherwise nothing happens.
        Sets the gamestate to pause.
        Updates the dsiplay.
        """
        if self._state == "running":
            self._set_state("pause")
            self._display.update(self._serialize())

    def reset(self):
        """Resets the game (independent on its state).
        Otherwise nothing happens.
        Sets the gamestate to "start".
        Updates the dsiplay.
        """
        # you can always reset a game
        self._active_figure = None
        self._field = {}
        self._set_state("start")
        self._display.update(self._serialize())

    def _move_vertical(self, n):
        """Moves the active figure n steps vertically and executes all resulting
        game/field effects. N>0 --> up, n<0 --> down.

        Args:
            n (int): The direction and number of steps to move.
        """
        if self._state == "running":
            self._active_figure.move_vertical(n)
            if self._intersects():
                self._active_figure.move_vertical(-n)
                self._freeze()
            self._display.update(self._serialize())

    def drop(self):
        """Moves the active figure to as low as possible and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        if self._state == "running":
            while not self._intersects():
                self._active_figure.move_vertical(-1)
            self._active_figure.move_vertical(1)
            self._freeze()
            self._display.update(self._serialize())

    def _move_horizontal(self, n):
        """Moves the active figure n steps horizontally and executes all resulting
        game/field effects. N>0 --> right, n<0 --> left.

        Args:
            n (int): The direction and number of steps to move.
        """
        if self._state == "running":
            self._active_figure.move_horizontal(n)
            if self._intersects():
                self._active_figure.move_horizontal(-n)
            self._display.update(self._serialize())

    def move_right(self):
        """Moves the active figure horizontally to the right and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._move_horizontal(1)

    def move_left(self):
        """Moves the active figure horizontally to the right left executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._move_horizontal(-1)

    def _rotate(self, n: int):
        """Rotates the active figure n times when the filed is free.

        Args:
            n (int): Number of 90 degree rotations.
        """
        if self._state == "running":
            self._active_figure.rotate(n)
            if self._intersects():
                self._active_figure.rotate(-n)
            self._display.update(self._serialize())

    def rotate_right(self):
        """Rotates the figure by 90 degrees clockwise if the field is free.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._rotate(1)

    def rotate_left(self):
        """Rotates the figure by 90 degrees counterclockwise if the field is free.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._rotate(-1)
