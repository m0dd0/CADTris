# pylint:disable=logging-fstring-interpolation

import logging
import traceback
from pathlib import Path

from .addin.libs.fusion_addin_framework import fusion_addin_framework as faf
from .addin import config
from .addin.commands.CADTris import CADTrisCommand


def run(context):  # pylint:disable=unused-argument
    try:
        # setup logging
        if config.LOGGING_ENABLED:
            Path(config.LOGGING_FOLDER).mkdir(parents=True, exist_ok=True)
            faf.utils.create_logger(
                __name__,  # also applies to faf since its a submodule
                [
                    logging.StreamHandler(),
                    # faf.utils.TextPaletteLoggingHandler(),
                    logging.handlers.TimedRotatingFileHandler(
                        config.LOGGING_FOLDER / config.LOGFILE_BASENAME,
                        when=config.LOGGING_ROTATE_WHEN,
                        interval=config.LOGGING_ROTATE_INTERVAL,
                        backupCount=config.LOGGING_ROTATE_COUNT,
                    ),
                ],
            )
            logging.getLogger(__name__).info(f"Logging to {config.LOGGING_FOLDER}")

        # create the top level addin instance
        addin = faf.FusionAddin()

        # create the command
        CADTrisCommand(addin)

    except:  # pylint:disable=bare-except
        msg = "Failed:\n{}".format(traceback.format_exc())
        ui = faf.utils.AppObjects().userInterface
        if ui:
            ui.messageBox(msg)
        print(msg)


def stop(context):  # pylint:disable=unused-argument
    try:
        faf.stop()
    except:  # pylint:disable=bare-except
        msg = "Failed:\n{}".format(traceback.format_exc())
        ui = faf.utils.AppObjects().userInterface
        if ui:
            ui.messageBox(msg)
        print(msg)
