import logging
import traceback

from .CADTris.fusion_addin_framework import fusion_addin_framework as faf
from .CADTris import addin_config
from .CADTris.commands.CADTris import CADTrisCommand


def run(context):  # pylint:disable=unused-argument
    try:
        ui = faf.utils.AppObjects().userInterface

        if addin_config.LOGGING_ENABLED:
            faf.utils.create_logger(
                faf.__name__,
                [logging.StreamHandler(), faf.utils.TextPaletteLoggingHandler()],
            )

        addin = faf.FusionAddin()
        workspace = faf.Workspace(addin, id=addin_config.ADDIN_WORKSPACE)
        tab = faf.Tab(workspace, id=addin_config.ADDIN_TAB)
        panel = faf.Panel(tab, id=addin_config.ADDIN_PANEL)

        CADTrisCommand(panel)

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
