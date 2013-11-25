import rg
from abstract_robot import can_move


class Robot:
    """
    This Robot herds in the middle
    """
    def act(self, game):
        if rg.dist(self.location, rg.CENTER_POINT) < 1:
            return ['guard']
        closer = rg.toward(self.location, rg.CENTER_POINT)
        return ['move', closer] if can_move(closer, game) else ['guard']
