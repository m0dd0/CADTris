import adsk.core, adsk.fusion

from ...fusion_addin_framework import fusion_addin_framework as faf
from ... import addin_config
from . import config
from .logic_model import TetrisGame
from .ui import InputsWindow, InputIds, FusionDisplay


class CADTrisCommand(faf.AddinCommandBase):
    def __init__(
        self,
        parent=None,
        id="random",  # pylint:disable=redefined-builtin
        name="random",
        resourceFolder="lightbulb",
        tooltip="",
        toolClipFileName=None,
        isEnabled=True,
        isVisible=True,
        isChecked=True,
        listControlDisplayType=adsk.core.ListControlDisplayTypes.RadioButtonlistType,
    ):
        super().__init__(
            parent,
            id,
            name,
            resourceFolder,
            tooltip,
            toolClipFileName,
            isEnabled,
            isVisible,
            isChecked,
            listControlDisplayType,
        )

        self.game = None
        self.display = None
        self.ao = faf.utils.AppObjects()

    def commandCreated(self, eventArgs: adsk.core.CommandCreatedEventArgs):
        # TODO check and ask
        self.ao.design.designType = adsk.fusion.DesignTypes.DirectDesignType

        command_window = InputsWindow(
            eventArgs.command,
            addin_config.RESOURCE_FOLDER,
            TetrisGame.max_level,
            TetrisGame.height_range,
            config.GAME_INITIAL_HEIGHT,
            TetrisGame.width_range,
            config.GAME_INITIAL_WIDTH,
            config.VOXEL_INITIAL_GRID_SIZE,
        )

        self.display = FusionDisplay(
            command_window,
            faf.utils.new_component(config.GAME_COMPONENT_NAME),
            config.GAME_INITIAL_WIDTH,
        )

        faf.utils.execute_as_event(lambda: eventArgs.command.doExecute(False))

    def inputChanged(self, eventArgs: adsk.core.InputChangedEventArgs):
        # do NOT use: inputs = event_args.inputs (will only contain inputs of the same input group as the changed input)
        # use instead: inputs = event_args.firingEvent.sender.commandInputs

        if eventArgs.input.id == InputIds.PlayButton.value:
            self.game.start()
        elif eventArgs.input.id == InputIds.PauseButton.value:
            self.game.pause()
        elif eventArgs.input.id == InputIds.RedoButton.value:
            self.game.reset()
        # elif eventArgs.input.id == InputIds.BlockHeight.value:
        #     self.display.

        # BlockWidth = auto()
        # BlockSize = auto()
        # KeepBodies = auto()

    def execute(self, eventArgs: adsk.core.CommandEventArgs):
        self.game = TetrisGame(
            self.display,
            config.GAME_INITIAL_HEIGHT,
            config.GAME_INITIAL_WIDTH,
        )

    def destroy(self, eventArgs: adsk.core.CommandEventArgs):
        pass

    def keyDown(self, eventArgs: adsk.core.KeyboardEventArgs):
        # {
        #     adsk.core.KeyCodes.UpKeyCode: self.game.rotate_right,
        #     adsk.core.KeyCodes.LeftKeyCode: self.game.move_left,
        #     adsk.core.KeyCodes.RightKeyCode: self.game.move_right,
        #     adsk.core.KeyCodes.DownKeyCode: self.game.rotate_left,
        #     adsk.core.KeyCodes.ShiftKeyCode: self.game.drop,
        # }.get(eventArgs.keyCode, lambda: None)()
        pass
