import random
from collections import deque, namedtuple
import enum
from typing import Iterable
from functools import partial

import adsk.core, adsk.fusion

from ...apper.utilities import (PeriodicExecuter, create_cube, new_comp,
                                apply_color, change_material, AppObjects,
                                view_extent_by_rectangle, clear_collection,
                                make_ordinal)

ao = AppObjects()

GameCoord = namedtuple('GameCoord', ['x', 'y'])


@enum.unique
class GameState(enum.Enum):
    start = enum.auto()
    running = enum.auto()
    pause = enum.auto()
    gameover = enum.auto()


class Figure():
    #   y
    #   ^
    # 3 | (0,3) (1,3) (2,3) (3,3)
    # 2 | (0,2) (1,2) (2,2) (3,2)
    # 1 | (0,1) (1,1) (2,1) (3,1)
    # 0 | (0,0) (1,0) (2,0) (3,0)
    #     ------------------------> x
    #      0     1     2     3

    I = deque([{(1, 3), (1, 2), (1, 1), (1, 0)},
               {(0, 2), (1, 2), (2, 2), (3, 2)}])
    Z = deque([{(0, 2), (1, 2), (1, 1), (2, 1)},
               {(2, 3), (2, 2), (1, 2), (1, 1)}])
    S = deque([{(2, 2), (3, 2), (1, 1), (2, 1)},
               {(1, 3), (1, 2), (2, 2), (2, 1)}])
    L = deque([{(1, 3), (2, 3), (1, 2), (1, 1)},
               {(0, 3), (0, 2), (1, 2), (2, 2)},
               {(1, 3), (1, 2), (1, 1), (0, 1)},
               {(0, 2), (1, 2), (2, 2), (2, 1)}])
    J = deque([{(1, 3), (2, 3), (2, 2), (2, 1)},
               {(1, 2), (2, 2), (3, 2), (1, 1)},
               {(2, 3), (2, 2), (2, 1), (3, 1)},
               {(3, 3), (1, 2), (2, 2), (3, 2)}])
    T = deque([{(1, 3), (0, 2), (1, 2), (2, 2)},
               {(1, 3), (0, 2), (1, 2), (1, 1)},
               {(0, 2), (1, 2), (2, 2), (1, 1)},
               {(1, 3), (1, 2), (2, 2), (1, 1)}])
    O = deque([{(1, 3), (2, 3), (1, 2), (2, 2)}])
    all_figures = [I, Z, S, L, J, T, O]

    figure_colors = [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
        (0, 255, 255, 255),
        (255, 0, 255, 255),
    ]

    def __init__(self, x, y):
        self._x = x
        self._y = y

        self._figure_coords = random.choice(
            self.all_figures)  # set of rotations of a single tetronimo
        self.color = random.choice(self.figure_colors)

    @property
    def coords(self):
        return set(
            GameCoord(x + self._x, y + self._y)
            for x, y in self._figure_coords[0])

    def rotate(self, n=1):
        self._figure_coords.rotate(n)

    def move_vertical(self, n):
        self._y += n

    def move_horizontal(self, n):
        self._x += n


