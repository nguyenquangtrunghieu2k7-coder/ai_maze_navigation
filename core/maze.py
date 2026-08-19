'''
Maze có các trách nhiệm sau:
-lưu grid
-biết start/goal
-kiểm tra hợp lệ
-trả về hàng xóm
-trả về chi phí terrain
-hỗ trợ gán terrain
'''

from core.cell import Cell
from core.terrain import Terrain, get_cost, get_speed

class Maze:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.grid = [[Cell(x,y,walkable = False) for x in range(width)]
                     for y in range(height)]
        self.start = (1,1)
        self.goal = (width -2, height -2)
    ''' 
    dung grid[y][x] vi:
    tọa độ Descartes (x, y) khác với chỉ số ma trận (row, col)
    VD toa do (1,2) => ve hinh ra => hang 2, cot 1 => grid[2][1]
    => Đây là convention của Python
    '''
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x,y) and self.grid[y][x].walkable
    def get_cell(self, x: int, y: int) -> Cell:
        return self.grid[y][x]
    def set_walkable(self, x: int, y: int, walkable: bool = True):
        if self.in_bounds(x, y):
            self.grid[y][x].walkable = walkable
    def set_terrain(self, x: int, y: int, terrain: Terrain):
        if self.is_walkable(x,y):
            self.grid[y][x].terrain = terrain
    def terrain_cost(self, x: int, y: int) -> float: #encapsulation, Nó không cần biết TerrainInfo
        return get_cost(self.grid[y][x].terrain)
    def neighbors(self, x: int, y: int): #Khong "-> Cell" vi Tuple hash nhanh hơn object
        directions = [(1,0), (-1,0), (0, 1), (0,-1)]
        for dx,dy in directions:
            nx = x+dx
            ny= y+dy

            if self.is_walkable(nx,ny):
                yield (nx,ny)
                #Khi A* chạy: for nx, ny in maze.neighbors(x, y): nó sẽ lấy từng yielded neighbor một.
    def reset(self):
        for row in self.grid:
            for cell in row:
                cell.walkable = False
                cell.terrain = Terrain.ROAD
    def set_start(self, x: int, y: int):
        if self.is_walkable(x, y):
            self.start = (x, y)

    def set_goal(self, x: int, y: int):
        if self.is_walkable(x, y):
            self.goal = (x, y)
    def get_elevation(self, x: int, y: int) -> float:
        return self.grid[y][x].elevation
    def get_slope(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> float:
        elevation_1 = self.get_elevation(x1, y1)
        elevation_2 = self.get_elevation(x2, y2)

        return elevation_2 - elevation_1
    def get_speed(self, x: int, y: int) -> float:
        return get_speed(self.grid[y][x].terrain)
    def __repr__(self):
        return f"Maze({self.width}x{self.height})"