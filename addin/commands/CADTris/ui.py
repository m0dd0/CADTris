from enum import auto
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict, List, Tuple, Set
import bisect
import json

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
    HighscoreHeading = auto()
    SettingsGroup = auto()
    BlockHeight = auto()
    BlockWidth = auto()
    BlockSize = auto()
    KeepBodies = auto()


class InputsWindow:
    def __init__(self, command: adsk.core.Command):
        """Creates the input window in Fusion for the passed command. This includes all InputGroups and
        Input configuration. The inputs are saved as properties of this class.

        Args:
            command (adsk.core.Command): The command for which the inputs are createtd.
        """

        self._command = command

        # TODO (maybe) put texts like tooltips in config
        # TODO investigate changing alignment of button when settings group gets expanded

        self._create_controls_group()
        self._create_info_group()
        self._create_highscores_group()
        self._create_settings_group()

    def _create_controls_group(self):
        """Creates the control group for the Play, PAuse buttons etc. and the corresponding inputs."""
        self.controls_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.ControlsGroup.value, config.CADTRIS_CONTROL_GROUP_NAME
        )

        self.play_button = self.controls_group.children.addBoolValueInput(
            InputIds.PlayButton.value,
            config.CADTRIS_PLAY_BUTTON_NAME,
            True,
            str(config.RESOURCE_FOLDER / "play_button"),
            False,
        )
        self.play_button.tooltip = "Start/Continue the game."

        self.pause_button = self.controls_group.children.addBoolValueInput(
            InputIds.PauseButton.value,
            config.CADTRIS_PAUSE_BUTTON_NAME,
            True,
            str(config.RESOURCE_FOLDER / "pause_button"),
            False,
        )
        self.pause_button.tooltip = "Pause the game."

        self.redo_button = self.controls_group.children.addBoolValueInput(
            InputIds.RedoButton.value,
            config.CADTRIS_RESET_BUTTON_NAME,
            True,
            str(config.RESOURCE_FOLDER / "redo_button"),
            False,
        )
        self.redo_button.tooltip = "Reset the game"

    def _create_info_group(self):
        """Creates the control group for the level, speed and lines information-inputs."""
        self.info_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.GameInfoGroup.value, config.CADTRIS_INFO_GROUP_NAME
        )
        self.info_group.isExpanded = False

        self.speed_slider = self.info_group.children.addIntegerSliderListCommandInput(
            InputIds.SpeedSlider.value,
            config.CADTRIS_LEVEL_SLIDER_NAME,
            list(range(1, config.CADTRIS_MAX_LEVEL + 1)),
            False,
        )
        self.speed_slider.tooltip = config.CADTRIS_LEVEL_SLIDER_TOOLTIP
        self.speed_slider.setText("1", str(config.CADTRIS_MAX_LEVEL))
        self.speed_slider.valueOne = 1
        self.speed_slider.isEnabled = False

        self.score_text = self.info_group.children.addTextBoxCommandInput(
            InputIds.ScoreText.value, config.CADTRIS_SCORE_INPUT_NAME, str(0), 1, True
        )
        self.score_text.isEnabled = False
        self.score_text.tooltip = config.CADTRIS_SCORE_INPUT_TOOLTIP
        self.cleared_lines_text = self.info_group.children.addTextBoxCommandInput(
            InputIds.LinesText.value, config.CADTRIS_LINES_INPUT_NAME, str(0), 1, True
        )
        self.cleared_lines_text.isEnabled = False
        self.cleared_lines_text.tooltip = config.CADTRIS_LINES_INPUT_TOOLTIP

    def _create_highscores_group(self):
        """Creates the input group for the highscore to display."""
        self.highscore_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.HighscoreGroup.value, config.CADTRIS_SCORES_GROUP_NAME
        )
        self.highscore_texts = [
            self.highscore_group.children.addTextBoxCommandInput(
                InputIds.HighscoreHeading.value + str(rank),
                f"{rank + 1}.",
                config.CADTRIS_NO_SCORE_SYMBOL,
                1,
                True,
            )
            for rank in range(config.CADTRIS_DISPLAYED_SCORES)
        ]
        self.update_highscores(faf.utils.get_json_from_file(config.CADTRIS_SCORES_PATH))

        self.highscore_group.isExpanded = False

    def _create_settings_group(self):
        """Creates the input group for all setting related inputs like width, height, etc."""
        self.setting_group = self._command.commandInputs.addGroupCommandInput(
            InputIds.SettingsGroup.value, config.CADTRIS_SETTINGS_GROUP_NAME
        )

        self.height_setting = self.setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockHeight.value,
            config.CADTRIS_HEIGHT_INPUT_NAME,
            config.CADTRIS_MIN_HEIGHT,
            config.CADTRIS_MAX_HEIGHT,
            1,
            config.CADTRIS_INITIAL_HEIGHT,
        )
        self.height_setting.tooltip = config.CADTRIS_HEIGHT_INPUT_TOOLTIP

        self.width_setting = self.setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockWidth.value,
            config.CADTRIS_WIDTH_INPUT_NAME,
            config.CADTRIS_MIN_WIDTH,
            config.CADTRIS_MAX_WIDTH,
            1,
            config.CADTRIS_INITIAL_WIDTH,
        )
        self.width_setting.tooltip = config.CADTRIS_WIDTH_INPUT_TOOLTIP

        self.block_size_input = self.setting_group.children.addValueInput(
            InputIds.BlockSize.value,
            config.CADTRIS_BLOCKSIZE_INPUT_NAME,
            "mm",
            adsk.core.ValueInput.createByReal(config.CADTRIS_INITIAL_VOXEL_SIZE),
        )
        self.block_size_input.tooltip = config.CADTRIS_BLOCKSIZE_INPUT_NAME

        self.keep_bodies_setting = self.setting_group.children.addBoolValueInput(
            InputIds.KeepBodies.value, config.CADTRIS_KEEP_INPUT_NAME, True, "", False
        )
        self.keep_bodies_setting.tooltip = config.CADTRIS_KEEP_INPUT_TOOLTIP

        self.setting_group.isExpanded = False

    def update_control_buttons(self, enabled_buttons: Set[str]):
        """Sets the state of the Pause, Play, Reset buttons accordingly. Only buttons corresponding to the
        names in the enable_buttons parameter are enabeld. Additionally the button value is set to False
        to get the feel of a snappy button.

        Args:
            enabled_buttons (Set[str]): A iterable which determines which button are enabled. Possible
                values are {"start", "pause", "reset"}.
        """
        self.play_button.value = False
        self.pause_button.value = False
        self.redo_button.value = False

        self.play_button.isEnabled = "start" in enabled_buttons
        self.pause_button.isEnabled = "pause" in enabled_buttons
        self.redo_button.isEnabled = "reset" in enabled_buttons

    def able_settings(self, enable: bool):
        """Enables or disabler all inputs in the settings group.

        Args:
            enable (bool): Whether the inputs get enabled or disabled.
        """
        self.height_setting.isEnabled = enable
        self.width_setting.isEnabled = enable
        self.block_size_input.isEnabled = enable

    def update_highscores(self, scores: List[int]):
        """Updates the highscore text inputs accorfing to the values in the passed list.
        It is asumed that the values in the passed list are sorted. Only the first values in the list
        are used.

        Args:
            scores (List[int]): A ordered list containing the current scores.
        """
        for rank in range(config.CADTRIS_DISPLAYED_SCORES):
            if rank < len(scores):
                self.highscore_texts[rank].text = str(scores[rank])
            else:
                self.highscore_texts[rank].text = str(config.CADTRIS_NO_SCORE_SYMBOL)


