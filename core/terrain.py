from enum import Enum
from dataclasses import dataclass

#dùng Enum Thay vì string: cell.terrain = 'sand'
#ta dùng: cell.terrain = Terrain.SAND
#Lợi ích: autocomplete trong VSCode, tránh typo, so sánh nhanh hơn

class Terrain(Enum):
    ROAD="road"
    GRASS="grass"
    SAND="sand"
    MUD="mud"

@dataclass(frozen=True) #TerrainInfo là metadata, không nên bị thay đổi trong runtime
#frozen=True nghĩa là immutable
class TerrainInfo:
    cost: float
    speed: float
    color: tuple[int,int,int]

TERRAIN_DATA = {
    Terrain.ROAD: TerrainInfo(
        cost=1.0,
        speed=2.0,
        color=(240, 240, 240),
    ),
    Terrain.GRASS: TerrainInfo(
        cost=2.0,
        speed=1.5,
        color=(120, 200, 120),
    ),
    Terrain.SAND: TerrainInfo(
        cost=4.0,
        speed=1.0,
        color=(230, 210, 120),
    ),
    Terrain.MUD: TerrainInfo(
        cost=7.0,
        speed=0.5,
        color=(140, 90, 60),
    ),

}