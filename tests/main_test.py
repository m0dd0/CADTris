from unittest.mock import Mock
import sys

sys.modules["adsk"] = Mock()
sys.modules["adsk.fusion"] = Mock()
sys.modules["adsk.core"] = Mock()

from CADTris.logic_model import TetrisGame
from CADTris.ui import AsciisDisplay


if __name__ == "__main__":
    from pynput import keyboard

    display = AsciisDisplay()
    game = TetrisGame(display, 15, 7)

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
