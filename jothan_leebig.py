import random
from copy import deepcopy
from norman_abstract_robot import AbstractRobot
import rg
from settings import settings


DEBUG = True


class Height(object):
    INVALID = 65536
    OBSTACLE = 512
    SPAWN = 256
    DIBS = 128  # Prevents collision with friendlies
    # Friend and enemy heights will be compounded by recursion.
    #FRIEND = 8.0  # For exponential curves
    #ENEMY = -8.0
    FRIEND = 4.0  # For linear curves
    ENEMY = -4.0


class Robot(AbstractRobot):
    """
    Technically `Jothan Leebig`_ was a human, but he was a robotist, and he
    shunned contact with his own kind.


    _Jothan Leebig: http://en.wikipedia.org/wiki/The_Naked_Sun
    """
    def __init__(self):
        self.robots = None  # Locations of all robots in the game
        self.solaria = None  # A landscape where enemies form troughs and friends and obstacles form peaks
        self.robot_index = None  # We have n in the field. How many have moved?
        self.team = None  # Dictionary of locations and robots on our team
        self.last_game = None  # The state of the previous turn

    def act(self, game):
        # What do we know?
        if self.robots != set(game['robots'].keys()):
            # Robots have moved since we last checked. This is a new turn.
            if DEBUG:
                print('New turn')
            self.team = {loc: bot for loc, bot in game['robots'].iteritems()}
            self.robot_index = 0
            self.init_solaria()
            self.populate_solaria(game)
            self.robots = set(game['robots'].keys())
        else:
            self.robot_index += 1
        if self.robot_index == len(self.team) - 1:
            if DEBUG:
                print('Robot index is {}, team size is {}, saving game state'.format(
                    self.robot_index, len(self.team)))
            self.last_game = deepcopy(game)

        # Attack neighbours
        adj_enemies = self.get_adjacent_bots(game)
        if adj_enemies:
            if self.is_worth_dying(adj_enemies):
                return ['suicide']
            return ['attack', next(iter(adj_enemies.keys()))]

        # Move downhill
        downhill = self.get_downhill()
        if downhill == self.location:
            return ['guard']
        # Mark where we will move or attack, so that other team members won't try to move there.
        x, y = downhill
        self.solaria[y][x] += Height.DIBS
        if self.collided(downhill, game):
            if DEBUG:
                print('Preemptive attack location {}'.format(downhill))
            return ['attack', downhill]
        return ['move', downhill]

    def collided(self, loc, game):
        """
        Checks whether robots collided at loc in the last turn
        """
        if not self.last_game:
            # This is the first turn.
            return False
        collided_friend = collided_enemy = False
        adjacent = rg.locs_around(loc)
        for adj in adjacent:
            if (
                adj in game['robots'] and
                adj in self.last_game['robots'] and
                game['robots'][adj].player_id == self.last_game['robots'][adj]['player_id'] and
                game['robots'][adj].hp == self.last_game['robots'][adj]['hp'] - settings.collision_damage
            ):
                if game['robots'][adj].player_id == self.player_id:
                    collided_friend = True
                else:
                    collided_enemy = True
                if collided_friend and collided_enemy:
                    if DEBUG:
                        print('Avoided collision at {}'.format(loc))
                    return True
        return False

    def curve_solaria(self, x, y, inc, exp=False):
        """
        Increment the solaria location by inc, and recursively increment
        adjacent locations by a reduced value of inc.

        By default inc is decremented. If exp is True, inc is halved.

        >>> settings.board_size = 5
        >>> daneel = Robot()
        >>> daneel.init_solaria()
        >>> daneel.curve_solaria(2, 2, 3)
        >>> daneel.solaria == [
        ... [0, 0, 1, 0, 0],
        ... [0, 2, 2, 2, 0],
        ... [1, 2, 7, 2, 1],
        ... [0, 2, 2, 2, 0],
        ... [0, 0, 1, 0, 0]]
        True
        >>> daneel.init_solaria()
        >>> daneel.curve_solaria(2, 2, 4, exp=True)
        >>> daneel.solaria == [
        ... [0, 0, 1, 0, 0],
        ... [0, 2, 2, 2, 0],
        ... [1, 2, 8, 2, 1],
        ... [0, 2, 2, 2, 0],
        ... [0, 0, 1, 0, 0]]
        True

        """
        if (
            -1 < inc < 1 or
            not (0 <= x < settings.board_size) or
            not (0 <= y < settings.board_size)
        ):
            return
        self.solaria[y][x] += int(inc)
        if exp:
            small_inc = float(inc) / 2
        else:
            small_inc = inc - 1 if inc > 0 else inc + 1
        self.curve_solaria(x, y + 1, small_inc)
        self.curve_solaria(x + 1, y, small_inc)
        self.curve_solaria(x, y - 1, small_inc)
        self.curve_solaria(x - 1, y, small_inc)

    def get_downhill(self):
        """
        Determine which adjacent location is downhill from self.location

        >>> settings.board_size = 5
        >>> daneel = Robot()
        >>> daneel.solaria = [
        ... [0, 0, 1, 0, 0],
        ... [0, 2, 2, 2, 0],
        ... [1, 2, 8, 2, 1],
        ... [0, 2, 2, 2, 0],
        ... [0, 0, 1, 0, 0]]
        >>> daneel.location = (2, 1)  # 3 across, 2 down
        >>> daneel.get_downhill()
        (2, 0)
        >>> daneel.location = (3, 2)
        >>> daneel.get_downhill()
        (4, 2)
        >>> daneel.location = (2, 3)
        >>> daneel.get_downhill()
        (2, 4)
        >>> daneel.location = (1, 2)
        >>> daneel.get_downhill()
        (0, 2)

        """
        x, y = self.location
        adjacents = [(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]
        locs = [(x, y)]
        lowest = self.solaria[y][x]
        for sxa, sya in adjacents:
            try:
                height = self.solaria[sya][sxa]
            except IndexError:
                continue
            if height == lowest:
                locs += [(sxa, sya)]
            elif height < lowest:
                lowest = height
                locs = [(sxa, sya)]
        return locs[0] if len(locs) == 1 else random.choice(locs)

    def init_solaria(self):
        """
        Initialise a matrix with the dimentions of the board

        >>> settings.board_size = 5
        >>> daneel = Robot()
        >>> daneel.init_solaria()
        >>> daneel.solaria == [
        ... [0, 0, 0, 0, 0],
        ... [0, 0, 0, 0, 0],
        ... [0, 0, 0, 0, 0],
        ... [0, 0, 0, 0, 0],
        ... [0, 0, 0, 0, 0]]
        True

        """
        self.solaria = [[0 for x in range(settings.board_size)] for y in range(settings.board_size)]

    def populate_solaria(self, game):
        for y in range(settings.board_size):
            for x in range(settings.board_size):
                loc = (x, y)
                if 'obstacle' in rg.loc_types(loc):
                    self.solaria[y][x] += Height.OBSTACLE
                elif 'spawn' in rg.loc_types(loc):
                    self.solaria[y][x] += Height.SPAWN
                if loc in game['robots']:
                    bot = game['robots'][loc]
                    if bot.player_id == self.player_id:
                        self.curve_solaria(x, y, Height.FRIEND)
                    else:
                        # Weak enemies are more attractive
                        #height = Height.ENEMY * float(self.hp) / bot.hp
                        #self.curve_solaria(x, y, height)
                        self.curve_solaria(x, y, Height.ENEMY)

    def print_solaria(self):
        for y in self.solaria:
            for x in y:
                print '{:03d}'.format(x),
            print
        print
