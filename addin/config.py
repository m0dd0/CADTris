from pathlib import Path

# general settings
LOGGING_ENABLED = True
RESOURCE_FOLDER = Path(__file__).parent / "resources"
CADTRIS_WORKSPACE = "FusionSolidEnvironment"
CADTRIS_TAB = "ToolsTab"
CADTRIS_PANEL = "SolidScriptsAddinsPanel"

# command related settings
CADTRIS_COMMAND_NAME = "CADtris"
CADTRIS_TOOLTIP = "Play CADtris!"

CADTRIS_GAME_INITIAL_HEIGHT = 15
CADTRIS_GAME_INITIAL_WIDTH = 7
CADTRIS_GAME_COMPONENT_NAME = "CADTris"

CADTRIS_VOXEL_INITIAL_GRID_SIZE = 10
