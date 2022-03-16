from enum import auto
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import adsk.core, adsk.fusion

from .fusion_addin_framework import fusion_addin_framework as faf
from .voxler import voxler as vox


class InputIds(faf.utils.InputIdsBase):
    ControlsGroup = auto()
    PlayButton = auto()
    PauseButton = auto()
    RedoButton = auto()
    GameInfoGroup = auto()
    SpeedSlider = auto()
    ScoreText = auto()
    LinesText = auto()
    HighscoreGroup = auto()
    SettingsGroup = auto()
    BlockHeight = auto()
    BlockWidth = auto()
    BlockSize = auto()
    KeepBodies = auto()


class InputsWindow:
    def __init__(
        self,
        command,
        resource_folder,
        max_level,
        height_range,
        initial_height,
        width_range,
        initial_width,
        initial_grid_size,
    ):
        self._command = command
        self._resource_folder = resource_folder

        self._max_level = max_level
        self._height_range = height_range
        self._width_range = width_range
        self._initial_height = initial_height
        self._initial_width = initial_width
        self._initial_grid_size = initial_grid_size

        self._create_controls_group()
        self._create_info_group()
        self._create_highscores_group()
        self._create_settings_group()

    def _create_controls_group(self):
        self.controls_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.ControlsGroup.value, "Controls"
        )

        self.play_button = self.controls_group.children.addBoolValueInput(
            InputIds.PlayButton.value,
            "Play",
            True,
            str(self._resource_folder / "play_button"),
            False,
        )
        self.play_button.tooltip = "Start/Continue the game."

        self.pause_button = self.controls_group.children.addBoolValueInput(
            InputIds.PauseButton.value,
            "Pause",
            True,
            str(self._resource_folder / "pause_button"),
            False,
        )
        self.pause_button.tooltip = "Pause the game."

        self.redo_button = self.controls_group.children.addBoolValueInput(
            InputIds.RedoButton.value,
            "Reset",
            True,
            str(self._resource_folder / "redo_button"),
            False,
        )
        self.redo_button.tooltip = "Reset the game"

    def _create_info_group(self):
        self.info_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.GameInfoGroup.value, "Info"
        )

        self.speed_slider = self.info_group.children.addIntegerSliderListCommandInput(
            InputIds.SpeedSlider.value,
            "Level",
            list(range(1, self._max_level + 1)),
            False,
        )
        self.speed_slider.tooltip = "Current level."
        self.speed_slider.setText("1", "5")
        self.speed_slider.valueOne = 1
        self.speed_slider.isEnabled = False

        self.score_text = self.info_group.children.addTextBoxCommandInput(
            InputIds.ScoreText.value, "Score", str(0), 1, True
        )
        self.score_text.isEnabled = False
        self.score_text.tooltip = "Your current score."
        self.cleared_lines_text = self.info_group.children.addTextBoxCommandInput(
            InputIds.LinesText.value, "Lines", str(0), 1, True
        )
        self.cleared_lines_text.isEnabled = False
        self.cleared_lines_text.tooltip = "Number of line you have cleared till now."
        self.info_group.isVisible = False

    def _create_highscores_group(self):
        self.highscore_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.HighscoreGroup.value, "Highscores (Top 5)"
        )
        self.highscore_group.isExpanded = False

    def _create_settings_group(self):
        self.setting_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.SettingsGroup.value, "Settings"
        )

        self.height_setting = self.setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockHeight.value,
            "Height (blocks)",
            self._height_range[0],
            self._height_range[1],
            1,
            self._initial_height,
        )
        self.height_setting.tooltip = "Height of the frame in blocks."

        self.width_setting = self.setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockWidth.value,
            "Width (blocks)",
            self._width_range[0],
            self._width_range[1],
            1,
            self._initial_width,
        )
        self.width_setting.tooltip = "Width of the frame in blocks."

        self.block_size_input = self.setting_group.children.addValueInput(
            InputIds.BlockSize.value,
            "Block size",
            "mm",
            adsk.core.ValueInput.createByReal(self._initial_grid_size),
        )
        self.block_size_input.tooltip = "Side length of single block in mm."

        self.keep_bodies_setting = self.setting_group.children.addBoolValueInput(
            InputIds.KeepBodies.value, "Keep blocks", True, "", False
        )
        self.keep_bodies_setting.tooltip = "Flag determining if the blocks should be kept after closing the gae command."

        self.setting_group.isExpanded = False

    def update_control_buttons(self, enabled_buttons):
        self.play_button.isEnabled = "start" in enabled_buttons
        self.pause_button.isEnabled = "pause" in enabled_buttons
        self.redo_button.isEnabled = "reset" in enabled_buttons

    def able_settings(self, enable: bool):
        self.height_setting.isEnabled = enable
        self.width_setting.isEnabled = enable
        self.block_size_input.isEnbaled = enable


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
        command_window: InputsWindow,
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
        self._command_window = command_window

        self._voxel_world = vox.VoxelWorld(grid_size, component, (1.5, 1.5, -0.5))

        self._tetronimo_colors = tetronimo_colors
        self._wall_color = wall_color
        self._appearance = appearance

        self._last_state = None

        super().__init__()

    def _convert_color_code(self, code: int) -> Tuple[int]:
        return self._tetronimo_colors[code % len(self._tetronimo_colors)]

    def _get_voxel_dict(self, serialized_game):
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
                "shape": "cube",
                "color": color,
                "appearance": self._appearance,
                "name": "CADTris voxel",
            }
            for coord, color in voxels.items()
        }

        return voxels

    @faf.utils.execute_as_event_deco()
    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """

        if serialized_game["state"] != self._last_state:
            self._command_window.update_control_buttons(
                serialized_game["allowed_actions"]
            )
            self._command_window.able_settings(serialized_game["state"] == "start")
        self._last_state = serialized_game["state"]

        voxels = self._get_voxel_dict(serialized_game)
        self._voxel_world.update(voxels)

    @property
    def grid_size(self):
        return self._voxel_world.grid_size

    # @grid_size.setter
    # def grid_size(self):
    #     self._voxel_world.grid_size =
