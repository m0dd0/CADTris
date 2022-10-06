from queue import Queue
import threading
import functools
from typing import Callable
import logging

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

        self.execution_queue = Queue()
        self._fusion_command: adsk.core.Command = None
        self.last_handler = None

    def _executer(self, to_execute: Callable, type_of_change: str):
        """Utility function which can be used to execute arbitrary FusionAPI calls by automatically
        determining the correct way of executing them. Either via the CustomCommand-doExecute mechanism
        or directly depending on the thread and on the currently active hanler.

        Args:
            to_execute (Callable): The function to execute. Must not accept any arguments.
        """
        # actions from the event must be executed via customEvent(doExecute) (as described in docs)
        # actions from inputChanged handler must be executed via customEvent (otherwise bodies wont get created)
        # actions from commandCreated handler should be executed directly (they might work also with customEvent but not reliable)
        # actions from destroy handler must be executed directly since the command gets already destroyed
        if threading.current_thread() == threading.main_thread():
            if self.last_handler in ("commandCreated", "destroy") or (
                self.last_handler == "inputChanged" and type_of_change == "inputs"
            ):
                method = "direct"
            else:
                method = "custom_event_doExecute"

        if (
            threading.current_thread() != threading.main_thread()
            and method != "custom_event_doExecute"
        ):
            logging.getLogger(__name__).warning(
                "Using not the custom event / doExecute mechanism will most likely lead to undesired behaviour or crashes Fusion."
            )

        if method == "direct":
            to_execute()
        elif method == "custom_event_doExecute":
            self.execution_queue.put(to_execute)
            # FireCustomEvent returns immediately and therefore the lock for actions is removed.
            # The customevent (and the contained doExecute call) is scheduled and might not get immideately executed.
            # Therefore this function might get called (from the periodic thread) again when the execute
            # event is still executed.
            # However, this is not a problem since we can simply put the next ipdate action in the queue.
            adsk.core.Application.get().fireCustomEvent(config.CADTRIS_CUSTOM_EVENT_ID)
        elif method == "custom_event":
            raise NotImplementedError(f"'{method}' is not implemented yet.")
        elif method == "doExecute":
            raise NotImplementedError(f"'{method}' is not implemented yet.")
        elif method == "doExecutePreview":
            raise NotImplementedError(f"'{method}' is not implemented yet.")
        else:
            raise ValueError(f"'{method}' is not a supperoted method for execution.")

    def _track_last_handler(meth: Callable):  # pylint:disable=no-self-argument
        """Method decorator which sets the self.last_handler property to the name of the decorated method."""

        @functools.wraps(meth)
        def wrapper(self: "CADTrisCommand", *args, **kwargs):
            self.last_handler = meth.__name__
            return meth(self, *args, **kwargs)

        return wrapper

    @_track_last_handler
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

        # fusion_command must be saved as attribute otherwise it will get evaluated at call time
        # when the eventArgs.command value might have changed or become invalid.
        faf.utils.create_custom_event(
            config.CADTRIS_CUSTOM_EVENT_ID,
            lambda _: self._fusion_command.doExecute(False),
        )

        comp = faf.utils.new_component(config.CADTRIS_COMPONENT_NAME)
        design.rootComponent.allOccurrencesByComponent(comp).item(0).activate()
        command_window = InputsWindow(eventArgs.command)
        self.display = FusionDisplay(command_window, comp, self._executer)

        self.game = TetrisGame(self.display)

    @_track_last_handler
    def inputChanged(self, eventArgs: adsk.core.InputChangedEventArgs):
        # do NOT use: inputs = event_args.inputs (will only contain inputs of the same input group as the changed input)
        # use instead: inputs = event_args.firingEvent.sender.commandInputs
        logging.getLogger(__name__).info(f"Changed input id: {eventArgs.input.id}")
        if eventArgs.input.id == InputIds.PlayButton.value:
            self.game.start()
        elif eventArgs.input.id == InputIds.PauseButton.value:
            self.game.pause()
        elif eventArgs.input.id == InputIds.RedoButton.value:
            self.game.reset()
        elif eventArgs.input.id == InputIds.BlockHeight.value:
            self.game.set_height(eventArgs.input.valueOne)
        elif eventArgs.input.id == InputIds.BlockWidth.value:
            self.game.set_width(eventArgs.input.valueOne)
        elif eventArgs.input.id == InputIds.BlockSize.value:
            self.display.set_grid_size(eventArgs.input.value)
        elif eventArgs.input.id == InputIds.KeepBodies.value:
            pass  # we do not need to do anythong, the input is checked in the destroy handler

    def execute(
        self, eventArgs: adsk.core.CommandEventArgs  # pylint:disable=unused-argument
    ):
        c = 0
        while not self.execution_queue.empty():
            self.execution_queue.get()()
            c += 1
        logging.getLogger(__name__).debug(f"Executed {c} actions.")

    @_track_last_handler
    def destroy(
        self, eventArgs: adsk.core.CommandEventArgs  # pylint:disable=unused-argument
    ):
        # at first game must be terminated to avoid further thread calls while display is cleared
        self.game.terminate()

        if not eventArgs.command.commandInputs.itemById(
            InputIds.KeepBodies.value
        ).value:
            self.display.clear_world()

        self.execution_queue = Queue()

    @_track_last_handler
    def keyDown(self, eventArgs: adsk.core.KeyboardEventArgs):
        logging.getLogger(__name__).info(f"Pressed key {eventArgs.keyCode}.")
        {
            adsk.core.KeyCodes.UpKeyCode: self.game.rotate_right,
            adsk.core.KeyCodes.LeftKeyCode: self.game.move_left,
            adsk.core.KeyCodes.RightKeyCode: self.game.move_right,
            adsk.core.KeyCodes.DownKeyCode: self.game.rotate_left,
            adsk.core.KeyCodes.ShiftKeyCode: self.game.drop,
        }.get(eventArgs.keyCode, lambda: None)()
