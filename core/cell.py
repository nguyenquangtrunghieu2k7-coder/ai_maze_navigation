from dataclasses import dataclass
from .terrain import Terrain

#dataclass để viết các class chủ yếu dùng để chứa dữ liệu (data model)
#không phải tự viết constructor và các hàm cơ bản
#vẫn là class bình thường, chỉ là Python tự sinh một số phương thức cho mình
#Python sẽ tự tạo: __init__, __repr__, __eq__
@dataclass(slots=True)
#slots =True => Object chỉ được phép có đúng các thuộc tính đã khai báo
# ít RAM hơn, truy cập thuộc tính nhanh hơn
class Cell:
    x: int
    y: int
    walkable: bool = True
    terrain: Terrain = Terrain.ROAD
    @property
    def pos(self) -> tuple[int,int]:
        return (self.x, self.y)
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    def __repr__(self) -> str:
        #biểu diễn object để debug
        return (
            f"Cell(x={self.x}, y={self.y}, "
            f"walkable={self.walkable}, terrain= {self.terrain})"
        )
