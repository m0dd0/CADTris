import traceback
import logging
import os
from datetime import datetime

import adsk.core

app = adsk.core.Application.cast(adsk.core.Application.get())
ui = app.userInterface

try:
    from .apper.utilities import create_default_logger
    from .apper.apper import FusionApp
    from .apper.apper.UiElements import Workspace, Toolbar, Tab, Panel  # pylint: disable = unused-import
    from .apper.apper.UiElements import Dropdown, CommandControl, SplitButtonControl  # pylint: disable = unused-import
    from .apper.apper.UiElements import ButtonDefinition, CheckBoxDefinition, ListDefinition  # pylint: disable = unused-import
    from .apper.apper.Enums import Workspaces, Toolbars, Tabs, Panels  # pylint: disable = unused-import

    from .commands.CADtrisCommandDir import CADtrisCommand  # cookiecutter CADtrisCommand (+ Dir)

    logfile = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'logs',
        datetime.now().strftime(
            '%Y-%m-%d_%H-%M-%S_CADtris_log.txt'))  # cookiecutter CADtris
    logger = create_default_logger(
        name='CADtris_logger',  # cookiecutter CADtris
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(logfile)],
        level=logging.ERROR)

    cadtris_addin = FusionApp(  # cookiecutter cadtris
        name='CADtrisAddin',  # cookiecutter CADtris
        debug_to_ui=True,
        logger=logger,
    )

    cadtris_addin.add_command(  # cookiecutter cadtris
        command_class=CADtrisCommand,  # cookiecutter CADtris
        positions=[[
            Workspace(),
            Tab(),
            Panel('Fun'),  # cookiecutter Addins
            CommandControl(),
            ButtonDefinition(
                'CADtris',  # cookiecutter CADtris
                # cookiecutter remove resources and tooltip
                resources=os.path.join(cadtris_addin.resources, 'icon'),
                tooltip='Have fun with playing CADtris!')
        ]])

except:
    app = adsk.core.Application.get()
    ui = app.userInterface
    message = 'Initialization Failed: {0}'.format(traceback.format_exc())
    logger.error(message)
    if ui:
        ui.messageBox(message)


def run(context):  # pylint: disable = unused-argument
    """[summary]

    Args:
        context ([type]): [description]
    """
    cadtris_addin.run_app()  # cookiecutter cadtris


def stop(context):  # pylint: disable = unused-argument
    """[summary]

    Args:
        context ([type]): [description]
    """
    cadtris_addin.stop_app()  # cookiecutter cadtris
