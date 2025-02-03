import csv
from box import Box

def test_read_input():
    palleta = [10, 9, 7]
    boxes = [[33, 1, 2, 3], [42, 1, 6, 7], [43, 1, 2, 3], [34, 5, 3, 2], [35, 2, 2, 3], [36, 5, 7, 6], [37, 3, 2, 1], [38, 4, 3, 2], [39, 1, 2, 4], [40, 4, 5, 7], [41, 2, 5, 7], [42, 1, 2, 4]]
    return boxes, palleta

def read_file(file_path):
    boxes = []
    seen_boxes = set()  # Множество для отслеживания уникальных размеров коробок

    with open(file_path, newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            sku, quantity, length, width, height, weight, strength, aisle, caustic = row

            length, width, height = int(length), int(width), int(height)

            box_size = (length, width, height)
            if box_size not in seen_boxes:
                for _ in range(int(quantity)): 
                    boxes.append(Box(sku, length, width, height))
                seen_boxes.add(box_size)  

    return boxes





                                                           
