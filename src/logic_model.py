from collections import deque
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from copy import deepcopy


class Display(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """
        pass


class TetrisDisplay(Display):
    def __init__(self) -> None:
        super().__init__()


class AsciisDisplay(TetrisDisplay):
    def __init__(
        self,
        wall_char: str = "X",
        element_char: str = "O",
        air_char: str = " ",
        horizontal_spacing: str = "  ",
    ) -> None:
        self.horizontal_spacing = horizontal_spacing
        self.wall_char = wall_char + self.horizontal_spacing
        self.element_char = element_char + self.horizontal_spacing
        self.air_char = air_char + self.horizontal_spacing
        super().__init__()

    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """
        output = ""

        output += serialized_game["state"]
        output += "\n\n"

        for y in range(serialized_game["height"] - 1, -1, -1):  # from top to bottom
            output += self.wall_char
            for x in range(serialized_game["width"]):
                if (x, y) in serialized_game["field"].keys():
                    output += self.element_char
                else:
                    output += self.air_char
            output += self.wall_char
            output += "\n"

        output += self.wall_char * (serialized_game["width"] + 2)
        print(output)


class FusionDispaly(TetrisDisplay):
    def __init__(self) -> None:
        super().__init__()

    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """
        raise NotImplementedError()


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
        self.color = random.choice(self.figure_colors)

    def serialize(self) -> Dict:
        """Creates a serialized version of the figure. This serialization contains
        only primitive datatype but contains all information to visualize or rebuild it.

        Returns:
            Dict: The serialized game.
        """
        return {"coordinates": deepcopy(self._figure_coords), "color": self.color}

    @property
    def coords(self) -> List[Tuple[int]]:
        """Returns a list of all coordinates of the elements of the figure. The
        coordinates are relative to the nivenebt of figure and the initial coordinate.

        Returns:
            List[Tuple[int]]: The coordinates of the elements of the figure.
        """
        return [(c[0] + self._x, c[1] + self._y) for c in self._figure_coords]

    def rotate(self, n: int) -> None:
        """Rotates the figure n times by 90 degress clockwise by updates its coordinates accordingly.
        A value <1 means rotating it conunterclockwise.

        Args:
            n (int): The number of 90 degree rotations.
        """
        self._figure_coords.rotate(n)

    def move_vertical(self, n: int):
        """Moves the figure n steps in y direction.

        Args:
            n (int): Number of steps to move the figure
        """
        self._y += n

    def move_horizontal(self, n: int):
        """Moves the figure n steps in x direction.

        Args:
            n (int): Number of steps to move the figure
        """
        self._x += n


class TetrisGame:
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

        self._height = height
        self._width = width

        self._active_figure = None
        self._field = {}  # {(x,y):(r,g,b)} x=[0...width-1] y=[0...height-1]
        self._state = "start"  # "running" "pause", "gameover"

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
            if p.y == y:
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
            self._field[p] = self._active_figure.color
        self._active_figure = None

    def _new_figure(self):
        self._active_figure = Figure(self._width // 2 - 1, self._height - 4)

    def _check_gameover(self):
        for _, y in self._field.keys():
            if y >= self._height:
                return True
        return False

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

        if self._check_gameover():
            self.state = "gameover"
        else:
            self._new_figure()

        # return broken_lines

    def start(self):
        """Starts or continues the game when the game state is either "start" or "paused".
        Otherwise nothing happens.
        This sets the gamestate to running.
        Updates the dsiplay.
        """
        if self._state in ["start", "paused"]:
            if self._state == "start":
                assert self._active_figure is None
                self._active_figure = Figure(self._width // 2 - 1, self._height - 4)
            self._state = "running"
            self._display.update(self._serialize())

    def pause(self):
        """Pauses the gane if its currently in state "running".
        Otherwise nothing happens.
        Sets the gamestate to pause.
        Updates the dsiplay.
        """
        if self._state == "running":
            self._state = "pause"
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
        self._state = "start"
        self._display.update(self._serialize())

    def drop(self):
        """Moves the active figure to as low as possible and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        if self.state == "running":
            while not self._intersects():
                self.figure.move_vertical(-1)
            self.figure.move_vertical(1)
            self._freeze()
            self._display.update(self._serialize())
            # self.go_down_timer.reset()

    def _move_horizontally(self, n):
        """Moves the active figure n steps horizontally and executes all resulting
        game/field effects. N>0 --> right, n<0 --> left.

        Args:
            n (int): The direction and number of steps to move.
        """
        if self.state == "running":
            self.figure.move_horizontal(n)
            if self._intersects():
                self.figure.move_horizontal(-n)
            self._display.update(self._serialize())

    def move_right(self):
        """Moves the active figure horizontally to the right and executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._move_horizontally(1)

    def move_left(self):
        """Moves the active figure horizontally to the right left executes all resulting
        game/field effects.
        Is only executed when gamestate is "running".
        Updates the dsiplay.
        """
        self._move_horizontally(-1)

    def _rotate(self, n: int):
        """Rotates the active figure n times when the filed is free.

        Args:
            n (int): Number of 90 degree rotations.
        """
        if self.state == "running":
            self.figure.rotate(n)
            if self._intersects():
                self.figure.rotate(-n)
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


if __name__ == "__main__":
    from pynput import keyboard

    display = AsciisDisplay()
    game = TetrisGame(display, 15, 7)

    keymap = {
        "s": game.start,
        "p": game.pause,
        "r": game.reset,
        keyboard.Key.left: game.move_left,
        keyboard.Key.right: game.move_right,
        keyboard.Key.up: game.rotate_right,
        keyboard.Key.down: game.rotate_left,
        keyboard.Key.shift: game.drop,
    }

    def on_press(key):
        try:
            identifier = key.char
        except AttributeError:
            identifier = key

        keymap[identifier]()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
