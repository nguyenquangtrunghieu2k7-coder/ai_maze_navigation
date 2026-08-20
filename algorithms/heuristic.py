from core.maze import Maze
import math
from core.config import *
from core.terrain import TERRAIN_DATA

def zero_heuristic(
    maze: Maze,
    current: tuple[int, int],
    goal: tuple[int, int],
) -> float:
    return 0.0

def euclidean_3d(
    maze: Maze,
    current: tuple[int, int],
    goal: tuple[int, int]
) -> float:

    x, y = current
    gx, gy = goal

    z = maze.get_elevation(x, y)
    gz = maze.get_elevation(gx, gy)

    dx = gx - x
    dy = gy - y
    dz = gz - z

    return math.sqrt(dx * dx + dy * dy + dz * dz)

def time_heuristic(maze: Maze, current: tuple[int,int], goal: tuple[int,int]) -> float:
    distance = euclidean_3d(maze, current, goal)
    max_speed = BASE_SPEED*1.0

    return distance/max_speed

def energy_heuristic(maze: Maze, current: tuple[int,int], goal: tuple[int,int]) -> float:
    x,y = current
    gx, gy = goal

    cell = maze.get_cell(x,y)
    next_cell = maze.get_cell(gx,gy)

    z = cell.elevation
    gz = next_cell.elevation
    dz = gz - z

    distance = euclidean_3d(maze, current, goal)

    #Lower bound của năng lượng chống lại trọng lực
    gravity_energy = max(0.0, ROBOT_MASS*GRAVITY*dz)
    # Lower bound của friction
    min_friction = min(
                        info.friction
                        for info in TERRAIN_DATA.values()
                    )
    friction_energy = (ROBOT_MASS*GRAVITY*distance*min_friction)
    # Lower bound của static energy
    max_speed = BASE_SPEED * 1.0
    min_time = distance / max_speed

    static_energy = STATIC_POWER * min_time

    return static_energy
       