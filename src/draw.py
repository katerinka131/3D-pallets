import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

def draw_box(ax, box_data, color="yellow", alpha=0.3):
    """Рисует коробку в 3D пространстве."""
    x = box_data['x']
    y = box_data['y']
    z = box_data['z']
    length = box_data['length']
    width = box_data['width']
    height = box_data['height']
    
    # Координаты вершин коробки
    x1, x2 = x, x + length
    y1, y2 = y, y + width
    z1, z2 = z, z + height
    
    vertices = [
        [(x1, y1, z1), (x1, y2, z1), (x2, y2, z1), (x2, y1, z1)],  # Нижняя грань
        [(x1, y1, z2), (x1, y2, z2), (x2, y2, z2), (x2, y1, z2)],  # Верхняя грань
        [(x1, y1, z1), (x1, y1, z2), (x2, y1, z2), (x2, y1, z1)],  # Передняя грань
        [(x1, y2, z1), (x1, y2, z2), (x2, y2, z2), (x2, y2, z1)],  # Задняя грань
        [(x1, y1, z1), (x1, y1, z2), (x1, y2, z2), (x1, y2, z1)],  # Левая грань
        [(x2, y1, z1), (x2, y1, z2), (x2, y2, z2), (x2, y2, z1)],  # Правая грань
    ]
    
    box = Poly3DCollection(vertices, alpha=alpha, edgecolor="black", facecolor=color)
    ax.add_collection3d(box)

def visualize_pallet(pallet, last_added_box=None):
    """Визуализирует паллету с коробками.
    
    Args:
        pallet: Объект класса Pallet
        last_added_box: Последняя добавленная коробка (будет выделена цветом)
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    
    # Устанавливаем пропорции осей
    ax.set_box_aspect([pallet.length, pallet.width, pallet.current_height if pallet.current_height > 0 else 1])
    
    # Рисуем все коробки
    for box in pallet.boxes:
        # Если это последняя добавленная коробка, рисуем зеленым
        if last_added_box is not None and box['box'].id == last_added_box['box'].id:
            draw_box(ax, box, color="green", alpha=0.7)
        else:
            draw_box(ax, box, color="blue", alpha=0.3)
    
    # Настройка осей и подписей
    ax.set_xlim(0, pallet.length)
    ax.set_ylim(0, pallet.width)
    ax.set_zlim(0, pallet.current_height if pallet.current_height > 0 else 1)
    
    ax.set_xlabel("Длина (мм)")
    ax.set_ylabel("Ширина (мм)")
    ax.set_zlabel("Высота (мм)")
    
    plt.title("3D визуализация паллеты")
    plt.tight_layout()
    plt.show()