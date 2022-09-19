"""This module tests the CADTris gam logic located in logic_model.py.
The test is not related to anything of Fusion360.
However there are some Fusion specific import statements in the related packages.
Therefore we mock them.
To allow importing the logic_model classes from this file the addin must be pip-installed this addin
via pip install -e .[dev].
"""

from unittest.mock import Mock
import sys

# adsk modules are not needed to test with Ascii Screen
sys.modules["adsk"] = Mock()
sys.modules["adsk.fusion"] = Mock()
sys.modules["adsk.core"] = Mock()

from addin.commands.CADTris.logic_model import TetrisGame
from addin.commands.CADTris.ui import AsciisDisplay

if __name__ == "__main__":
    from pynput import keyboard

    display = AsciisDisplay()
    game = TetrisGame(display)

    keymap = {
        "s": game.start,
        "S": game.start,
        "p": game.pause,
        "P": game.pause,
        "r": game.reset,
        "R": game.reset,
        keyboard.Key.left: game.move_left,
        keyboard.Key.right: game.move_right,
        keyboard.Key.up: game.rotate_right,
        keyboard.Key.down: game.rotate_left,
        keyboard.Key.shift: game.drop,
        keyboard.Key.shift_r: game.drop,
    }

    def on_press(key):
        try:
            identifier = key.char
        except AttributeError:
            identifier = key

        action = keymap.get(identifier)
        if action is not None:
            action()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
