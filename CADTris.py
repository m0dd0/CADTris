import logging
from uuid import uuid4
import traceback
from pathlib import Path
import random
from queue import Queue

import adsk.core, adsk.fusion, adsk.cam

from .fusion_addin_framework import fusion_addin_framework as faf
from .voxler import voxler as vox
from .src.ui import InputIds, CommandWindow


# settings / constants #########################################################
LOGGING_ENABLED = True
RESOURCE_FOLDER = (
    Path(__file__).parent
    / "fusion_addin_framework"
    / "fusion_addin_framework"
    / "default_images"
)
# RESOURCE_FOLDER = Path(__file__).parent / "resources"


# globals ######################################################################
addin = None
ao = faf.utils.AppObjects()
command = None  # needed for custom event handlers see def on_custom_event()
custom_event_id = None  # see notes on def on_custom_event()
periodic_thread = None  # started in creaed handler and stoppen on destroy
execution_queue = Queue()

# handlers #####################################################################
def thread_execute():
    # to get fusion work done from an thread you normally fire a custom event:
    # ao.app.fireCustomEvent(custom_event_id)

    # sometimes you want the action in the thread to be determined by the thread
    # itself (otherwise you would have to create a custom event for every action)
    # this can be achieved by using a (second) execution_query for the custom event:
    # custom_event_execution_queue.put(action)
    # ao.app.fireCustomEvent(custom_event_id)
    # (custom event handler looks same as execute handler in this case)

    # however since this is quite similar to the command.doExecute(False) approach
    # it seems logically to use the execute handler directly.
    # In this case only one excution_queue needs to be handled.
    # it seems like both verison are working fine
    execution_queue.put(
        lambda: vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="periodic execute")
    )
    # in this case replaces ao.app.fireCustomEvent(custom_event_id)
    # can be seen as ao.app.fireEvent('execute_id')
    command.doExecute(False)


def on_created(event_args: adsk.core.CommandCreatedEventArgs):
    global command
    command = event_args.command

    ao.design.designType = adsk.fusion.DesignTypes.DirectDesignType

    command_window = CommandWindow(command, RESOURCE_FOLDER)

    global periodic_thread
    periodic_thread = faf.utils.PeriodicExecuter(1, thread_execute)
    periodic_thread.start()

    # does not work because command hasnt been created yet
    # event_args.command.doExecute(False)
    # but creating bodies works in creaed handler (but not in the other handler except execute)
    vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="created")


def on_input_changed(event_args: adsk.core.InputChangedEventArgs):
    # !!! do NOT use this because of bug
    # (will only contain inputs of the same input group as the changed input)
    # inputs = event_args.inputs
    # use instead:
    # inputs = event_args.firingEvent.sender.commandInputs

    if event_args.input.id == InputIds.Button1.value:
        # no effect at all
        # vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="input changed")
        execution_queue.put(
            lambda: vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="input changed")
        )
        adsk.core.Command.cast(event_args.firingEvent.sender).doExecute(False)


def on_preview(event_args: adsk.core.CommandEventArgs):
    # everything in the preview is deleted before the next preview objects are build
    # object which were build in the preview handler are also not kept afer the execute handler
    # vox.DirectCube(
    #     ao.rootComponent, (0, 0, 0), 1, name=f"preview {random.randint(0,1000)}"
    # )
    # therfore it makes no sense to use the preview handler in case of an "dynamic" addin
    # instead use the queue/doExecute technique directly from the input changed handler
    pass


def on_execute(event_args: adsk.core.CommandEventArgs):
    # in execute everything works as exspected
    # use adsk.core.Command.doExecute(terminate = False) to remain in the command
    while not execution_queue.empty():
        execution_queue.get()()


def on_destroy(event_args: adsk.core.CommandEventArgs):
    periodic_thread.kill()


def on_custom_event(event_args: adsk.core.CustomEventArgs):
    # does not work reliable
    # vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="execute")
    # use commadn.doExecute(False) workaround
    # but command cant be retrieved from args --> global instance necessary
    if command.isValid:
        execution_queue.put(
            lambda: vox.DirectCube(ao.rootComponent, (0, 0, 0), 1, name="custom")
        )
        command.doExecute(False)


### entry point ################################################################
def run(context):
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
        cmd = faf.AddinCommand(
            control,
            resourceFolder="lightbulb",
            name="CADTris",
            commandCreated=on_created,
            inputChanged=on_input_changed,
            executePreview=on_preview,
            execute=on_execute,
            destroy=on_destroy,
            customEventHandlers={custom_event_id: on_custom_event},
        )

    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)


def stop(context):
    try:
        ui = ao.userInterface
        addin.stop()
    except:
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)