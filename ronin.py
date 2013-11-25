import rg
from abstract_robot import can_move, AbstractRobot


class Robot(AbstractRobot):
    """
    This Robot picks off the nearest target
    """
    def act(self, game):
        # Move out of spawning zone
        if 'spawn' in rg.loc_types(self.location):
            loc = self.get_open_adjacent(game)
            if loc:
                return ['move', loc]
            else:
                # All adjacent are occupied, or still in the spawning zone.
                loc = self.get_open_adjacent(game, spawnok=True)
                if loc:
                    return ['move', loc]

        # Find an enemy
        loc, d = self.get_closest_enemy(game)
        if d < 0:
            # The are no enemies
            return ['guard']
        elif d <= 1:
            # Enemy within range
            if self.is_worth_dying(game):
                return ['suicide']
            return ['attack', loc]
        else:
            # Enemy out of range
            closer = rg.toward(self.location, loc)
            if can_move(closer, game):
                return ['move', closer]
            loc = self.get_open_adjacent(game)
            if loc:
                return ['move', loc]
            return ['guard']

    def get_closest_enemy(self, game):
        """
        Returns location of and distance to nearest enemy.

        If no enemies, returns (0, 0), -1
        """
        closest_loc, closest_d, = (0, 0), -1
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                d = rg.dist(loc, self.location)
                if closest_d < 0:
                    closest_d = d
                    closest_loc = loc
                elif d < closest_d:
                    closest_d = d
                    closest_loc = loc
        return closest_loc, closest_d

    def is_worth_dying(self, game):
        adj_enemies = self.get_adjacent_bots(game)
        return super(Robot, self).is_worth_dying(adj_enemies)
