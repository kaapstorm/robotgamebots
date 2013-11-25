from abstract_robot import AbstractRobot


class Robot(AbstractRobot):
    """
    This Robot walks randomly
    """
    def act(self, game):
        loc = self.get_open_adjacent(game)
        if loc:
            return ['move', loc]
        return ['guard']
