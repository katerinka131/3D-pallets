import csv
from box import Box

def test_read_input():
    
    boxes = [
    [1, 600, 500, 750], 
    [1, 600, 500, 750],
    [2, 400, 500, 750], 
    [3, 200, 500, 750], 
    [4, 600, 500, 750], 
    [5, 400, 500, 750], 
    [6, 200, 500, 750], 
    [7, 600, 500, 750], 
    [8, 400, 500, 750], 
    [9, 200, 500, 750], 
    [10, 600, 500, 750], 
    [11, 400, 500, 750], 
    [12, 200, 500, 750]
]

    # boxes = [[1, 1, 2, 3], [2, 1, 6, 7], [3, 1, 2, 3], [4, 5, 3, 2], [5, 2, 2, 3], [6, 5, 7, 6], [7, 3, 2, 1], [8, 4, 3, 2], [9, 1, 2, 4], [10, 4, 5, 7], [11, 2, 5, 7], [12, 1, 2, 4]]
    return boxes


def read_file(file_path):
    boxes = []
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        next(reader)
          # Пропускаем заголовок
        for row in reader:
            sku = int(row[0])
            quantity = int(row[1])
            length = int(row[2])
            width = int(row[3])
            height = int(row[4])
            
            for _ in range(quantity):
                boxes.append([sku, length, width, height])
        
    
    return boxes


                                                           
