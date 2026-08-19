from core.maze import Maze

def distance_cost(maze: Maze, x: int, y: int, nx: int, ny: int) -> float:
    return 1.0
def terrain_cost(maze: Maze, x: int, y: int, nx: int, ny: int) -> float:
    return maze.terrain_cost(nx,ny)
def time_cost(
    maze: Maze,
    x: int,
    y: int,
    nx: int,
    ny: int
) -> float:
    speed = maze.get_speed(nx, ny)
    return 1.0 / speed
