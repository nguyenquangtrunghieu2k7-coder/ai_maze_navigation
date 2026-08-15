#recursive_backtracking.py là module sinh mê cung
import random
from core.maze import Maze

class RecursiveBacktrackingGeneraion:
    def __init__(self, seed: int | None=None):
        self.random = random.Random(seed)
    def generate(self, width, height) -> Maze:
        if width%2 == 0:
            width += 1
        if height%2 == 0:
            height += 1
        maze = Maze(width,height)
        self._carve(Maze)
        maze.start = (1,1)
        maze.goal = (width -2, height -2)

        return maze
    def _carve(self, maze: Maze):
        stack=[(1,1)]
        maze.set_walkable(1,1,True)
        direction = [(2,0), (-2,0), (0,2), (0, -2),]

        while stack:
            x,y = stack[-1]
            neighbors = []

            for dx,dy in direction:
                nx,ny = x+dx, y+dy

                if (maze.in_bounds(nx,ny) and not maze.is_walkable(nx,ny)):
                    neighbors.append((nx,ny,dx,dy))
            if neighbors:
                nx,ny,dx,dy = self.random.choice(neighbors)
                maze.set_walkable(x+dx//2, y+dy//2, True)
                maze.set_walkable(nx,ny, True)

                stack.append((nx,ny))
            else: 
                stack.pop()
                