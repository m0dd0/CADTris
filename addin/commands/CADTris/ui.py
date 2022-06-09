from enum import auto
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict, Tuple

import adsk.core, adsk.fusion  # pylint:disable=import-error

from ...libs.fusion_addin_framework import fusion_addin_framework as faf
from ...libs.voxler import voxler as vox

from ... import config


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
    def __init__(self, command):
        self._command = command

        # TODO (maybe) put texts like tooltips in config
        # TODO investigate changing alignment of button when settings group gets expanded

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
            str(config.RESOURCE_FOLDER / "play_button"),
            False,
        )
        self.play_button.tooltip = "Start/Continue the game."

        self.pause_button = self.controls_group.children.addBoolValueInput(
            InputIds.PauseButton.value,
            "Pause",
            True,
            str(config.RESOURCE_FOLDER / "pause_button"),
            False,
        )
        self.pause_button.tooltip = "Pause the game."

        self.redo_button = self.controls_group.children.addBoolValueInput(
            InputIds.RedoButton.value,
            "Reset",
            True,
            str(config.RESOURCE_FOLDER / "redo_button"),
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
            list(range(1, config.CADTRIS_MAX_LEVEL + 1)),
            False,
        )
        self.speed_slider.tooltip = "Current level."
        self.speed_slider.setText("1", str(config.CADTRIS_MAX_LEVEL))
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
            config.CADTRIS_MIN_HEIGHT,
            config.CADTRIS_MAX_HEIGHT,
            1,
            config.CADTRIS_INITIAL_HEIGHT,
        )
        self.height_setting.tooltip = "Height of the frame in blocks."

        self.width_setting = self.setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockWidth.value,
            "Width (blocks)",
            config.CADTRIS_MIN_WIDTH,
            config.CADTRIS_MAX_WIDTH,
            1,
            config.CADTRIS_INITIAL_WIDTH,
        )
        self.width_setting.tooltip = "Width of the frame in blocks."

        self.block_size_input = self.setting_group.children.addValueInput(
            InputIds.BlockSize.value,
            "Block size",
            "mm",
            adsk.core.ValueInput.createByReal(config.CADTRIS_INITIAL_VOXEL_SIZE),
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
        fusion_command: adsk.core.Command,
        execution_queue: Queue,
    ) -> None:
        self._command_window = command_window

        self._voxel_world = vox.VoxelWorld(
            config.CADTRIS_INITIAL_VOXEL_SIZE, component, (1.5, 1.5, -0.5)
        )

        self._last_state = None

        self._fusion_command = fusion_command
        self._execution_queue = execution_queue
        self._initial_update_called = False

        super().__init__()

    def _convert_color_code(self, code: int) -> Tuple[int]:
        return config.CADTRIS_TETRONIMO_COLORS[
            code % len(config.CADTRIS_TETRONIMO_COLORS)
        ]

    def _get_voxel_dict(self, serialized_game):
        field_voxels = {
            coord: self._convert_color_code(color_code)
            for coord, color_code in serialized_game["field"].items()
        }

        figure_voxels = dict()
        if serialized_game["figure"]:
            figure_voxels = {
                coord: self._convert_color_code(serialized_game["figure"]["color_code"])
                for coord in serialized_game["figure"]["coordinates"]
            }

        wall_voxels = {
            **{
                (x, y): config.CADTRIS_WALL_COLOR
                for x in (-1, serialized_game["width"])
                for y in range(-1, serialized_game["height"])
            },
            **{
                (x, -1): config.CADTRIS_WALL_COLOR
                for x in range(-1, serialized_game["width"])
            },
        }

        # {(x_game,y_game):(r,b,g,o)}
        voxels = {**field_voxels, **figure_voxels, **wall_voxels}
        print(voxels)
        voxels = {
            (*coord, 0): {
                "shape": "cube",
                "color": color,
                "appearance": config.CADTRIS_BLOCK_APPEARANCE,
                "name": "CADTris voxel",
            }
            for coord, color in voxels.items()
        }

        return voxels

    def _update(self, serialized_game: Dict) -> None:
        if serialized_game["state"] != self._last_state:
            self._command_window.update_control_buttons(
                serialized_game["allowed_actions"]
            )
            self._command_window.able_settings(serialized_game["state"] == "start")
        self._last_state = serialized_game["state"]

        voxels = self._get_voxel_dict(serialized_game)
        self._voxel_world.update(voxels)

    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state.

        Args:
            serialized_game (Dict): A full representation of the game which allows to visualize
                the game but prevents changign the game.
        """
        # this methods gets called in three different ways:
        # 1) when we initially want to build the game from the commadcreated event handler
        # 2) from the thread event that ultimately leads to an update of the display
        # 3) from the input changed handler which also modfies the game and therfore also the display
        # except from the first case we need to execute this function from the commandExecute handler
        # and the doExecute function must be called from a custom event.
        # (for more details see the GenericDynamicAddin minimal example)
        # for the first case we need to execute is directly as the command hasnt been created yet
        # therfore we need a command and queue object which we can access from here
        # to distinguish the two cases we need a flag which indicates this
        # as the commandcreated handler is always executed before everything else we simply set a flag
        # initially to False and then to True

        if self._initial_update_called:
            self._execution_queue.put(lambda: self._update(serialized_game))
            faf.utils.execute_as_event(
                lambda: self._fusion_command.doExecute(False),
                "cadtris_custom_event_id",
                True,
            )
        else:
            self._initial_update_called = True
            self._update(serialized_game)

    @property
    def grid_size(self):
        return self._voxel_world.grid_size

    # @grid_size.setter
    # def grid_size(self):
    #     self._voxel_world.grid_size =
