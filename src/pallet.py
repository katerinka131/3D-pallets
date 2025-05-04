from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict

class Pallet:
    def __init__(self, length: int, width: int):
        self.length = length  # 1200 мм
        self.width = width    # 800 мм
        self.current_height = 0  # в мм
        self.boxes = []
        
        # Карта высот в миллиметрах (1 клетка = 10x10 мм)
        self.cell_size = 10
        self.grid_length = (length + self.cell_size - 1) // self.cell_size
        self.grid_width = (width + self.cell_size - 1) // self.cell_size
        self.height_map = np.zeros((self.grid_length, self.grid_width), dtype=np.int16)
        
        # Для хранения информации о дырах (свободных объемах)
        self.hole_map = np.zeros_like(self.height_map, dtype=np.int16)
        self.holes = defaultdict(list)  # {высота: [(x1,y1,x2,y2)]}

    def try_add(self, box, orientation: int) -> bool:
        box_length, box_width, box_height = box.get_orientations()[orientation]
        box_grid_length = (box_length + self.cell_size - 1) // self.cell_size
        box_grid_width = (box_width + self.cell_size - 1) // self.cell_size
        
        # 1. Попробовать разместить в существующих дырах
        if self._try_place_in_holes(box_grid_length, box_grid_width, box_height, box):
            return True
            
        # 2. Стандартное размещение по минимальной высоте
        return self._try_place_standard(box_grid_length, box_grid_width, box_height, box)

    def _try_place_in_holes(self, box_grid_length: int, box_grid_width: int, 
                          box_height: int, box) -> bool:
        """Пытается разместить коробку в существующих дырах"""
        # Сортируем дыры по высоте (от самых низких)
        for h in sorted(self.holes.keys()):
            for (x1, y1, x2, y2) in self.holes[h]:
                # Проверяем, помещается ли коробка в эту дыру
                if (x2 - x1 >= box_grid_length and 
                    y2 - y1 >= box_grid_width and 
                    h >= box_height):
                    
                    # Ищем конкретное положение внутри дыры
                    for x in range(x1, x2 - box_grid_length + 1):
                        for y in range(y1, y2 - box_grid_width + 1):
                            # Проверяем, что область свободна
                            if np.all(self.height_map[x:x+box_grid_length, y:y+box_grid_width] <= h - box_height):
                                self._place_box(x, y, box_grid_length, box_grid_width, box_height, box)
                                self._update_holes()
                                return True
        return False

    def _try_place_standard(self, box_grid_length: int, box_grid_width: int,
                          box_height: int, box) -> bool:
        """Стандартный алгоритм размещения с минимальной высотой"""
        min_height = float('inf')
        best_positions = []
        
        for x in range(self.grid_length - box_grid_length + 1):
            for y in range(self.grid_width - box_grid_width + 1):
                area_height = np.max(self.height_map[x:x+box_grid_length, y:y+box_grid_width])
                
                if area_height < min_height:
                    min_height = area_height
                    best_positions = [(x, y)]
                elif area_height == min_height:
                    best_positions.append((x, y))
        
        if not best_positions:
            print(f'Не удалось разместить коробку {box.id}')
            return False
            
        best_x, best_y = min(best_positions, key=lambda pos: pos[0]**2 + pos[1]**2)
        self._place_box(best_x, best_y, box_grid_length, box_grid_width, box_height, box)
        self._update_holes()
        return True

    def _place_box(self, x: int, y: int, 
                 grid_length: int, grid_width: int, 
                 height_mm: int, box) -> None:
        """Размещает коробку и обновляет карту высот"""
        base_height = np.max(self.height_map[x:x+grid_length, y:y+grid_width])
        new_height = base_height + height_mm
        
        self.height_map[x:x+grid_length, y:y+grid_width] = new_height
        self.current_height = max(self.current_height, new_height)
        
        self.boxes.append({
            'box': box,
            'x': x * self.cell_size,
            'y': y * self.cell_size,
            'z': base_height,
            'length': grid_length * self.cell_size,
            'width': grid_width * self.cell_size,
            'height': height_mm
        })

    def _update_holes(self):
        """Обновляет информацию о дырах после размещения коробки"""
        self.holes = defaultdict(list)
        visited = np.zeros_like(self.height_map, dtype=bool)
        
        for x in range(self.grid_length):
            for y in range(self.grid_width):
                if not visited[x, y]:
                    current_height = self.height_map[x, y]
                    
                    # Находим максимальную прямоугольную область с такой же высотой
                    max_w = 1
                    while y + max_w < self.grid_width and self.height_map[x, y + max_w] == current_height:
                        max_w += 1
                        
                    max_h = 1
                    while x + max_h < self.grid_length and np.all(
                        self.height_map[x + max_h, y:y + max_w] == current_height):
                        max_h += 1
                    
                    visited[x:x+max_h, y:y+max_w] = True
                    
                    # Находим минимальную высоту над этой областью
                    if x + max_h < self.grid_length:
                        h_above = np.min(self.height_map[x + max_h, y:y + max_w])
                        if h_above > current_height:
                            self.holes[h_above - current_height].append((x, y, x + max_h, y + max_w))

    def occupied_volume(self) -> int:
        return sum(box['length'] * box['width'] * box['height'] for box in self.boxes)
    
    def total_volume(self) -> int:
        return self.length * self.width * self.current_height
    
    def utilization(self) -> float:
        occupied = self.occupied_volume()
        total = self.total_volume()
        return min(occupied / total if total > 0 else 0.0, 1.0)  # Гарантируем не более 100%

    def print_status(self):
        print("\nТекущие коробки:")
        for box_data in self.boxes:
            box = box_data['box']
            x1, y1, z1 = box_data['x'], box_data['y'], box_data['z']
            x2 = x1 + box_data['length']
            y2 = y1 + box_data['width']
            z2 = z1 + box_data['height']
            
            print(f"Коробка {box.id}: ({x1},{y1},{z1}) -> ({x2},{y2},{z2})")
        
        print(f"\nСтатус паллеты {self.length}x{self.width}x{self.current_height} мм:")
        print(f"Коробок: {len(self.boxes)}")
        print(f"Заполнение: {self.utilization():.2%}")
        print(f"Обнаружено дыр: {sum(len(v) for v in self.holes.values())}")

    def get_box_positions(self) -> List[Dict]:
        return [{
            'id': box['box'].id,
            'x': box['x'],
            'y': box['y'], 
            'z': box['z'],
            'x2': box['x'] + box['length'],
            'y2': box['y'] + box['width'],
            'z2': box['z'] + box['height']
        } for box in self.boxes]