class Game:
    minimum_width = 9
    maximum_width = 50
    minimum_height = 9
    maximum_height = 100
    max_level = 5
    lines_per_level = 5
    # orig times: 0.8 -> 0.71 -> 0.63 -> 0.55 -> 0.46 -> 0.3 -> ...
    drop_time = lambda self, level: 0.75 - (level - 1) * 0.1
    achieved_score = lambda self, lines, level: (lines**2) * level

    def __init__(self, screen, periodic_go_down_func, height=20, width=10):
        self.screen = screen
        self.go_down_timer = PeriodicExecuter(float('inf'),
                                              periodic_go_down_func)

        self.figure = None  # has no setter and therfore must be defined here

        self.reset()

        self._height = height
        self._width = width
        self.screen.draw_frame(self)

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    @height.setter
    def height(self, new_height):
        if self.state == GameState.start:
            self._height = new_height  # TODO check borders
            self.field = {}
            self.screen.draw_frame(self)

    @width.setter
    def width(self, new_width):
        if self.state == GameState.start:
            self._width = new_width  # TODO check borders
            self.field = {}
            self.screen.draw_frame(self)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state
        self.screen.state_change(self)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, new_level):
        self._level = min(new_level, self.max_level)
        self.go_down_timer.interval = self.drop_time(self._level)
        self.screen.update_game_info(self)

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, new_score):
        self._score = new_score
        self.screen.update_game_info(self)
        # self.level = self._score // 10 + 1

    @property
    def figure_count(self):
        return self._figure_count

    @figure_count.setter
    def figure_count(self, new_count):
        self._figure_count = new_count
        # self.level = self._figure_count // 10 + 1

    @property
    def line_count(self):
        return self._line_count

    @line_count.setter
    def line_count(self, new_count):
        self._line_count = new_count
        self.level = self._line_count // self.lines_per_level + 1
        self.screen.update_game_info(self)

    def _create_figure(self):
        self.figure = Figure(self.width // 2 - 1, self.height - 3)
        self.figure_count += 1

    def _intersects(self):
        for x, y in self.figure.coords:
            if (x >= self.width or x < 0 or y < 0 or (x, y) in self.field):
                return True
        return False

    def _break_lines(self):
        lines = 0
        for y in range(self.height, -1, -1):  # from top to botton
            if all((x, y) in self.field for x in range(self.width)):
                for p in set(self.field.keys()):  # remove row
                    if p.y == y:
                        self.field.pop(p)
                new_field = {}
                for p, c in self.field.items():  # lower all points above
                    if p.y > y:  # point is above
                        new_field[GameCoord(p.x, p.y - 1)] = c
                    else:
                        new_field[p] = c
                self.field = new_field
                lines += 1

        self.line_count += lines
        self.score += self.achieved_score(lines, self.level)

    def _freeze(self):
        for p in self.figure.coords:
            self.field[p] = self.figure.color
        self._break_lines()
        self._create_figure()
        if self._intersects():
            self.figure = None
            self.go_down_timer.reset()
            self.go_down_timer.pause()
            self.state = GameState.gameover

    def start(self):
        if self.state == GameState.start or self.state == GameState.pause:
            if self.state == GameState.start:
                self._create_figure()
                self.screen.draw_field(self)
            self.go_down_timer.start()
            self.state = GameState.running
            return True

    def pause(self):
        if self.state == GameState.running:
            self.go_down_timer.pause()
            self.state = GameState.pause
            return True

    def reset(self):
        self.go_down_timer.reset()
        self.go_down_timer.pause()
        self.go_down_timer.interval = float('inf')
        self.state = GameState.start

        self.figure_count = 0
        self.line_count = 0
        self.score = 0
        self.level = 1

        self.field = {}  # {(x,y):(r,g,b)}
        self.figure = None
        self.screen.draw_field(self)
        return True

    def drop(self):
        if self.state == GameState.running:
            while not self._intersects():
                self.figure.move_vertical(-1)
            self.figure.move_vertical(1)
            self._freeze()
            self.go_down_timer.reset()
            self.screen.draw_field(self)

    def move_down(self, n=1):
        if self.state == GameState.running:
            self.figure.move_vertical(-n)
            if self._intersects():
                self.figure.move_vertical(n)
                self._freeze()
            self.go_down_timer.reset()
            self.screen.draw_field(self)

    def move_side(self, n):
        if self.state == GameState.running:
            self.figure.move_horizontal(n)
            if self._intersects():
                self.figure.move_horizontal(-n)
            self.screen.draw_field(self)

    def rotate(self, n=1):
        if self.state == GameState.running:
            self.figure.rotate(n)
            if self._intersects():
                self.figure.rotate(-n)
            self.screen.draw_field(self)


class Block:
    def __init__(self,
                 center,
                 side,
                 comp,
                 base_feature,
                 color=None,
                 material=None):
        self._center = center
        self._side = side
        self._comp = comp
        self._color = color
        self._material = material
        self.brep = None
        self.base_feature = base_feature

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, new_center):
        self._center = new_center
        self._recreate_brep()

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, new_side):
        self._side = new_side
        self._recreate_brep()

    @property
    def comp(self):
        return self._comp

    @comp.setter
    def comp(self, new_block_comp):
        self._comp = new_block_comp
        self._recreate_brep()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_color):
        self._color = new_color
        if new_color is not None:
            apply_color(self.brep, *self.color)

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, new_material):
        self._material = new_material
        if new_material is not None:
            change_material(self.brep, self.material)

    def _recreate_brep(self):
        if self.brep:
            self.brep.deleteMe()
            self.create_brep()

    def create_brep(self):
        if not self.brep:
            cube = create_cube(self.center, self.side)
            if self.base_feature is not None:
                self.brep = self.comp.bRepBodies.add(cube, self.base_feature)
            else:
                self.brep = self.comp.bRepBodies.add(cube)
            if self.material:
                change_material(self.brep, self.material)
            if self.color:
                apply_color(self.brep, *self.color)

    def delete_brep(self):
        self.brep.deleteMe()
        self.brep = None


