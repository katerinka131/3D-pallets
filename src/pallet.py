from box import Box
from typing import List, Dict, Tuple, Optional
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
        
        # Структуры для быстрого поиска минимальной высоты
        self.min_height = 0
        self.height_cells = defaultdict(list)
        for x in range(self.grid_length):
            for y in range(self.grid_width):
                self.height_cells[0].append((x, y))
    
    def try_add(self, box: Box, orientation: int) -> bool:
        box_length, box_width, box_height = box.get_orientations()[orientation]
        
        # Округляем размеры коробки вверх до 10 мм (1 клетка)
        box_grid_length = (box_length + self.cell_size - 1) // self.cell_size
        box_grid_width = (box_width + self.cell_size - 1) // self.cell_size
        
        
        
        # Если на минимальной высоте не нашли, ищем на других высотах
        for h in sorted(self.height_cells.keys()):
            
                
            # Снова сортируем по близости к углу
            sorted_cells = sorted(self.height_cells[h], key=lambda pos: (pos[0] + pos[1], pos[0], pos[1]))
            
            for x, y in sorted_cells:
                if (x + box_grid_length <= self.grid_length and 
                    y + box_grid_width <= self.grid_width and
                    np.all(self.height_map[x:x+box_grid_length, y:y+box_grid_width] <= h)):
                    # Размещаем первую подходящую (ближайшую к углу)
                    self._place_box(x, y, box_grid_length, box_grid_width, box_height, box)
                    return True
        
        return False

    def _place_box(self, x: int, y: int, 
                 grid_length: int, grid_width: int, 
                 height_mm: int, box: Box):
        """Размещает коробку и обновляет структуры данных."""
        old_height = self.height_map[x, y]
        new_height = old_height + height_mm
        
        # Обновляем карту высот
        self.height_map[x:x+grid_length, y:y+grid_width] = new_height
        
        # Обновляем структуры для быстрого поиска
        # Удаляем клетки из старых высот
        cells_to_remove = set()
        for xi in range(x, x + grid_length):
            for yi in range(y, y + grid_width):
                cells_to_remove.add((xi, yi))
        
        # Удаляем клетки из соответствующих списков высот
        for h in list(self.height_cells.keys()):
            if h < new_height:
                self.height_cells[h] = [cell for cell in self.height_cells[h] if cell not in cells_to_remove]
                if not self.height_cells[h]:
                    del self.height_cells[h]
        
        # Обновляем минимальную высоту
        if self.height_cells:
            self.min_height = min(self.height_cells.keys())
        else:
            self.min_height = new_height
        
        # Добавляем только граничные клетки новой области
        boundary_cells = set()
        for xi in range(x, x + grid_length):
            boundary_cells.add((xi, y))
            boundary_cells.add((xi, y + grid_width - 1))
        for yi in range(y, y + grid_width):
            boundary_cells.add((x, yi))
            boundary_cells.add((x + grid_length - 1, yi))
        
        for cell in boundary_cells:
            if (0 <= cell[0] < self.grid_length and 
                0 <= cell[1] < self.grid_width):
                self.height_cells[new_height].append(cell)
        
        # Сохраняем коробку (все координаты в мм)
        self.boxes.append({
            'box': box,
            'x': x * self.cell_size,
            'y': y * self.cell_size,
            'z': old_height,
            'length': grid_length * self.cell_size,
            'width': grid_width * self.cell_size,
            'height': height_mm
        })
        
        self.current_height = max(self.current_height, new_height)
    
    # Остальные методы остаются без изменений
    def occupied_volume(self) -> int:
        """Возвращает суммарный объем всех коробок на паллете."""
        return sum(box['box'].volume() for box in self.boxes)
    
    def total_volume(self) -> int:
        """Возвращает общий объем паллеты (длина × ширина × текущая высота)."""
        return self.length * self.width * self.current_height
    
    def utilization(self) -> float:
        """Возвращает коэффициент использования объема паллеты."""
        occupied = self.occupied_volume()
        total = self.total_volume()
        return occupied / total if total > 0 else 0.0
    
    def print_status(self):
        """Выводит текущее состояние паллеты."""
        print("\nТекущие коробки (занятые области):")
        for i, box_data in enumerate(self.boxes, start=1):
            box = box_data['box']
            x1 = box_data['x']
            y1 = box_data['y']
            z1 = box_data['z']
            x2 = x1 + box_data['length']
            y2 = y1 + box_data['width']
            z2 = z1 + box_data['height']
            
            print(f"  Коробка {box.id}: Левый нижний угол ({x1}, {y1}, {z1}), "
                f"Правый верхний угол ({x2}, {y2}, {z2})")
        
        print(f"\n=== Статус паллеты ===")
        print(f"Размеры паллеты: {self.length}x{self.width}x{self.current_height} мм")
        print(f"Количество коробок: {len(self.boxes)}")
        print(f"Занятый объем: {self.occupied_volume():,} мм³")
        print(f"Общий объем паллеты: {self.total_volume():,} мм³")
        print(f"Коэффициент заполнения: {self.utilization():.2%}")