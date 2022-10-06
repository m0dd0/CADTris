from pathlib import Path
from .libs.appdirs import appdirs

# general settings
APPNAME = "CADTris"
LOGGING_ENABLED = True
LOGGING_FOLDER = Path(appdirs.user_log_dir(APPNAME))
LOGFILE_BASENAME = "CADTrisLog.log"
LOGGING_ROTATE_WHEN = "H"
LOGGING_ROTATE_INTERVAL = 6
LOGGING_ROTATE_COUNT = 20
RESOURCE_FOLDER = Path(__file__).parent / "resources"
CADTRIS_WORKSPACE = "FusionSolidEnvironment"
CADTRIS_TAB = "ToolsTab"
CADTRIS_PANEL = "SolidScriptsAddinsPanel"
CADTRIS_CUSTOM_EVENT_ID = "cadtris_custom_event_id"

# command related settings
CADTRIS_COMMAND_NAME = "CADtris"
CADTRIS_TOOLTIP = "Play CADtris!"

CADTRIS_COMPONENT_NAME = "CADTris"

# game related settings
CADTRIS_INITIAL_VOXEL_SIZE = 10

CADTRIS_INITIAL_WIDTH = 7
CADTRIS_MIN_WIDTH = 6
CADTRIS_MAX_WIDTH = 25
CADTRIS_INITIAL_HEIGHT = 15
CADTRIS_MIN_HEIGHT = 9
CADTRIS_MAX_HEIGHT = 50

CADTRIS_MAX_LEVEL = 5
CADTRIS_LINES_PER_LEVEL = 6
# time delta in earlier version 0.75s...0.25s --> 1/0.75=1.333 ... 4
CADTRIS_MIN_SPEED = 1  # drops per second
CADTRIS_MAX_SPEED = 4  # drops per second

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

# ui related settings
CADTRIS_CONTROL_GROUP_NAME = "Controls"
CADTRIS_PLAY_BUTTON_NAME = "Play"
CADTRIS_PAUSE_BUTTON_NAME = "Pause"
CADTRIS_RESET_BUTTON_NAME = "Reset"
CADTRIS_INFO_GROUP_NAME = "Info"
CADTRIS_LEVEL_SLIDER_NAME = "Level"
CADTRIS_LEVEL_SLIDER_TOOLTIP = "Current level."
CADTRIS_SCORE_INPUT_NAME = "Score"
CADTRIS_SCORE_INPUT_TOOLTIP = "Your current score."
CADTRIS_LINES_INPUT_NAME = "Lines"
CADTRIS_LINES_INPUT_TOOLTIP = "Number of line you have cleared till now."
CADTRIS_SCORES_GROUP_NAME = "Highscores (Top 5)"
CADTRIS_SCORES_PATH = Path(appdirs.user_state_dir(APPNAME)) / "highscores.json"
CADTRIS_DISPLAYED_SCORES = 5
CADTRIS_NO_SCORE_SYMBOL = "-"
CADTRIS_MAX_SAVED_SCOES = 100
CADTRIS_SETTINGS_GROUP_NAME = "Settings"
CADTRIS_HEIGHT_INPUT_NAME = "Height (blocks)"
CADTRIS_HEIGHT_INPUT_TOOLTIP = "Height of the game in blocks."
CADTRIS_WIDTH_INPUT_NAME = "Width (blocks)"
CADTRIS_WIDTH_INPUT_TOOLTIP = "Width of the game in blocks."
CADTRIS_BLOCKSIZE_INPUT_NAME = "Block size"
CADTRIS_BLOCKSIZE_INPUT_TOOLTIP = "Side length of single block in mm."
CADTRIS_KEEP_INPUT_NAME = "Keep blocks"
CADTRIS_KEEP_INPUT_TOOLTIP = (
    "Flag determining if the blocks should be kept after closing the gae command."
)
CADTRIS_KEEP_INPUT_INITIAL_VALUE = False
CADTRIS_GAME_OVER_MESSAGE = "GAME OVER."
CADTRIS_HIGHSCORE_MESSAGE = "\n\nCongratulations, you made the {} place in the ranking!"
CADTRIS_DIRECT_DESIGN_QUESTION = (
    "WARNING: CADTris can only be played in direct design mode.\n"
    + "Do you want to switch to direct design mode by disabling the timeline?\n\n"
    + "The timeline and all design history will be removed, \n"
    + "and further operations will not be captured in the timeline."
)
CADTRIS_DIRECT_DESIGN_TITLE = "Warning"
MIN_VOXELS_FOR_PROGRESSBAR = 15
CADTRIS_PROGRESSBAR_TITLE = "Updating Screen"
CADTRIS_PROGRESSBAR_MESSAGE = "Updating Screen (%p%)"
CADTRIS_VOXEL_CHANGES_FOR_DIALOG = 10

# camera/display related settings
# {"xy", "yz", "xz"} # "xz" will display from the backside FIXME
CADTRIS_DISPLAY_PLANE = "xy"
CADTRIS_SCREEN_OFFSET_LEFT = 3  # in blocks
CADTRIS_SCREEN_OFFSET_RIGHT = 1
CADTRIS_SCREEN_OFFSET_TOP = 4
CADTRIS_SCREEN_OFFSET_BOTTOM = 3
