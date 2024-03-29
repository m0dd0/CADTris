from collections import deque
import random
from typing import Dict, List, Tuple
from copy import deepcopy
import threading

from ...libs.fusion_addin_framework import fusion_addin_framework as faf
from ... import config
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
    Z = deque([{(2, 2), (2, 1), (1, 1), (1, 0)}, {(0, 1), (1, 1), (1, 0), (2, 0)}])
    S = deque([{(1, 2), (1, 1), (2, 1), (2, 0)}, {(2, 1), (3, 1), (1, 0), (2, 0)}])
    L = deque(
        [
            {(1, 2), (2, 2), (1, 1), (1, 0)},
            {(0, 2), (0, 1), (1, 1), (2, 1)},
            {(1, 2), (1, 1), (1, 0), (0, 0)},
            {(0, 1), (1, 1), (2, 1), (2, 0)},
        ]
    )
    J = deque(
        [
            {(1, 2), (2, 2), (2, 1), (2, 0)},
            {(1, 1), (2, 1), (3, 1), (1, 0)},
            {(2, 2), (2, 1), (2, 0), (3, 0)},
            {(3, 2), (1, 1), (2, 1), (3, 1)},
        ]
    )
    T = deque(
        [
            {(1, 2), (1, 1), (2, 1), (1, 0)}, #1
            {(1, 2), (0, 1), (1, 1), (2, 1)}, #2
            {(1, 2), (0, 1), (1, 1), (1, 0)}, #3
            {(0, 1), (1, 1), (2, 1), (1, 0)}, #4
        ]
    )
    O = deque([{(1, 1), (2, 1), (1, 0), (2, 0)}])
    all_figures = [I, Z, S, L, J, T, O]

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
        # assert any([c[1] == 0 for c in self._figure_coords[0]])
        self._actual_coords = None
        self._update_actual_coords()
        self._color_code = random.randint(1, len(config.CADTRIS_TETRONIMO_COLORS))

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

    @property
    def color_code(self) -> int:
        """A number which represents the color of the figure. Which color gets applied finally
        is determined by the Screen instance.
        """
        return self._color_code

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
    # all public methods will update the display after they have executed

    def __init__(self, display: TetrisDisplay):
        """Creates a game according to passed parameters. Sets the initial state to "start"
        and calls the displays upate function once.

        Args:
            display (TetrisDisplay): The display which controls how the game is visualized.
        """
        self._display = display

        assert (
            config.CADTRIS_MIN_HEIGHT
            <= config.CADTRIS_INITIAL_HEIGHT
            <= config.CADTRIS_MAX_HEIGHT
        )
        assert (
            config.CADTRIS_MIN_WIDTH
            <= config.CADTRIS_INITIAL_WIDTH
            <= config.CADTRIS_MAX_WIDTH
        )
        # we set the inital height by the config but it might chamge later due to user input
        self._height = config.CADTRIS_INITIAL_HEIGHT
        self._width = config.CADTRIS_INITIAL_WIDTH

        self._active_figure = None
        self._field = {}  # {(x,y):color_code} x=[0...width-1] y=[0...height-1]
        self._go_down_scheduler = faf.utils.PeriodicExecuter(
            1 / config.CADTRIS_MIN_SPEED,
            lambda: self._move_vertical(-1),
            # True # do not set this as it might lead to unstable behaviour (for unknown reason)
        )
        self._action_lock = threading.Lock()

        self._state = None  # "start" "running" "pause", "gameover"
        self._allowed_actions = None  # "start" "pause" "reset" "move" "change"
        self._set_state("start")

        self._score = None
        self._lines = None
        self._level = None
        self._reset_scores()

        self._update_display()

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
            "allowed_actions": self._allowed_actions,
            "figure": self._active_figure.serialize()
            if self._active_figure is not None
            else None,
            "lines": self._lines,
            "score": self._score,
            "level": self._level,
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
            self._field[p] = self._active_figure.color_code
        self._active_figure = None

    def _new_figure(self):
        """Creates a mew figure at the initial top middle position"""
        self._active_figure = Figure(self._width // 2 - 1, self._height)
        self._go_down_scheduler.reset()

    def _reset_scores(self):
        """Resets all score related attributes and also resets the interval for the go down timer."""
        self._score = 0
        self._level = 1
        self._lines = 0
        self._go_down_scheduler.interval = 1 / config.CADTRIS_MIN_SPEED

    def _update_score(self, broken_lines: int):
        """Updates all score related attributes (lines, score, level) and also updates the go down
        interval accordignaly. Should be executed after lines were collapsed.

        Args:
            broken_lines (int): The number of lines beeing removed which lead to the increase of the score.
        """
        self._lines += broken_lines
        self._score += broken_lines**2
        self._level = min(
            self._lines // config.CADTRIS_LINES_PER_LEVEL + 1,
            config.CADTRIS_MAX_LEVEL,
        )
        self._go_down_scheduler.interval = 1 / (
            config.CADTRIS_MIN_SPEED
            + (config.CADTRIS_MAX_SPEED - config.CADTRIS_MIN_SPEED)
            * ((self._level - 1) / (config.CADTRIS_MAX_LEVEL - 1))
        )

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

    def _set_state(self, new_state: str):
        """Sets the game state to the passed value and sets the go down scheduler accordingly.
        Also does everything else whihc is needed in a game state change.
        The main idea of this function is to have a single place where all allowed actions are defined
        for each state.
        (ALternativly we could maintain a dictionary which maps the actions to the states, but then it
        would be more complicated to pass the allowed action to the display)

        Args:
            new_state (str): The new state to set. Possible values are {"pause","running","start","gameover"}.

        Raises:
            ValueError: If the passed new state is no valid name of a game state.
        """
        if new_state == "pause":
            self._go_down_scheduler.pause()
            self._allowed_actions = ("start", "reset")
        elif new_state == "running":
            if self._state == "start":
                assert self._active_figure is None
                self._new_figure()
            self._go_down_scheduler.start()
            self._allowed_actions = ("pause", "reset", "move")
        elif new_state == "start":
            self._active_figure = None
            self._field = {}
            self._go_down_scheduler.pause()
            self._go_down_scheduler.reset()
            self._reset_scores()
            self._allowed_actions = ("start", "change")
        elif new_state == "gameover":
            self._active_figure = None
            self._go_down_scheduler.pause()
            self._allowed_actions = ("reset",)
        elif new_state == "terminated":
            self._go_down_scheduler.pause()
            self._allowed_actions = ()
        else:
            raise ValueError("Invalid state.")
        self._state = new_state

    def start(self):
        """Starts or continues the game when the game state is either "start" or "pause".
        Otherwise nothing happens.
        This sets the gamestate to running.
        Updates the dsiplay.
        """
        with self._action_lock:
            if "start" in self._allowed_actions:
                self._set_state("running")
                self._update_display()

    def pause(self):
        """Pauses the gane if its currently in state "running".
        Otherwise nothing happens.
        Sets the gamestate to pause.
        Updates the dsiplay.
        """
        with self._action_lock:
            if "pause" in self._allowed_actions:
                self._set_state("pause")
                self._update_display()

    def reset(self):
        """Resets the game (independent on its state).
        Otherwise nothing happens.
        Sets the gamestate to "start".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "reset" in self._allowed_actions:
                self._set_state("start")
                self._update_display()

    def terminate(self):
        """Ultimately terminates the game. ITs not possible to do anything after the game has been terminated.
        A game can always get terminated. No screen update is executed. Stops the go down scheduler.
        """
        with self._action_lock:
            self._set_state("terminated")

    def _move_vertical(self, n):
        """Moves the active figure n steps vertically and executes all resulting
        game/field effects. N>0 --> up, n<0 --> down.

        Args:
            n (int): The direction and number of steps to move.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                self._active_figure.move_vertical(n)
                if self._intersects():
                    self._active_figure.move_vertical(-n)
                    self._freeze()
                self._update_display()

    def drop(self):
        """Moves the active figure to as low as possible and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                while not self._intersects():
                    self._active_figure.move_vertical(-1)
                self._active_figure.move_vertical(1)
                self._freeze()
                self._update_display()

    def _move_horizontal(self, n):
        """Moves the active figure n steps horizontally and executes all resulting
        game/field effects. N>0 --> right, n<0 --> left.

        Args:
            n (int): The direction and number of steps to move.
        """
        self._active_figure.move_horizontal(n)
        if self._intersects():
            self._active_figure.move_horizontal(-n)

    def move_right(self):
        """Moves the active figure horizontally to the right and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                self._move_horizontal(1)
                self._update_display()

    def move_left(self):
        """Moves the active figure horizontally to the right left executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                self._move_horizontal(-1)
                self._update_display()

    def _rotate(self, n: int):
        """Rotates the active figure n times when the filed is free.

        Args:
            n (int): Number of 90 degree rotations.
        """
        self._active_figure.rotate(n)
        if self._intersects():
            self._active_figure.rotate(-n)

    def rotate_right(self):
        """Rotates the figure by 90 degrees clockwise if the field is free.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                self._rotate(1)
                self._update_display()

    def rotate_left(self):
        """Rotates the figure by 90 degrees counterclockwise if the field is free.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        with self._action_lock:
            if "move" in self._allowed_actions:
                self._rotate(-1)
                self._update_display()

    def set_width(self, new_width: int):
        """Sets the width of the game. This can only be done in the start state.
        If an new_width is given which is outside the range defined in the configs nothing will be done.

        Args:
            new_width (int): The new width to set.
        """
        with self._action_lock:
            if "change" in self._allowed_actions:
                if config.CADTRIS_MIN_WIDTH <= new_width <= config.CADTRIS_MAX_WIDTH:
                    self._width = new_width
                    self._update_display()

    def set_height(self, new_height: int):
        """Sets the height of the game. This can only be done in the start state.
        If an new_height is given which is outside the range defined in the configs nothing will be done.

        Args:
            new_height (int): The new height to set.
        """
        with self._action_lock:
            if "change" in self._allowed_actions:
                if config.CADTRIS_MIN_HEIGHT <= new_height <= config.CADTRIS_MAX_HEIGHT:
                    self._height = new_height
                    self._update_display()
