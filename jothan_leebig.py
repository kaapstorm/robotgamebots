import random
from abstract_robot import AbstractRobot
import rg
from settings import settings


class Height(object):
    INVALID = 65536
    OBSTACLE = 512
    SPAWN = 256
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
        self.robots = None
        self.solaria = None

    def act(self, game):
        # Attack neighbours
        adj_enemies = self.get_adjacent_bots(game)
        if adj_enemies:
            if self.is_worth_dying(adj_enemies):
                return ['suicide']
            return ['attack', next(iter(adj_enemies.keys()))]

        # Move downhill
        if self.robots != set(game['robots'].keys()):
            # Robots have moved since we last checked
            self.init_solaria()
            self.populate_solaria(game)
            self.robots = set(game['robots'].keys())
        downhill = self.get_downhill()
        if downhill == self.location:
            return ['guard']
        return ['move', downhill]

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
        return random.choice(locs)

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
