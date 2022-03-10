from enum import auto
from abc import ABC, abstractmethod
from typing import Dict

import adsk.core, adsk.fusion

from .fusion_addin_framework import fusion_addin_framework as faf


class InputIds(faf.utils.InputIdsBase):
    Group1 = auto()
    Button1 = auto()


class CommandWindow:
    def __init__(self, command, resource_folder):
        self._command = command
        self._resource_folder = resource_folder

        self._create_group_1()

    def _create_group_1(self):
        self.controls_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.Group1.value, "Group1"
        )

        self.button_1 = self.controls_group.children.addBoolValueInput(
            InputIds.Button1.value,
            "Button 1",
            True,
            str(self._resource_folder / "lightbulb"),
            False,
        )


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


class TetrisDisplay(Display, ABC):
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

        elements = {
            # field tetronimo
            **{c: self.element_char for c in serialized_game["field"].keys()},
            # active tetronimo
            **(
                {c: self.element_char for c in serialized_game["figure"]["coordinates"]}
                if serialized_game["figure"]
                else {}
            ),
            # sides
            **{
                (x, y): self.wall_char
                for x in (-1, serialized_game["width"])
                for y in range(-1, serialized_game["height"])
            },
            # bottom
            **{(x, -1): self.wall_char for x in range(-1, serialized_game["width"])},
        }

        xs, ys = list(zip(*elements.keys()))
        for y in range(max(ys), min(ys) - 1, -1):
            for x in range(min(xs), max(xs) + 1):
                c = elements.get((x, y), self.air_char)
                output += c
            output += "\n"

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
