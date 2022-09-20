from queue import Queue
import functools

import adsk.core, adsk.fusion  # pylint:disable=import-error

from ...libs.fusion_addin_framework import fusion_addin_framework as faf
from ... import config
from .logic_model import TetrisGame
from .ui import InputsWindow, InputIds, FusionDisplay


def track_active_handler(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.active_handler = method.__name__
        result = method(self, *args, **kwargs)
        self.active_handler = None
        return result

    return wrapper


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

        self.execution_queue = Queue()
        self._fusion_command = None
        self.active_handler = None

    def execute_safely(self, action):
        assert self.active_handler != "execute"
        if self.active_handler is not None:
            action()
        else:
            self.execution_queue.put(action)
            # the custom event calls simply self._fusion_command.doExecute()
            adsk.core.Application.get().fireCustomEvent(config.CADTRIS_CUSTOM_EVENT_ID)

    @track_active_handler
    def commandCreated(self, eventArgs: adsk.core.CommandCreatedEventArgs):
        self._fusion_command = eventArgs.command

        # change design type to direct design type
        design = adsk.core.Application.get().activeDocument.design
        if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            dialog_result = adsk.core.Application.get().userInterface.messageBox(
                config.CADTRIS_DIRECT_DESIGN_QUESTION,
                config.CADTRIS_DIRECT_DESIGN_TITLE,
                adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            )
            if dialog_result == adsk.core.DialogResults.DialogYes:
                design.designType = adsk.fusion.DesignTypes.DirectDesignType
            else:
                return

        # hide ok button
        eventArgs.command.isOKButtonVisible = False

        faf.utils.create_custom_event(
            lambda: self._fusion_command.doExecute(False),
            event_id=config.CADTRIS_CUSTOM_EVENT_ID,
        )

        comp = faf.utils.new_component(config.CADTRIS_COMPONENT_NAME)
        design.rootComponent.allOccurrencesByComponent(comp).item(0).activate()
        command_window = InputsWindow(eventArgs.command)
        self.display = FusionDisplay(command_window, comp, self.execute_safely)

        self.game = TetrisGame(self.display)

    @track_active_handler
    def inputChanged(self, eventArgs: adsk.core.InputChangedEventArgs):
        # do NOT use: inputs = event_args.inputs (will only contain inputs of the same input group as the changed input)
        # use instead: inputs = event_args.firingEvent.sender.commandInputs
        if eventArgs.input.id == InputIds.PlayButton.value:
            self.game.start()
        elif eventArgs.input.id == InputIds.PauseButton.value:
            self.game.pause()
        elif eventArgs.input.id == InputIds.RedoButton.value:
            self.game.reset()
        elif eventArgs.input.id == InputIds.BlockHeight.value:
            self.game.set_height(eventArgs.input.value)
        elif eventArgs.input.id == InputIds.BlockWidth.value:
            self.game.set_width(eventArgs.input.value)
        elif eventArgs.input.id == InputIds.BlockSize.value:
            self.display.set_grid_size(eventArgs.input.value)
        elif eventArgs.input.id == InputIds.KeepBodies.value:
            pass  # we do not need to do anythong, the input is checked in the destroy handler

    @track_active_handler
    def execute(
        self, eventArgs: adsk.core.CommandEventArgs  # pylint:disable=unused-argument
    ):
        while not self.execution_queue.empty():
            self.execution_queue.get()()

    @track_active_handler
    def destroy(
        self, eventArgs: adsk.core.CommandEventArgs  # pylint:disable=unused-argument
    ):
        if not eventArgs.command.commandInputs.itemById(
            InputIds.KeepBodies.value
        ).value:
            self.display.clear_world()

        self.game.terminate()
        self.execution_queue = Queue()

    @track_active_handler
    def keyDown(self, eventArgs: adsk.core.KeyboardEventArgs):
        {
            adsk.core.KeyCodes.UpKeyCode: self.game.rotate_right,
            adsk.core.KeyCodes.LeftKeyCode: self.game.move_left,
            adsk.core.KeyCodes.RightKeyCode: self.game.move_right,
            adsk.core.KeyCodes.DownKeyCode: self.game.rotate_left,
            adsk.core.KeyCodes.ShiftKeyCode: self.game.drop,
        }.get(eventArgs.keyCode, lambda: None)()
