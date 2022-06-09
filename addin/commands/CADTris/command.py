from queue import Queue

import adsk.core, adsk.fusion  # pylint:disable=import-error

from ...libs.fusion_addin_framework import fusion_addin_framework as faf
from ... import config
from .logic_model import TetrisGame
from .ui import InputsWindow, InputIds, FusionDisplay


class CADTrisCommand(faf.AddinCommandBase):
    def __init__(self, addin: faf.FusionAddin):

        workspace = faf.Workspace(addin, id=config.CADTRIS_WORKSPACE)
        tab = faf.Tab(workspace, id=config.CADTRIS_TAB)
        panel = faf.Panel(tab, id=config.CADTRIS_PANEL)
        control = faf.Control(panel)

        super().__init__(
            control,
            name=config.CADTRIS_COMMAND_NAME,
            resourceFolder=config.RESOURCE_FOLDER / "logo",
            tooltip=config.CADTRIS_TOOLTIP,
        )

        self.game = None
        self.display = None
        self.command_window = None

        self.execution_queue = Queue()

        self.ao = faf.utils.AppObjects()

    def commandCreated(self, eventArgs: adsk.core.CommandCreatedEventArgs):
        # TODO check and ask
        self.ao.design.designType = adsk.fusion.DesignTypes.DirectDesignType

        eventArgs.command.isOKButtonVisible = False

        self.command_window = InputsWindow(eventArgs.command)

        # TODO adjust camera view

        self.display = FusionDisplay(
            self.command_window,
            faf.utils.new_component(config.CADTRIS_COMPONENT_NAME),
            eventArgs.command,
            self.execution_queue,
        )
        self.game = TetrisGame(self.display)

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
        while not self.execution_queue.empty():
            self.execution_queue.get()()

    def destroy(self, eventArgs: adsk.core.CommandEventArgs):
        self.game.reset()
        self.execution_queue = Queue()

    def keyDown(self, eventArgs: adsk.core.KeyboardEventArgs):
        {
            adsk.core.KeyCodes.UpKeyCode: self.game.rotate_right,
            adsk.core.KeyCodes.LeftKeyCode: self.game.move_left,
            adsk.core.KeyCodes.RightKeyCode: self.game.move_right,
            adsk.core.KeyCodes.DownKeyCode: self.game.rotate_left,
            adsk.core.KeyCodes.ShiftKeyCode: self.game.drop,
        }.get(eventArgs.keyCode, lambda: None)()
