import random
import operator
import rg
from settings import settings


def can_move(loc, game, spawnok=False):
    """
    Returns True if loc is an unoccupied, normal location

    :param loc: Proposed location
    :param game: Current game data
    :param spawnok: Is it OK to move to a spawn zone location?
    """
    # In GitHub version of rgkit, rg.loc_types(loc) returns a set, and website
    # version it returns a list. Cast as set. Website uses Python < 2.7, so no
    # set literals
    if spawnok:
        return set(rg.loc_types(loc)) | set(['spawn']) == set(['normal', 'spawn']) and loc not in game['robots']
    return set(rg.loc_types(loc)) == set(['normal']) and loc not in game['robots']


class AbstractRobot(object):
    """
    Provides useful methods to Robots
    """
    def get_adjacent_bots(self, game, enemies=True):
        """
        Returns a dictionary of adjacent bots' locations: health points

        Defaults to only enemies. If enemies is False, return friendlies.
        """
        op = operator.ne if enemies else operator.eq
        adjacent = rg.locs_around(self.location)
        adj_enemies = {}
        for adj in adjacent:
            if adj in game['robots'] and op(game['robots'][adj].player_id, self.player_id):
                adj_enemies[adj] = game['robots'][adj].hp
        return adj_enemies

    def get_open_adjacent(self, game, spawnok=False):
        """
        Return an open location adjacent to here, or None

        If spawnok is True, it's OK to move to a spawn zone location
        """
        adjacent = rg.locs_around(self.location)
        random.shuffle(adjacent)
        for adj in adjacent:
            if can_move(adj, game, spawnok=spawnok):
                return adj

    def is_worth_dying(self, adj_enemies):
        if not adj_enemies:
            return False

        # Our death will cost them more
        total_damage = sum([min(hp, settings.suicide_damage) for hp in iter(adj_enemies.values())])
        if self.hp < total_damage:
            return True

        # We are one attack away from death (assuming all adjacent enemies attack us)
        if self.hp <= max(settings.attack_range) * len(adj_enemies):
            return True

        return False
