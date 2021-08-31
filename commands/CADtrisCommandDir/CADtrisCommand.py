# pylint: disable = unused-import
# pylint: disable = unused-argument

from typing import Dict, Any
from enum import auto
import os
from collections import namedtuple
import traceback
import json

import adsk.core
import adsk.fusion

from ...apper.apper import Fusion360CommandBase, HandlerState
from ...apper.utilities import (AppObjects, InputIdsBase, new_comp,
                                item_by_name, delete_comp,
                                remove_custom_appearances, get_json_from_file,
                                make_comp_invisible, with_time_printed)

from .GameLogic import Game, Screen

ao = AppObjects()
game = None
screen = None
made_invisible = ([], [])


class InputIds(InputIdsBase):
    SettingsGroup = auto()
    #Height = auto()
    BlockHeight = auto()
    #Width = auto()
    BlockWidth = auto()
    BlockSize = auto()
    KeepBodies = auto()
    GameInfoGroup = auto()
    Speed = auto()
    Score = auto()
    Lines = auto()
    ControlGroup = auto()
    Play = auto()
    Pause = auto()
    Reset = auto()
    HighscoreGroup = auto()


# Class for a Fusion 360 Command
# Place your program logic here
class CADtrisCommand(Fusion360CommandBase):
    """[summary]"""
    def on_create(self, args: adsk.core.CommandEventArgs,
                  command: adsk.core.Command, inputs: adsk.core.CommandInputs,
                  state: HandlerState):
        """ Executed when addin button is pressed."""

        # message box to turn of parametric design type
        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            dialog_result = ao.ui.messageBox(
                'WARNING: Due to performance isuues it is not recommended to' +
                'play CADtris with enabled timeline.\n\n' +
                'Do you want to disable the timeline?', 'Warning',
                adsk.core.MessageBoxButtonTypes.YesNoButtonType)
            if dialog_result == adsk.core.DialogResults.DialogYes:
                ao.design.designType = adsk.fusion.DesignTypes.DirectDesignType

        # register custom event
        self.register_custom_command_event(self.on_periodic_go_down)

        # configuring commadn dialog buttons
        command.isOKButtonVisible = False
        command.cancelButtonText = 'Exit'

        # adding help file
        command.helpFile = os.path.join(self.fusion_app.resources, 'help_file',
                                        'CADtris_help.pdf')

        # turn off visibility of all other bodies
        global made_invisible
        made_invisible = make_comp_invisible(ao.root_comp)

        # set initial values
        initial_height = 20
        initial_width = 10
        initial_grid = 5
        offset = namedtuple('Point3D', ['x', 'y', 'z'])(1.5, 0, 1.5)
        scores_to_show = 5

        # get path of json with achieved highscores
        scores_path = os.path.join(self.fusion_app.user_state_dir,
                                   'highscores.json')
        scores = get_json_from_file(scores_path, [])

        # initilaize global game and screen instance
        global screen, game
        screen = Screen(inputs, InputIds, scores, scores_to_show, offset,
                        initial_grid)
        game = Game(
            screen,
            lambda: self.fire_custom_command_event(self.on_periodic_go_down),
            initial_height, initial_width)

        # move camera to fit game
        screen.set_camera(game)

        ### controls input group
        controls_group = inputs.addGroupCommandInput(
            InputIds.ControlGroup.value, 'Controls')
        controls_group.children.addBoolValueInput(
            InputIds.Play.value, 'Play', True,
            os.path.join(self.fusion_app.resources, 'play_button'),
            False).tooltip = 'Start/Continue the game.'
        controls_group.children.addBoolValueInput(
            InputIds.Pause.value, 'Pause', True,
            os.path.join(self.fusion_app.resources, 'pause_button'),
            False).tooltip = 'Pause the game.'
        controls_group.children.addBoolValueInput(
            InputIds.Reset.value, 'Reset', True,
            os.path.join(self.fusion_app.resources, 'redo_button'),
            False).tooltip = 'Reset the game'

        ### game info group
        info_group = inputs.addGroupCommandInput(InputIds.GameInfoGroup.value,
                                                 'Info')
        speed_slider = info_group.children.addIntegerSliderListCommandInput(
            InputIds.Speed.value, 'Level', list(range(1, game.max_level + 1)),
            False)
        speed_slider.tooltip = 'Current level.'
        speed_slider.setText('1', '5')
        speed_slider.valueOne = game.level
        speed_slider.isEnabled = False
        score_text = info_group.children.addTextBoxCommandInput(
            InputIds.Score.value, 'Score', str(game.score), 1, True)
        score_text.isEnabled = False
        score_text.tooltip = 'Your current score.'
        cleared_lines_text = info_group.children.addTextBoxCommandInput(
            InputIds.Lines.value, 'Lines', str(game.line_count), 1, True)
        cleared_lines_text.isEnabled = False
        cleared_lines_text.tooltip = 'Number of line xou have cleared till now.'
        info_group.isVisible = False

        ### highscore input group
        highscore_group = inputs.addGroupCommandInput(
            InputIds.HighscoreGroup.value, 'Highscores (Top 5)')
        screen.write_scores()
        highscore_group.isExpanded = False

        ### settings input group
        setting_group = inputs.addGroupCommandInput(
            InputIds.SettingsGroup.value, 'Settings')
        # height inputs
        # height_distance = setting_group.children.addDistanceValueCommandInput(
        #     InputIds.Height.value, 'Height',
        #     adsk.core.ValueInput.createByReal(
        #         (initial_height + 1) * initial_grid))
        # height_distance.setManipulator(
        #     adsk.core.Point3D.create((offset.x - 1.5) * initial_grid,
        #                              (offset.y - 0.5) * initial_grid,
        #                              (offset.z - 1.5) * initial_grid),
        #     adsk.core.Vector3D.create(0, 0, 1))
        # height_distance.minimumValue = initial_grid * game.minimum_height
        # height_distance.maximumValue = initial_grid * game.maximum_height
        setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockHeight.value, 'Height (blocks)', game.minimum_height,
            game.maximum_height, 1,
            initial_height).tooltip = 'Height of the frame in blocks.'
        # width inputs
        # width_distance = setting_group.children.addDistanceValueCommandInput(
        #     InputIds.Width.value, 'Width',
        #     adsk.core.ValueInput.createByReal(
        #         (initial_width + 2) * initial_grid))
        # width_distance.setManipulator(
        #     adsk.core.Point3D.create((offset.x - 1.5) * initial_grid,
        #                              (offset.y - 0.5) * initial_grid,
        #                              (offset.z - 1.5) * initial_grid),
        #     adsk.core.Vector3D.create(1, 0, 0))
        # width_distance.minimumValue = initial_grid * game.minimum_width
        # width_distance.maximumValue = initial_grid * game.maximum_width
        setting_group.children.addIntegerSpinnerCommandInput(
            InputIds.BlockWidth.value, 'Width (blocks)', game.minimum_width,
            game.maximum_width, 1,
            initial_width).tooltip = 'Width of the frame in blocks.'
        # block size input
        setting_group.children.addValueInput(
            InputIds.BlockSize.value, 'Block size', 'mm',
            adsk.core.ValueInput.createByReal(
                initial_grid)).tooltip = 'Side length of single block in mm.'
        # keep bodies input
        setting_group.children.addBoolValueInput(
            InputIds.KeepBodies.value, 'Keep blocks', True, '', False
        ).tooltip = 'Flag determining if the blocks should be kept after closing the gae command.'
        setting_group.isExpanded = False

        # draw the frame and field
        # the command isnt created yet so cmd.doExecute() wont work
        while screen.todo:
            screen.todo.pop(0)()

    def on_preview(self, args: adsk.core.CommandEventArgs,
                   command: adsk.core.Command, inputs: adsk.core.CommandInputs,
                   input_values: Dict[str, Any], state: HandlerState):
        """ Executed when any inputs have changed, will updated the graphic"""
        pass

    def on_input_changed(self, args: adsk.core.InputChangedEventArgs,
                         command: adsk.core.Command,
                         inputs: adsk.core.CommandInputs,
                         input_values: Dict[str, Any],
                         changed_input: adsk.core.CommandInput,
                         state: HandlerState):
        """Executed when any inputs have changed."""

        if changed_input.id == InputIds.Play.value:
            game.start()
        elif changed_input.id == InputIds.Pause.value:
            game.pause()
        elif changed_input.id == InputIds.Reset.value:
            game.reset()

        # elif changed_input.id == InputIds.Height.value:
        #     block_size = input_values[InputIds.BlockSize.value]
        #     blocks_vertical = int(changed_input.value / block_size - 1)
        #     game.height = blocks_vertical
        #     changed_input.value = blocks_vertical * block_size
        #     inputs.itemById(InputIds.BlockHeight.value).value = blocks_vertical

        # elif changed_input.id == InputIds.Width.value:
        #     block_size = input_values[InputIds.BlockSize.value]
        #     blocks_horizontal = int(changed_input.value / block_size - 2)
        #     game.width = blocks_horizontal
        #     changed_input.value = blocks_horizontal * block_size
        #     inputs.itemById(
        #         InputIds.BlockWidth.value).value = blocks_horizontal

        elif changed_input.id == InputIds.BlockHeight.value:
            game.height = changed_input.value
            # inputs.itemById(InputIds.Height.value).value = input_values[
            #     InputIds.BlockSize.value] * (changed_input.value + 1)

        elif changed_input.id == InputIds.BlockWidth.value:
            game.width = changed_input.value
            # inputs.itemById(InputIds.Width.value).value = input_values[
            #     InputIds.BlockSize.value] * (changed_input.value + 2)

        elif changed_input.id == InputIds.BlockSize.value and changed_input.value > 0:
            block_size = changed_input.value
            screen.block_size = block_size
            screen.draw_field(game)
            screen.draw_frame(game)
            # height_input = inputs.itemById(InputIds.Height.value)
            # height_input.minimumValue = block_size * game.minimum_height
            # height_input.maximumValue = block_size * game.maximum_height
            # height_input.value = (game.height + 1) * block_size
            # height_input.setManipulator(
            #     adsk.core.Point3D.create((screen.offset.x - 1.5) * block_size,
            #                              (screen.offset.y - 0.5) * block_size,
            #                              (screen.offset.z - 1.5) * block_size),
            #     adsk.core.Vector3D.create(0, 0, 1))
            # width_input = inputs.itemById(InputIds.Width.value)
            # width_input.minimumValue = block_size * game.minimum_width
            # width_input.maximumValue = block_size * game.maximum_width
            # width_input.value = (game.width + 2) * block_size
            # width_input.setManipulator(
            #     adsk.core.Point3D.create((screen.offset.x - 1.5) * block_size,
            #                              (screen.offset.y - 0.5) * block_size,
            #                              (screen.offset.z - 1.5) * block_size),
            #     adsk.core.Vector3D.create(1, 0, 0))

        command.doExecute(False)

    def on_execute(self, args: adsk.core.CommandEventArgs,
                   command: adsk.core.Command, inputs: adsk.core.CommandInputs,
                   input_values: Dict[str, Any], state: HandlerState):
        """Will be executed when user selects OK in command dialog. """

        while screen.todo:
            screen.todo.pop(0)()

    def on_destroy(self, args: adsk.core.CommandEventArgs,
                   command: adsk.core.Command, inputs: adsk.core.CommandInputs,
                   input_values: Dict[str, Any],
                   reason: adsk.core.CommandTerminationReason,
                   state: HandlerState):
        """ Executed when the command is done."""
        global game, screen
        game.go_down_timer.kill()

        try:
            scores = screen.scores
        except:
            scores = None
        with open(
                os.path.join(self.fusion_app.user_state_dir,
                             'highscores.json'), 'w') as f:
            if scores is not None:  # prevent creating empty file
                json.dump(scores, f, indent=4)

        if not input_values[InputIds.KeepBodies.value]:
            delete_comp(screen.frame_comp)
            delete_comp(screen.field_comp)
            delete_comp(screen.cadtris_comp)
            remove_custom_appearances()
        else:
            if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
                start_index = ao.root_comp.allOccurrencesByComponent(
                    screen.cadtris_comp).item(0).timelineObject.index
                tl_group = ao.time_line.timelineGroups.add(
                    start_index, ao.time_line.markerPosition - 1)
                tl_group.name = 'CADtris'

        screen = None
        game = None

        for lightbulb_attr in made_invisible[0]:
            setattr(ao.root_comp, lightbulb_attr, True)
        for occ in made_invisible[1]:
            occ.isLightBulbOn = True

    @with_time_printed
    def on_key_down(self, args: adsk.core.CommandEventArgs,
                    command: adsk.core.Command,
                    inputs: adsk.core.CommandInputs, input_values: Dict[str,
                                                                        Any],
                    keycode: int, state: HandlerState):
        if game is None:
            return

        # check if the keys can be set as custom shortcuts, do not use them if so
        if keycode == adsk.core.KeyCodes.UpKeyCode:
            game.rotate()
        elif keycode == adsk.core.KeyCodes.LeftKeyCode:
            game.move_side(-1)
        elif keycode == adsk.core.KeyCodes.RightKeyCode:
            game.move_side(1)
        elif keycode == adsk.core.KeyCodes.DownKeyCode:
            game.move_down()
        elif keycode == adsk.core.KeyCodes.ShiftKeyCode:
            game.drop()

        command.doExecute(False)

    @with_time_printed
    def on_periodic_go_down(self, args, cmd, state):
        game.move_down()
        cmd.doExecute(False)