from core.maze import Maze
import math
from core.config import *
from core.cost import edge_distance, slope_angle
from core.terrain import get_friction


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

    return distance/speed
def energy_heuristic(maze: Maze, current: tuple[int,int], goal: tuple[int,int]) -> float:
    x,y = current
    nx, ny = goal

    cell = maze.get_cell(x,y)
    next_cell = maze.get_cell(nx,ny)

    z = cell.elevation
    nz = next_cell.elevation

    distance = edge_distance(x,y,nx,ny,z,nz)
    phi = slope_angle(x,y,nx,ny,z,nz)
    mu = get_friction(next_cell.terrain) 

    breaking_angle = -math.atan(mu)

    if phi <= breaking_angle:
        motion_energy = 0.0
    else:
        motion_energy = ROBOT_MASS*GRAVITY*distance*(math.sin(phi) + mu*math.cos(phi))
    
    speed = BASE_SPEED*maze.get_speed(nx,ny)
    time = distance/speed
    static_energy = STATIC_POWER*time

    return static_energy + motion_energy    