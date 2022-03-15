import logging
import traceback

# pylint:disable=no-name-in-module
# pylint:disable=no-member
import adsk.core, adsk.fusion
from .CADTris.fusion_addin_framework import fusion_addin_framework as faf

from .CADTris.logic_model import TetrisGame
from .CADTris.ui import InputsWindow, FusionDisplay, InputIds
from .CADTris import config


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
            config.RESOURCE_FOLDER,
            TetrisGame.max_level,
            TetrisGame.height_range,
            config.GAME_INITIAL_HEIGHT,
            TetrisGame.width_range,
            config.GAME_INITIAL_WIDTH,
            config.VOXEL_INITIAL_GRID_SIZE,
        )

        self.display = FusionDisplay(
            self,
            command_window,
            faf.utils.new_component("CADTris"),
            config.GAME_INITIAL_WIDTH,
        )
        self.game = TetrisGame(
            self.display, config.GAME_INITIAL_HEIGHT, config.GAME_INITIAL_WIDTH
        )

    def inputChanged(self, eventArgs: adsk.core.InputChangedEventArgs):
        # do NOT use: inputs = event_args.inputs
        # (will only contain inputs of the same input group as the changed input)
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
        pass

    def destroy(self, eventArgs: adsk.core.CommandEventArgs):
        pass

    def keyDown(self, eventArgs: adsk.core.KeyboardEventArgs):
        {
            adsk.core.KeyCodes.UpKeyCode: self.game.rotate_right,
            adsk.core.KeyCodes.LeftKeyCode: self.game.move_left,
            adsk.core.KeyCodes.RightKeyCode: self.game.move_right,
            adsk.core.KeyCodes.DownKeyCode: self.game.rotate_left,
            adsk.core.KeyCodes.ShiftKeyCode: self.game.drop,
        }.get(eventArgs.keyCode, lambda: None)()


### entry point ################################################################
def run(context):  # pylint:disable=unused-argument
    try:
        ui = faf.utils.AppObjects().userInterface

        if config.LOGGING_ENABLED:
            faf.utils.create_logger(
                faf.__name__,
                [logging.StreamHandler(), faf.utils.TextPaletteLoggingHandler()],
            )

        addin = faf.FusionAddin()
        workspace = faf.Workspace(addin, id="FusionSolidEnvironment")
        tab = faf.Tab(workspace, id="ToolsTab")
        panel = faf.Panel(tab, id="SolidScriptsAddinsPanel")
        control = faf.Control(panel)
        command = faf.AddinCommand(
            control,
            resourceFolder="lightbulb",
            name="CADTris",
        )

    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)


def stop(context):  # pylint:disable=unused-argument
    try:
        ui = faf.utils.AppObjects().userInterface
        faf.stop()
    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)
