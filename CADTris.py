import logging
from uuid import uuid4
import traceback
from pathlib import Path
from queue import Queue

import adsk.core, adsk.fusion
from .CADTris.fusion_addin_framework import fusion_addin_framework as faf

from .CADTris.logic_model import TetrisGame
from .CADTris.ui import InputIds, CommandWindow, FusionDisplay


# settings / constants #########################################################
LOGGING_ENABLED = True
RESOURCE_FOLDER = (
    Path(__file__).parent
    / "CADTris"
    / "fusion_addin_framework"
    / "fusion_addin_framework"
    / "default_images"
)
# RESOURCE_FOLDER = Path(__file__).parent / "resources"


# globals ######################################################################
addin = None
ao = faf.utils.AppObjects()
command = None
custom_event_id = None
command_window = None

# handlers #####################################################################
def on_created(event_args: adsk.core.CommandCreatedEventArgs):
    global command
    command = event_args.command

    ao.design.designType = adsk.fusion.DesignTypes.DirectDesignType

    global command_window
    command_window = CommandWindow(command, RESOURCE_FOLDER)

    display = FusionDisplay(faf.utils.new_component("CADTris"), 10)
    game = TetrisGame(display, 15, 7)


def on_input_changed(event_args: adsk.core.InputChangedEventArgs):
    # do NOT use: inputs = event_args.inputs
    # (will only contain inputs of the same input group as the changed input)
    # use instead:
    inputs = event_args.firingEvent.sender.commandInputs
    pass
    # if event_args.input.id == InputIds.Button1.value:
    #     # no effect at all
    #     # vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="input changed")
    #     execution_queue.put(
    #         lambda: vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="input changed")
    #     )
    #     adsk.core.Command.cast(event_args.firingEvent.sender).doExecute(False)


def on_execute(event_args: adsk.core.CommandEventArgs):
    pass


def on_destroy(event_args: adsk.core.CommandEventArgs):
    pass


### entry point ################################################################
def run(context):  # pylint:disable=unused-argument
    try:
        ui = ao.userInterface

        if LOGGING_ENABLED:
            faf.utils.create_logger(
                faf.__name__,
                [logging.StreamHandler(), faf.utils.TextPaletteLoggingHandler()],
            )

        global addin
        addin = faf.FusionAddin()
        workspace = faf.Workspace(addin, id="FusionSolidEnvironment")
        tab = faf.Tab(workspace, id="ToolsTab")
        panel = faf.Panel(tab, id="SolidScriptsAddinsPanel")
        control = faf.Control(panel)

        global custom_event_id
        custom_event_id = str(uuid4())
        faf.AddinCommand(
            control,
            resourceFolder="lightbulb",
            name="CADTris",
            commandCreated=on_created,
            inputChanged=on_input_changed,
            execute=on_execute,
            destroy=on_destroy,
            # customEventHandlers={custom_event_id: on_custom_event},
        )

    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)


def stop(context):  # pylint:disable=unused-argument
    try:
        ui = ao.userInterface
        addin.stop()
    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)
