from input_reader import test_read_input, read_file
from genetics import Population
from pallet import Pallet
from draw import visualize_pallet
from box import Box 
import time
import random


import toml

class Settings:
    def __init__(self, toml_file):
        # Load the TOML file
        config = toml.load(toml_file)
        
        # Extract pallets settings
        self.pallet_size = config['pallets']['pallet-size']
        self.pallet_width = self.pallet_size['width']
        self.pallet_length = self.pallet_size['length']
        self.pallet_height = self.pallet_size['height']
        
        # Other settings
        self.visualize = config['pallets']['visualize']
        self.test_data = config['pallets']['test-data']
        self.data_path = config['pallets']['data-path']
        self.deterministic_rand = config['pallets']['deterministic-rand']
    
    def __repr__(self):
        return f"Settings(width={self.pallet_width}, length={self.pallet_length}, height={self.pallet_height}, visualize={self.visualize}, test_data={self.test_data}, data_path='{self.data_path}')"



def main():
    
    settings = Settings("default.toml")
    if settings.deterministic_rand:
        random.seed(2005)
    if settings.test_data:
        box_dimensions = test_read_input()  
    else:
        box_dimensions = read_file(settings.data_path) 
    
    # Берем размеры паллеты из настроек
    pallet_dimensions = (settings.pallet_width, settings.pallet_length, settings.pallet_height)
    
    boxes = [Box(id, d1, d2, d3) for id, d1, d2, d3 in box_dimensions]
    pallet = Pallet(0, 0, 0, *pallet_dimensions)
    start_time = time.perf_counter()
    population = Population(20, boxes, pallet_dimensions)
    population.evolve(50)
    
    best_chromosome = population.best_chromosome()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    

    # Укладка коробок по лучшей хромосоме
    unplaced_boxes = []
    for box, orientation in zip(best_chromosome.sequence, best_chromosome.orientations):
        added = pallet.try_add(box, orientation)  # Сохраняем результат попытки добавления
        
        
        if added:
            last_added = pallet.boxes[-1]  # Получаем последнюю добавленную коробку
        else:
            unplaced_boxes.append(box)
        
        if settings.visualize and added:
            visualize_pallet(pallet, last_added if added else None)
        
        

    for box in unplaced_boxes:
        for orientation in range(6):  
            added_unplased_boxes=pallet.try_add(box, orientation)
            if added_unplased_boxes:
                if settings.visualize :
                    last_added = pallet.boxes[-1]
                    visualize_pallet(pallet, last_added if added else None)
                break

    pallet.print_status()

    # Выводим значение функции приспособленности
    fitness_value = best_chromosome.fitness()
    print(f"\nФункция приспособленности (отношение объёма коробок к объёму паллеты): {fitness_value:.3f}")
    print(f"\nВремя выполнения алгоритма: {elapsed_time:.2f} секунд")
    
if __name__ == "__main__":
    main()