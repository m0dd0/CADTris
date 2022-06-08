import logging
import traceback

from .addin.libs.fusion_addin_framework import fusion_addin_framework as faf
from .addin import config
from .addin.commands.CADTris import CADTrisCommand


def run(context):  # pylint:disable=unused-argument
    try:
        ui = faf.utils.AppObjects().userInterface

        if config.LOGGING_ENABLED:
            faf.utils.create_logger(
                faf.__name__,
                [logging.StreamHandler(), faf.utils.TextPaletteLoggingHandler()],
            )

        addin = faf.FusionAddin()
        workspace = faf.Workspace(addin, id=config.ADDIN_WORKSPACE)
        tab = faf.Tab(workspace, id=config.ADDIN_TAB)
        panel = faf.Panel(tab, id=config.ADDIN_PANEL)

        CADTrisCommand(panel)

    except:  # pylint:disable=bare-except
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)


def stop(context):  # pylint:disable=unused-argument
    try:
        ui = faf.utils.AppObjects().userInterface
        faf.stop()
    except:  # pylint:disable=bare-except
        msg = "Failed:\n{}".format(traceback.format_exc())
        if ui:
            ui.messageBox(msg)
        print(msg)
