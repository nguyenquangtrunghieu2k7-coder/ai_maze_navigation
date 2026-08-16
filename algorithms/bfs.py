from collections import deque
from time import perf_counter

from core.maze import Maze
from core.path import PathResult

from .base import SearchAlgorithms

class BFS(SearchAlgorithms):
    def search(self,
               maze: Maze, start: tuple[int,int], goal: tuple[int,int]) -> PathResult:
        
        start_time = perf_counter()

        queue = deque([start])
        visited={start}
        parent={start: None}

        result = PathResult()

        while queue:
            current = queue.popleft()
            result.visited_order.append(current)
            result.expanded_nodes+=1

            if current == goal:
                result.path = self._reconstruct_path(parent, goal)
                break

            x,y = current
            for neighbor in maze.neighbors(x,y):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
        
        result.runtime_ms=(perf_counter() - start_time) * 1000

        return result
    def _reconstruct_path(self, parent: dict[tuple[int,int], tuple[int,int] | None], goal: tuple[int,int]):
        path = []
        current = goal
        path.append(current)

        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]
        path.reverse() 

        return path
    
