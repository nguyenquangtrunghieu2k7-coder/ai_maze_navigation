from core.maze import Maze
from core.terrain import Terrain
from core.cost import (
    distance_cost,
    terrain_cost,
    time_cost,
)


def main():
    maze = Maze(5, 5)

    maze.set_walkable(1, 1)
    maze.set_walkable(2, 1)

    maze.set_terrain(1, 1, Terrain.ROAD)
    maze.set_terrain(2, 1, Terrain.MUD)

    print("Distance cost:")
    print(distance_cost(maze, 1, 1, 2, 1))

    print("Terrain cost:")
    print(terrain_cost(maze, 1, 1, 2, 1))

    print("Time cost:")
    print(time_cost(maze, 1, 1, 2, 1))


if __name__ == "__main__":
    main()