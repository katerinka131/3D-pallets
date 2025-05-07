from typing import List, Dict, Tuple
import numpy as np

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
    
    def try_add(self, box, orientation: int, is_initial_population: bool = False) -> bool:
        """Размещает коробку, выбирая позицию и ориентацию (если is_initial_population=True)"""
        if is_initial_population and orientation == -1:
            # Для начальной популяции пробуем обе ориентации и выбираем лучшую
            best_fit = None
            best_height_increase = float('inf')
            
            for orien in [0, 1]:
                box_length, box_width, box_height = box.get_orientations()[orien]
                box_grid_length = (box_length + self.cell_size - 1) // self.cell_size
                box_grid_width = (box_width + self.cell_size - 1) // self.cell_size
                
                x, y, area_height = self._find_best_position(box_grid_length, box_grid_width)
                if x is not None and area_height < best_height_increase:
                    best_height_increase = area_height
                    best_fit = (x, y, box_grid_length, box_grid_width, box_height, orien)
            
            if best_fit is not None:
                x, y, gl, gw, h, orien = best_fit
                self._place_box(x, y, gl, gw, h, box)
                return True, orien  # Возвращаем также выбранную ориентацию
            return False, None
        else:
            # Стандартное поведение для последующих поколений
            if orientation not in [0, 1]:
                orientation = 0  # Защита от неверных ориентаций
                
            box_length, box_width, box_height = box.get_orientations()[orientation]
            box_grid_length = (box_length + self.cell_size - 1) // self.cell_size
            box_grid_width = (box_width + self.cell_size - 1) // self.cell_size
            
            x, y, area_height = self._find_best_position(box_grid_length, box_grid_width)
            if x is not None:
                self._place_box(x, y, box_grid_length, box_grid_width, box_height, box)
                return True, orientation
            return False, None

    def _find_best_position(self, box_grid_length: int, box_grid_width: int) -> Tuple[int, int, int]:
        """Находит лучшую позицию для размещения коробки с заданными размерами"""
        min_height = float('inf')
        candidate_positions = []
        
        for x in range(self.grid_length - box_grid_length + 1):
            for y in range(self.grid_width - box_grid_width + 1):
                area_height = np.max(self.height_map[x:x+box_grid_length, y:y+box_grid_width])
                remaining_right = x + box_grid_length
                remaining_top = y + box_grid_width
                remaining_space = remaining_right + remaining_top
                
                candidate_score = (area_height, remaining_space, x + y)
                
                if area_height < min_height:
                    min_height = area_height
                    candidate_positions = [(x, y, candidate_score)]
                elif area_height == min_height:
                    candidate_positions.append((x, y, candidate_score))
        
        if not candidate_positions:
            return (None, None, None)
        
        best_x, best_y, _ = min(candidate_positions, key=lambda pos: pos[2])
        return (best_x, best_y, min_height)

    def _place_box(self, x: int, y: int, 
                 grid_length: int, grid_width: int, 
                 height_mm: int, box) -> None:
        """Размещает коробку и обновляет карту высот"""
        base_height = np.max(self.height_map[x:x+grid_length, y:y+grid_width])
        new_height = base_height + height_mm
        
        self.height_map[x:x+grid_length, y:y+grid_width] = new_height
        
        self.boxes.append({
            'box': box,
            'x': x * self.cell_size,
            'y': y * self.cell_size,
            'z': base_height,
            'length': grid_length * self.cell_size,
            'width': grid_width * self.cell_size,
            'height': height_mm
        })
        
        self.current_height = max(self.current_height, new_height)
    
    def occupied_volume(self) -> int:
        return sum(box['length'] * box['width'] * box['height'] for box in self.boxes)
    
    def total_volume(self) -> int:
        return self.length * self.width * self.current_height
    
    def utilization(self) -> float:
        occupied = self.occupied_volume()
        total = self.total_volume()
        return occupied / total if total > 0 else 0.0
    
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