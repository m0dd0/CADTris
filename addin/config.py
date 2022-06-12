from pathlib import Path
from .libs.appdirs import appdirs

# general settings
LOGGING_ENABLED = True
RESOURCE_FOLDER = Path(__file__).parent / "resources"
CADTRIS_WORKSPACE = "FusionSolidEnvironment"
CADTRIS_TAB = "ToolsTab"
CADTRIS_PANEL = "SolidScriptsAddinsPanel"

# command related settings
CADTRIS_COMMAND_NAME = "CADtris"
CADTRIS_TOOLTIP = "Play CADtris!"

CADTRIS_COMPONENT_NAME = "CADTris"
# input related strings are krpt in the ui file for now

CADTRIS_INITIAL_VOXEL_SIZE = 10

CADTRIS_INITIAL_WIDTH = 7
CADTRIS_MIN_WIDTH = 6
CADTRIS_MAX_WIDTH = 50
CADTRIS_INITIAL_HEIGHT = 15
CADTRIS_MIN_HEIGHT = 9
CADTRIS_MAX_HEIGHT = 100

CADTRIS_MAX_LEVEL = 5
CADTRIS_LINES_PER_LEVEL = 6
CADTRIS_MIN_SPEED = 0.5  # 0.7  # drops per second
CADTRIS_MAX_SPEED = 2  # drops per second

CADTRIS_TETRONIMO_COLORS = (
    (255, 0, 0, 255),
    (0, 255, 0, 255),
    (0, 0, 255, 255),
    (255, 255, 0, 255),
    (0, 255, 255, 255),
    (255, 0, 255, 255),
)
CADTRIS_WALL_COLOR = None
CADTRIS_BLOCK_APPEARANCE = "Steel - Satin"

CADTRIS_SCORES_PATH = Path(appdirs.user_state_dir("CADTRIS")) / "highscores.json"

CADTRIS_DISPLAYED_SCORES = 5
CADTRIS_NO_SCORE_SYMBOL = "-"
CADTRIS_MAX_SAVED_SCOES = 100
