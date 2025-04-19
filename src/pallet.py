from box import Box
import math
from typing import List, Tuple

count = 0


class Pallet:
    def __init__(self, x1, y1, z1, x2, y2, z2):
        self.x1, self.y1, self.z1 = x1, y1, z1
        self.x2, self.y2, self.z2 = x2, y2, z2
        self.subpallets = [(x1, y1, z1, x2, y2, z2)]
        self.boxes = []
    
    def try_add(self, box: Box, orientation: int) -> bool:
        # Генерируем размеры коробки с учётом ориентации
        dims = self._generate_orientations(box)[orientation]
        
        best_fit = min(
            filter(
                lambda subpallet: (
                    subpallet[3] - subpallet[0] >= dims[0]
                    and subpallet[4] - subpallet[1] >= dims[1]
                    and subpallet[5] - subpallet[2] >= dims[2]
                ),
                self.subpallets,
            ),
            key=(lambda x: math.sqrt(x[0] ** 2 + x[1] ** 2 + x[2] ** 2)),
            default=None
        )

        if best_fit:
            x1, y1, z1, x2, y2, z2 = best_fit
            x2 = x1 + dims[0]
            y2 = y1 + dims[1]
            z2 = z1 + dims[2]
            self.boxes.append((box.id, x1, y1, z1, x2, y2, z2))
            self._update_subpallets(x1, y1, z1, x2, y2, z2)
            return True
        return False

    def _generate_orientations(self, box: Box) -> List[Tuple[int, int, int]]:
        # Генерируем все возможные ориентации коробки
        return [
            (box.d1, box.d2, box.d3),
            (box.d1, box.d3, box.d2),
            (box.d2, box.d1, box.d3),
            (box.d2, box.d3, box.d1),
            (box.d3, box.d1, box.d2),
            (box.d3, box.d2, box.d1),
        ]

    def _update_subpallets(self, bx1, by1, bz1, bx2, by2, bz2):
        
        new_subpallets = []
        for sx1, sy1, sz1, sx2, sy2, sz2 in self.subpallets:
            if not (
                bx1 >= sx2
                or bx2 <= sx1
                or by1 >= sy2
                or by2 <= sy1
                or bz1 >= sz2
                or bz2 <= sz1
            ):
                if sx1 < bx1:
                    new_subpallets.append((sx1, sy1, sz1, bx1, sy2, sz2))
                if bx2 < sx2:
                    new_subpallets.append((bx2, sy1, sz1, sx2, sy2, sz2))
                if sy1 < by1:
                    new_subpallets.append((sx1, sy1, sz1, sx2, by1, sz2))
                if by2 < sy2:
                    new_subpallets.append((sx1, by2, sz1, sx2, sy2, sz2))
                if sz1 < bz1:
                    new_subpallets.append((sx1, sy1, sz1, sx2, sy2, bz1))
                if bz2 < sz2:
                    new_subpallets.append((sx1, sy1, bz2, sx2, sy2, sz2))
            else:
                new_subpallets.append((sx1, sy1, sz1, sx2, sy2, sz2))
        self.subpallets = new_subpallets

    def occupied_volume(self) -> int:
        # Считаем объём всех уложенных коробок
        return sum(
            (x2 - x1) * (y2 - y1) * (z2 - z1)
            for _, x1, y1, z1, x2, y2, z2 in self.boxes
        )

    def total_volume(self) -> int:
        # Считаем общий объём паллеты
        return (self.x2 - self.x1) * (self.y2 - self.y1) * (self.z2 - self.z1)

    def print_status(self):
        # Выводим только коробки (без сегментов)
        print("\nТекущие коробки (занятые области):")
        for i, (id, bx1, by1, bz1, bx2, by2, bz2) in enumerate(self.boxes, start=1):
            print(f"  Коробка {id}: ({bx1}, {by1}, {bz1}) -> ({bx2}, {by2}, {bz2})")