class Display(ABC):
    def __init__(self) -> None:
        """Base class for all Fusion-Game-Displays. Abstraction to clean logic and ui of addins."""
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
        """Display to visualize theb Teris game. Used for debugging the logic without using any part of Fusion

        Args:
            wall_char (str, optional): The character used to display walls. Defaults to "X".
            element_char (str, optional): The character used to display any kind of tetronimos. Defaults to "O".
            air_char (str, optional): The character used to display empty blocks. Defaults to " ".
            horizontal_spacing (str, optional): The characters used to seperate the displayed character horizontally.
                Used to get less thin look. Defaults to "  ".
        """
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
        """Display abstraction to visualite the Tetris game within Fusion360. This takes care of biulding
        the BREPBodies, executing the command for building etc.

        Args:
            command_window (InputsWindow): The command input window which get updated by the display due to
                changes in game state etc.
            component (adsk.fusion.Component): The Fusion360 component into which the blocks are build.
            fusion_command (adsk.core.Command): The command which is executed with a queue from a custom
                event in order to build the blocks.
            execution_queue (Queue): The execution queue which gets cleaned in the execute event handler
                of the passed fusion_command.
        """
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
        """Converts the color code of the figure of the serialized game to a rgbv-tuple.

        Args:
            code (int): Color code of the voxel.

        Returns:
            Tuple[int]: rgbv tuple.
        """
        return config.CADTRIS_TETRONIMO_COLORS[
            code % len(config.CADTRIS_TETRONIMO_COLORS)
        ]

    def _get_voxel_dict(self, serialized_game: Dict) -> Dict:
        """Takes the needed information from the serialized game and transforms them into dictionary
        qith all voxel description which can get passed directly to the voxler-world instance.

        Args:
            serialized_game (Dict): The serialized game.

        Returns:
            Dict: The voxel description for the voxler. {(x_game,y_game):(r,b,g,o)}
        """
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

    def _update_scores(self, serialized_game: Dict) -> str:
        """Fetches the current highscores from the file and compares the current game score to it.
        Updates the highscore file. Updates the command inputs. Return the respective game over message.

        Args:
            serialized_game (Dict): The serialized game.

        Returns:
            str: The game over message to display depending on the result.
        """
        score = serialized_game["score"]
        scores = faf.utils.get_json_from_file(config.CADTRIS_SCORES_PATH, [])

        achieved_rank = len(scores) - bisect.bisect_right(scores[::-1], score)

        scores.insert(achieved_rank, serialized_game["score"])
        with open(config.CADTRIS_SCORES_PATH, "w", encoding="utf-8") as f:
            json.dump(scores[: config.CADTRIS_MAX_SAVED_SCOES], f, indent=4)

        msg = config.CADTRIS_GAME_OVER_MESSAGE
        if achieved_rank < config.CADTRIS_DISPLAYED_SCORES:
            self._command_window.update_highscores(scores)
            # msg += f"\n\nCongratulations, you made the {faf.utils.make_ordinal(achieved_rank+1)} place in the ranking!"
            msg += config.CADTRIS_HIGHSCORE_MESSAGE.format(
                faf.utils.make_ordinal(achieved_rank + 1)
            )

        return msg

    def _update(self, serialized_game: Dict) -> None:
        """Steps to execute in order to update the screen accordingly. This includes updating the inputs and
        updating the voxel world. Depending on the context this function must be executed from the
        execute event handler or directly which is decided in the update-method.

        Args:
            serialized_game (Dict): The serialized game.
        """
        game_over_msg = None

        # things/inputs we update only when the game state has changed
        if serialized_game["state"] != self._last_state:
            self._command_window.update_control_buttons(
                serialized_game["allowed_actions"]
            )
            self._command_window.able_settings(serialized_game["state"] == "start")

            if serialized_game["state"] == "gameover":
                game_over_msg = self._update_scores(serialized_game)

        self._last_state = serialized_game["state"]

        # things we update all the time
        self._command_window.cleared_lines_text.formattedText = str(
            serialized_game["lines"]
        )
        self._command_window.score_text.formattedText = str(serialized_game["score"])
        self._command_window.speed_slider.valueOne = serialized_game["level"]

        voxels = self._get_voxel_dict(serialized_game)

        self._voxel_world.update(voxels)

        if game_over_msg is not None:
            adsk.core.Application.get().userInterface.messageBox(game_over_msg)

    @faf.utils.execute_as_event_deco("cadtris_custom_event_id", False)
    def _update_from_event(self, serialized_game: Dict):
        """Helper method which simply puts the _update method into the execution queue and triggers
        the command to be executed. Due to the decorator this is executed from a custom event.

        Args:
            serialized_game (Dict): The serialized game.
        """
        # we must put the action into the queue from within the event otherwise we crash fusion
        # otherwise it might happen that a key press adds a action to the queue and before the command
        # has executed the scheduler also puts a action into the queue. Then both try to call the event
        # which crahses Fusion. This way we somehow get it working and the queue always only contains
        # one action
        self._execution_queue.put(lambda: self._update(serialized_game))
        self._fusion_command.doExecute(False)

    def update(self, serialized_game: Dict) -> None:
        """Updates the display to show the game in its current state. Also takes care on how this is
        executed from Fusion.

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
            self._update_from_event(serialized_game)
        else:
            self._initial_update_called = True
            self._update(serialized_game)

    @property
    def grid_size(self) -> float:
        """The grid size of the voxel world used to display the game."""
        return self._voxel_world.grid_size

    # @grid_size.setter
    # def grid_size(self):
    #     self._voxel_world.grid_size =
