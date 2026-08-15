from dataclasses import dataclass, field

@dataclass
class PathReSult:
    #default_factory=list tạo list mới cho mỗi object.
    path: list[tuple[int, int]] = field(default_factory = list) #đường đi cuối cùng từ start đến goal (≤ visited_order)
    path_cost: float = 0.0
    expanded_nodes: int = 0 #Mỗi lần lấy một node ra để xử lý hàng xóm thì expanded_nodes += 1.
    runtime_ms: float = 0.0
    visited_order: list[tuple[int, int]] = field(default_factory = list) #tất cả node thuật toán đã xử lý 

    #property la decorator, Nó biến method thành thuộc tính chỉ đọc.
    #VD: a.get_x() => a.x (khong can ())
    @property
    def path_length(self) -> int: #tinh so buoc
        return max(0, len(self.path) -1 )
    @property
    def found(self) -> bool:
        return len(self.path) > 0
    