class Screen():
    def __init__(self,
                 inputs,
                 input_ids,
                 scores=[],
                 scores_to_show=5,
                 offset=(0, 0, 0),
                 block_size=5,
                 frame_material=None,
                 frame_color=None,
                 field_material=None):
        self.cadtris_comp = new_comp('CADtris')
        self.frame_comp = new_comp('Frame', self.cadtris_comp)
        self.field_comp = new_comp('Field', self.cadtris_comp)

        self.scores = scores
        self.scores_to_show = scores_to_show

        self._frame_base_feature = None
        self._field_base_feature = None

        self.offset = offset
        self.block_size = block_size

        self._frame_block_material = frame_material
        self._frame_block_color = frame_color
        self._field_block_material = field_material

        self.frame_blocks = []
        self.field_blocks = []

        self.todo = []  # queue not needed sinceno large number of calls

        self.inputs = inputs
        self.input_ids = input_ids

    @property
    def field_base_feature(self):
        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            if self._field_base_feature is None:
                self._field_base_feature = self.field_comp.features.baseFeatures.add(
                )
                self._field_base_feature.name = 'CADtris field'
            return self._field_base_feature
        else:
            return None

    @property
    def frame_base_feature(self):
        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            if self._frame_base_feature is None:
                self._frame_base_feature = self.frame_comp.features.baseFeatures.add(
                )
                self._frame_base_feature.name = 'CADtris frame'
            return self._frame_base_feature
        else:
            return None

    def game_coord_to_fusion(self, game_coord):
        coord_3d = (game_coord.x, 0, game_coord.y)
        fusion_coord = tuple((c + off) * self.block_size
                             for c, off in zip(coord_3d, self.offset))
        return fusion_coord

    def synchronize(self, existing_blocks: Iterable, target_blocks):
        target_centers = [block.center for block in target_blocks]
        to_delete = [
            block for block in existing_blocks if
            block.center not in target_centers or block.side != self.block_size
        ]
        while to_delete:
            block = to_delete.pop(0)
            existing_blocks.remove(block)
            block.delete_brep()

        for target_block in target_blocks:
            existing_block = None
            for block in existing_blocks:
                if block.center == target_block.center and block.side == self.block_size:
                    existing_block = block
                    break
            if existing_block:
                if existing_block.color != target_block.color:
                    existing_block.color = target_block.color
            else:
                target_block.create_brep()
                existing_blocks.append(target_block)

    def draw_frame(self, game):
        frame_coords = set()
        for y in range(game.height):
            frame_coords.add(self.game_coord_to_fusion(GameCoord(-1, y)))
            frame_coords.add(
                self.game_coord_to_fusion(GameCoord(game.width, y)))
        for x in range(-1, game.width + 1):
            frame_coords.add(self.game_coord_to_fusion(GameCoord(x, -1)))
        frame_blocks = [
            Block(coord, self.block_size, self.frame_comp,
                  self.frame_base_feature, self._frame_block_color,
                  self._frame_block_material) for coord in frame_coords
        ]

        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            self.todo.append(self.frame_base_feature.startEdit)
        self.todo.append(
            partial(self.synchronize, self.frame_blocks, frame_blocks))
        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            self.todo.append(self.frame_base_feature.finishEdit)

    def draw_field(self, game):
        field_and_figure = {
            self.game_coord_to_fusion(coord): color
            for coord, color in game.field.items()
        }
        if game.figure is not None:
            for coord in game.figure.coords:
                field_and_figure[self.game_coord_to_fusion(
                    coord)] = game.figure.color

        field_blocks = [
            Block(coord, self.block_size, self.field_comp,
                  self.field_base_feature, color, self._field_block_material)
            for coord, color in field_and_figure.items()
        ]

        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            self.todo.append(self.field_base_feature.startEdit)
        self.todo.append(
            partial(self.synchronize, self.field_blocks, field_blocks))
        if ao.design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            self.todo.append(self.field_base_feature.finishEdit)

    def write_scores(self):
        highscore_group = self.inputs.itemById(
            self.input_ids.HighscoreGroup.value)
        clear_collection(highscore_group.children)
        highscore_group.children.addTextBoxCommandInput(
            'ScoreLabels_inutId', 'Rank', 'Points', 1, True)
        for rank in range(1, min(self.scores_to_show, len(self.scores)) + 1):
            highscore_group.children.addTextBoxCommandInput(
                'Score{0}_inputId'.format(rank), '{0}.'.format(rank),
                '{0}'.format(self.scores[rank - 1]), 1, True)
        if len(self.scores) == 0:
            highscore_group.children.addTextBoxCommandInput(
                'NoScore_inputId', '', 'No scores yet', 1, True)

    def _on_game_over(self, score):
        achieved_rank = len(self.scores) + 1
        for index, points in enumerate(self.scores):
            if points <= score:
                achieved_rank = index + 1
                break
        self.scores.insert(achieved_rank - 1, score)
        score_message = ''
        if achieved_rank <= self.scores_to_show:
            score_message = '\n\nCongratulations! You made the {0} place in the ranking!'.format(
                make_ordinal(achieved_rank))
            self.write_scores()

        ao.ui.messageBox('Score: {0}{1}'.format(score, score_message),
                         'GAME OVER')

    def _update_cmd_dialog(self, active_ctrls, enabled_ctrls,
                           game_is_adjustable, info_is_shown):
        # it makes no sense to use an uniform dictonairy etc. for all infos ...
        # maybe use own subfunction for each "category" if it becomes mess<
        for button in self.inputs.itemById(
                self.input_ids.ControlGroup.value).children:
            button.value = button.id in active_ctrls
            button.isEnabled = button.id in enabled_ctrls

        for input_id in [
                self.input_ids.BlockHeight,
                self.input_ids.BlockWidth,
                self.input_ids.BlockSize,  # Height, Width
        ]:
            self.inputs.itemById(input_id.value).isEnabled = game_is_adjustable

        info_group = self.inputs.itemById(self.input_ids.GameInfoGroup.value)
        info_group.isVisible = info_is_shown

    def state_change(self, game):
        # {state: ([pressed_buttons], [enabled_buttons]),...}
        control_states = {
            GameState.start: ([], [self.input_ids.Play.value]),
            GameState.running:
            ([self.input_ids.Play.value],
             [self.input_ids.Pause.value, self.input_ids.Reset.value]),
            GameState.pause:
            ([self.input_ids.Pause.value],
             [self.input_ids.Play.value, self.input_ids.Reset.value]),
            GameState.gameover: ([], [self.input_ids.Reset.value])
        }

        active_ctrls = control_states[game.state][0]
        enabled_ctrls = control_states[game.state][1]
        game_is_adjustable = (game.state == GameState.start)
        info_is_shown = (game.state == GameState.running
                         or game.state == GameState.pause)

        self.todo.append(
            partial(self._update_cmd_dialog, active_ctrls, enabled_ctrls,
                    game_is_adjustable, info_is_shown))

        if game.state == GameState.gameover:
            self.todo.append(partial(self._on_game_over, game.score))

    def update_game_info(self, game):
        def update_info_cmd_dialog():
            self.inputs.itemById(self.input_ids.Score.value).text = str(
                game.score)
            self.inputs.itemById(
                self.input_ids.Speed.value).valueOne = game.level
            self.inputs.itemById(self.input_ids.Lines.value).text = str(
                game.line_count)

        self.todo.append(update_info_cmd_dialog)

    def set_camera(self, game):
        camera = ao.app.activeViewport.camera

        center = self.game_coord_to_fusion(
            GameCoord(game.width / 2, game.height / 2))
        camera.target = adsk.core.Point3D.create(*center)
        # being to close leads to wrong appearance in orthographic mode
        camera.eye = adsk.core.Point3D.create(center[0],
                                              -self.block_size * 100,
                                              center[2])
        camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
        camera.isSmoothTransition = False
        extent_horizontal = self.block_size * game.width * 1.5
        extent_vertical = self.block_size * game.height * 1.5
        camera.viewExtents = view_extent_by_rectangle(extent_horizontal,
                                                      extent_vertical)
        ao.app.activeViewport.camera = camera

    def _draw_all_in_ascii(self, game):
        pass
        # BORDER = 'x '
        # FREE = '  '
        # BLOCK = 'o '
        # output = ''
        # field_and_figure = {
        #     self.game_coord_to_fusion(coord): color
        #     for coord, color in game.field.items()
        # }
        # if game.figure is not None:
        #     for coord in game.figure.coords:
        #         field_and_figure[self.game_coord_to_fusion(
        #             coord)] = game.figure.color
        # for y in range(game.height):
        #     output += BORDER
        #     for x in range(game.width):
        #         if (x, y) in field_and_figure:
        #             output += BLOCK
        #         else:
        #             output += FREE
        #     output += BORDER + '\n'
        # output += BORDER * (game.width + 2)
        # print('\r')
        # print(output)
