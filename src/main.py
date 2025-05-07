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
        config = toml.load(toml_file)
        self.pallet_size = config['pallets']['pallet-size']
        self.pallet_width = self.pallet_size['width']
        self.pallet_length = self.pallet_size['length']
        self.pallet_height = 0
        
        self.visualize = config['pallets']['visualize']
        self.test_data = config['pallets']['test-data']
        self.data_path = config['pallets']['data-path']
        self.deterministic_rand = config['pallets']['deterministic-rand']
    
    def __repr__(self):
        return f"Settings(width={self.pallet_width}, length={self.pallet_length}, height=unlimited, visualize={self.visualize}, test_data={self.test_data}, data_path='{self.data_path}')"

def main():
    settings = Settings("default.toml")
    if settings.deterministic_rand:
        random.seed(2005)
    
    if settings.test_data:
        box_dimensions = test_read_input()  
    else:
        box_dimensions = read_file(settings.data_path) 
    boxes = [Box(id, d1, d2, d3) for id, d1, d2, d3 in box_dimensions]
    pallet = Pallet(settings.pallet_length, settings.pallet_width)
    
    start_time = time.perf_counter()
    
    pallet_dimensions = (settings.pallet_length, settings.pallet_width, float('inf'))
    population = Population(20, boxes, pallet_dimensions)
    population.evolve(200)
    
    best_chromosome = population.best_chromosome()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    
    # Укладка коробок по лучшей хромосоме
    for box, orientation in zip(best_chromosome.sequence, best_chromosome.orientations):
        pallet.try_add(box, orientation)
        
        if settings.visualize:
            last_added = pallet.boxes[-1] if pallet.boxes else None
            visualize_pallet(pallet, last_added)

    pallet.print_status()
    print(f"\nФункция приспособленности: {best_chromosome.fitness():.3f}")
    print(f"Общая высота упаковки: {pallet.current_height} мм")
    print(f"Заполнение объема: {pallet.occupied_volume() / (pallet.length * pallet.width * pallet.current_height):.2%}")
    print(f"\nВремя выполнения алгоритма: {elapsed_time:.2f} секунд")
    
if __name__ == "__main__":
    main()