import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

def draw_box(ax, x1, y1, z1, x2, y2, z2, color="yellow", alpha=0.3):  # Установлен alpha=0.3 для прозрачности
    """Рисует коробку или сегмент в 3D, правильно отображая грани по порядку."""
    vertices = [
        [(x1, y1, z1), (x1, y2, z1), (x2, y2, z1), (x2, y1, z1)],  # Нижняя грань
        [(x1, y1, z2), (x1, y2, z2), (x2, y2, z2), (x2, y1, z2)],  # Верхняя грань
        [(x1, y1, z1), (x1, y1, z2), (x2, y1, z2), (x2, y1, z1)],  # Передняя грань
        [(x1, y2, z1), (x1, y2, z2), (x2, y2, z2), (x2, y2, z1)],  # Задняя грань
        [(x1, y1, z1), (x1, y1, z2), (x1, y2, z2), (x1, y2, z1)],  # Левая грань
        [(x2, y1, z1), (x2, y1, z2), (x2, y2, z2), (x2, y2, z1)],  # Правая грань
    ]
    # Рисуем в том порядке, в котором нужно отображать, начиная с передних граней
    box = Poly3DCollection(vertices, alpha=alpha, edgecolor="black", facecolor=color)
    ax.add_collection3d(box)

def center_of_mass(box):
    """Возвращает координаты центра масс коробки (по средним значениям координат)."""
    _, x1, y1, z1, x2, y2, z2 = box  # Игнорируем первый элемент (id)
    return np.array([(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2])

def distance_from_camera(center, camera_position=(10, 0, 10)):
    """Вычисляем расстояние от центра масс коробки до камеры (точки (0, 0, 0))."""
    return np.linalg.norm(center - np.array(camera_position))

def visualize_pallet(pallet, last_added_box=None, show_segments=False):
    """Визуализирует паллету с коробками и, опционально, свободными сегментами.
    Последняя добавленная коробка отображается зеленым цветом."""
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_box_aspect([1, 1, 1])  # Сохраняем пропорции

    # Сортируем коробки по расстоянию от камеры (центр масс)
    sorted_boxes = sorted(pallet.boxes, key=lambda box: distance_from_camera(center_of_mass(box)))

    # Отображаем занятые коробки
    for box in sorted_boxes:
        # Если это последняя добавленная коробка, рисуем зеленым
        if last_added_box is not None and box[0] == last_added_box[0]:  # Сравниваем по id
            draw_box(ax, *box[1:], color="green", alpha=0.4)  # Более насыщенный зеленый для новой коробки
        else:
            draw_box(ax, *box[1:], color="red", alpha=0.3)

    # Отображаем свободные сегменты, если show_segments=True
    if show_segments:
        for segment in pallet.subpallets:
            draw_box(ax, *segment, color="blue", alpha=0.1)  # Изменил цвет сегментов на синий для различия

    # Настройки осей
    ax.set_xlim(0, pallet.x2)
    ax.set_ylim(0, pallet.y2)
    ax.set_zlim(0, pallet.z2)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    plt.show()