#recursive_backtracking.py là module sinh mê cung
import random
from core.maze import Maze
from collections import deque

def find_farthest_cell(maze, start):
    queue = deque([start])
    visited ={start}
    distance = {start: 0}

    farthest = start
    while queue:
        current = queue.popleft()
        farthest = current 

        x,y = current
        for nx,ny in maze.neighbors(x,y):
            if (nx,ny) not in visited:
                visited.add((nx,ny))
                distance[(nx,ny)] = distance[current] + 1
                queue.append((nx,ny))

    return farthest



class RecursiveBacktrackingGeneraion:
    def __init__(self, seed: int | None=None):
        #Seed là giá trị khởi tạo của bộ sinh số ngẫu nhiên.
        #Khi co seed => Lần nào chạy cũng ra cùng kết quả.
        #Các thí nghiệm được thực hiện trên tập mê cung cố định sinh bởi seed xác định. => same maze for all tests
        self.random = random.Random(seed)
    def generate(self, width, height) -> Maze:
        #Thuật toán Recursive Backtracking coi. ô lẻ = cell, ô chẵn = wall
        #=> biên luôn là tường, cell luôn ở vị trí lẻ, bước ±2 luôn hợp lệ
        #Đây là convention của perfect maze.
        if width%2 == 0:
            width += 1
        if height%2 == 0:
            height += 1
        maze = Maze(width,height)
        self._carve(Maze)
        maze.start = (1,1)
        maze.goal = find_farthest_cell(maze, maze.start)

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
