from dataclasses import dataclass
from .terrain import Terrain

@dataclass(slot=True)
class Cell:
    x: int
    y: int
    walkable: bool = True
    terrain: Terrain = Terrain.ROAD
    @property
    def pos(self) -> tuple[int,int]:
        return (self.x, self.y)
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    def __repr__(self) -> str:
        return (
            f"Cell(x={self.x}, y={self.y}, "
            f"walkable={self.walkable}, terrain= {self.terrain})"
        )
