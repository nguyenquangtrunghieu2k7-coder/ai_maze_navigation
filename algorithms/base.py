#Đây là interface chung

from abc import ABC
from core.maze import Maze
from core.path import PathResult

class SearchAlgorithms(ABC):
    @abstractmethod
    def search(self, maze: Maze, start: tuple[int,int], goal: tuple[int,int]) -> PathResult:
        pass
