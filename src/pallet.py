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
    
    def try_add(self, box, orientation: int) -> bool:
        """Размещает коробку, выбирая позицию с минимальной высотой и минимальным остаточным пространством"""
        box_length, box_width, box_height = box.get_orientations()[orientation]
        box_grid_length = (box_length + self.cell_size - 1) // self.cell_size
        box_grid_width = (box_width + self.cell_size - 1) // self.cell_size
        
        min_height = float('inf')
        candidate_positions = []
        
        # Перебираем все возможные позиции
        for x in range(self.grid_length - box_grid_length + 1):
            for y in range(self.grid_width - box_grid_width + 1):
                # Находим максимальную высоту в области размещения
                area_height = np.max(self.height_map[x:x+box_grid_length, y:y+box_grid_width])
                
                # Рассчитываем остаточное пространство справа и сверху
                remaining_right = self.grid_length - (x + box_grid_length)
                remaining_top = self.grid_width - (y + box_grid_width)
                remaining_space = remaining_right + remaining_top
                
                # Критерии выбора:
                # 1. Минимальная высота размещения
                # 2. Минимальное остаточное пространство
                # 3. Ближе к углу (0,0)
                candidate_score = (area_height, remaining_space, x + y)
                
                if area_height < min_height:
                    min_height = area_height
                    candidate_positions = [(x, y, candidate_score)]
                elif area_height == min_height:
                    candidate_positions.append((x, y, candidate_score))
        
        if not candidate_positions:
            print(f'Не удалось разместить коробку {box.id}')
            return False
        
        # Выбираем позицию с лучшими показателями
        best_x, best_y, _ = min(candidate_positions, key=lambda pos: pos[2])
        
        # Размещаем коробку
        self._place_box(best_x, best_y, box_grid_length, box_grid_width, box_height, box)
        return True

    def _place_box(self, x: int, y: int, 
                 grid_length: int, grid_width: int, 
                 height_mm: int, box) -> None:
        """Размещает коробку и обновляет карту высот"""
        base_height = np.max(self.height_map[x:x+grid_length, y:y+grid_width])
        new_height = base_height + height_mm
        
        # Обновляем карту высот
        self.height_map[x:x+grid_length, y:y+grid_width] = new_height
        
        # Сохраняем информацию о коробке
        self.boxes.append({
            'box': box,
            'x': x * self.cell_size,
            'y': y * self.cell_size,
            'z': base_height,
            'length': grid_length * self.cell_size,
            'width': grid_width * self.cell_size,
            'height': height_mm
        })
        
        # Обновляем максимальную высоту
        self.current_height = max(self.current_height, new_height)
    
    # Остальные методы без изменений
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