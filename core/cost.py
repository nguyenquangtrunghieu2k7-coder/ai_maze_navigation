import math
from core.maze import Maze
from core.terrain import Terrain, get_friction

ROBOT_MASS = 10.0
GRAVITY = 9.81
STATIC_POWER = 50
BASE_SPEED = 1.0

def edge_distance(x: int,y: int,nx: int,ny: int,z: int,nz: int):
    dx = nx - x
    dy = ny - y
    dz = nz - z
    return math.sqrt(dx*dx + dy*dy + dz*dz)
def slope_angle(x: int,y: int,nx: int,ny: int,z: int,nz: int):
    dx = nx - x
    dy = ny - y
    dz = nz - z

    horizontal_distance = math.sqrt(dx*dx + dy*dy)

    return math.atan2(dz, horizontal_distance)

def distance_cost(maze: Maze, x: int, y: int, nx: int, ny: int) -> float:
    z = maze.grid[y][x].get_elevation(x,y)
    nz = maze.grid[ny][nx].get_elevation(nx,ny)
    return edge_distance(x,y,nx,ny,z,nz)
def time_cost(maze: Maze, x: int, y: int, nx: int, ny: int) -> float:
    z = maze.grid[y][x].get_elevation(x,y)
    nz = maze.grid[ny][nx].get_elevation(nx,ny)
    distance = edge_distance(x,y,nx,ny,z,nz)

    speed = maze.get_speed(nx,ny)

    return distance/speed
def energy_cost(maze: Maze, x: int, y: int, nx: int, ny: int) -> float:
    cell = maze.get_cell(x,y)
    next_cell = maze.get_cell(nx,ny)

    z = cell.elevation
    nz = next_cell.elevation

    distance = edge_distance(x,y,nx,ny,z,nz)
    phi = slope_angle(x,y,nx,ny,z,nz)
    mu = get_friction(next_cell) 

    breaking_angle = -math.atan(mu)

    if phi <= breaking_angle:
        motion_energy = 0.0
    else:
        motion_energy = ROBOT_MASS*GRAVITY*distance*(math.sin(phi) + mu*math.cos(phi))
    
    speed = maze.get_speed(nx,ny)
    time = distance/speed
    static_energy = STATIC_POWER*time

    return static_energy + motion_energy