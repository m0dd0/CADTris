from enum import auto
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import adsk.core, adsk.fusion

from .fusion_addin_framework import fusion_addin_framework as faf
from .voxler import voxler as vox


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
    pass


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


class FusionDisplay(TetrisDisplay):
    def __init__(
        self,
        component: adsk.fusion.Component,
        grid_size: float,
        tetronimo_colors: Tuple[Tuple[int]] = (
            (255, 0, 0, 255),
            (0, 255, 0, 255),
            (0, 0, 255, 255),
            (255, 255, 0, 255),
            (0, 255, 255, 255),
            (255, 0, 255, 255),
        ),
        wall_color: Tuple[int] = None,
        appearance: str = "Steel - Satin",
    ) -> None:
        self._voxel_world = vox.VoxelWorld(grid_size, component, (1.5, 1.5, -0.5))

        self._tetronimo_colors = tetronimo_colors
        self._wall_color = wall_color
        self._appearance = appearance

        super().__init__()

    def _convert_color_code(self, code: int) -> Tuple[int]:
        return self._tetronimo_colors[code % len(self._tetronimo_colors)]

    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """
        field_voxels = {
            coord: self._convert_color_code(color_code)
            for coord, color_code in serialized_game["field"].keys()
        }

        figure_voxels = dict()
        if serialized_game["figure"]:
            figure_voxels = {
                coord: self._convert_color_code(serialized_game["figure"]["color_code"])
                for coord in serialized_game["figure"]["coordinates"]
            }

        wall_voxels = {
            **{
                (x, y): self._wall_color
                for x in (-1, serialized_game["width"])
                for y in range(-1, serialized_game["height"])
            },
            **{(x, -1): self._wall_color for x in range(-1, serialized_game["width"])},
        }

        # {(x_game,y_game):(r,b,g,o)}
        voxels = {**field_voxels, **figure_voxels, **wall_voxels}
        voxels = {
            (*coord, 0): {
                "voxel_class": vox.DirectCube,
                "color": color,
                "appearance": self._appearance,
                "additional_properties": {"name": "CADTris voxel"},
            }
            for coord, color in voxels.items()
        }

        self._voxel_world.update(voxels)
