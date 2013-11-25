import rg
from abstract_robot import can_move, AbstractRobot


class Robot(AbstractRobot):
    """
    This Robot exits the spawning zone, and squats
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

        # Attack neighbours
        adj_enemies = self.get_adjacent_bots(game)
        if adj_enemies:
            if self.is_worth_dying(adj_enemies):
                return ['suicide']
            return ['attack', next(iter(adj_enemies.keys()))]

        # Move away from friendlies
        adj_friendlies = self.get_adjacent_bots(game, enemies=False)
        for adj in adj_friendlies:
            x, y = self.location
            ax, ay = adj
            loc = (x + x - ax, y + y - ay)
            if can_move(loc, game):
                return ['move', loc]

        # Squat
        return ['guard']
