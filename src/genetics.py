import random
import os
import psutil
import logging
from pallet import Pallet
from box import Box
from typing import List, Tuple
import concurrent.futures
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ga_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Chromosome:
    def __init__(self, boxes: List[Box], pallet_dimensions: Tuple[int, int, int], sorted=False):
        self.boxes = boxes
        self.pallet_dimensions = pallet_dimensions
        if sorted:
            self.sequence = boxes[:]  
            
        else:
            self.sequence = random.sample(boxes, len(boxes))  
            

        self.orientations = [random.choice([0, 1, 2, 3, 4, 5]) for _ in range(len(boxes))]
        

    def __repr__(self):
        box_ids = [box.id for box in self.sequence]
        return f"Chromosome(box_ids={box_ids}, orientations={self.orientations})"
    
    def fitness(self) -> float:
        logger.debug(f"Calculating fitness for chromosome {id(self)}")
        pallet = Pallet(0, 0, 0, *self.pallet_dimensions)
        unplaced_boxes = []
        
        for box, orientation in zip(self.sequence, self.orientations):
            if not pallet.try_add(box, orientation):
                unplaced_boxes.append(box)

        for box in unplaced_boxes:
            for orientation in range(6):  
                pallet.try_add(box, orientation)
        fitness = pallet.occupied_volume() / pallet.total_volume()
        print(f"|")
        return fitness
            
        

    def mutate(self):
        
        num_boxes = len(self.sequence)

        # Меняем ориентации у 10% коробок
        mutations = num_boxes // 10 + 1
        for _ in range(mutations):  
            idx = random.randint(0, num_boxes - 1)
            old_orientation = self.orientations[idx]
            self.orientations[idx] = random.choice([0, 1, 2, 3, 4, 5])
            

        # Переставляем 5% коробок местами
        num_swaps = max(1, num_boxes // 20)
        swap_indices = random.sample(range(num_boxes), num_swaps * 2)
        for i in range(0, len(swap_indices), 2):
            idx1, idx2 = swap_indices[i], swap_indices[i+1]
            self.sequence[idx1], self.sequence[idx2] = self.sequence[idx2], self.sequence[idx1]
            self.orientations[idx1], self.orientations[idx2] = self.orientations[idx2], self.orientations[idx1]
    

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        logger.debug(f"Crossover between {id(self)} and {id(other)}")
        child = Chromosome(self.boxes, self.pallet_dimensions)
        split = random.randint(1, len(self.sequence) - 1)
        
        child.sequence = self.sequence[:split]
        child.orientations = self.orientations[:split]
        
        for i, box in enumerate(other.sequence):
            if box not in child.sequence:
                child.sequence.append(box)
                child.orientations.append(other.orientations[i])
        
        logger.debug(f"Created child chromosome {id(child)} with {len(child.sequence)} boxes")
        
        return child
    
    def crossover_ox(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome(self.boxes, self.pallet_dimensions)
        size = len(self.sequence)
        point1 = random.randint(0, size - 2)
        point2 = random.randint(point1 + 1, size - 1)
    
        # Копируем сегмент из родителя 1
        segment = self.sequence[point1:point2]
        segment_orient = self.orientations[point1:point2]
        
        # Добавляем остальные элементы из родителя 2, сохраняя порядок
        remaining_boxes = [box for box in other.sequence if box not in segment]
        remaining_orient = [
            other.orientations[i] 
            for i, box in enumerate(other.sequence) 
            if box not in segment
        ]
        
        # Собираем ребёнка
        child.sequence = remaining_boxes[:point1] + segment + remaining_boxes[point1:]
        child.orientations = remaining_orient[:point1] + segment_orient + remaining_orient[point1:]
        
        return child

class Population:
    def __init__(self, size: int, boxes: List[Box], pallet_dimensions: Tuple[int, int, int]):
        self.start_time = datetime.now()
        logger.info(f"Initializing population with {size} chromosomes at {self.start_time}")
        
        self.chromosomes = []
        sorted_boxes = sorted(boxes, key=lambda box: box.volume(), reverse=True)
        logger.info(f"Total boxes: {len(boxes)}, sorted by volume")

        for _ in range(size // 2):
            chromosome = Chromosome(sorted_boxes, pallet_dimensions, sorted=True)
            self.chromosomes.append(chromosome)
            logger.debug(f"Created sorted chromosome {id(chromosome)}")

        # Вторая половина - случайные
        for _ in range(size - len(self.chromosomes)):  
            chromosome = Chromosome(boxes, pallet_dimensions)
            self.chromosomes.append(chromosome)
            logger.debug(f"Created random chromosome {id(chromosome)}")

        self.fitness_cache = dict()
        logger.info(f"Population initialized with {len(self.chromosomes)} chromosomes")
        

    

    def evolve(self, generations: int):
        logger.info(f"Starting evolution for {generations} generations")
        
        for gen in range(generations):
            gen_start_time = datetime.now()
            logger.info(f"\n================================ Generation {gen + 1}/{generations} ==============================")
            
            # Вычисление fitness (с использованием кэша)
            logger.info("Calculating fitness values...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    fitness_values = list(executor.map(self.cached_fitness, self.chromosomes))
                logger.info(f"Fitness calculation completed for {len(fitness_values)} chromosomes")
            except Exception as e:
                logger.error(f"Error during fitness calculation: {str(e)}")
                raise
            
            # Отбор лучших хромосом
            logger.info("Selecting best chromosomes...")
            sorted_chromosomes = sorted(zip(fitness_values, self.chromosomes), 
                                  key=lambda x: x[0], reverse=True)
            new_population = [c for _, c in sorted_chromosomes[:len(self.chromosomes) // 2]]
            
            logger.info(f"Selected {len(new_population)} best chromosomes. "
                      f"Best fitness: {sorted_chromosomes[0][0]:.4f}, "
                      f"Worst kept: {sorted_chromosomes[len(new_population)-1][0]:.4f}")

            # Очистка кэша ТОЛЬКО для удалённых хромосом
            logger.info("Cleaning fitness cache...")
            remaining_chromosomes = set(new_population)
            before_cache_size = len(self.get_fitness_cache())
            self.fitness_cache = {
                chrom: fitness 
                for chrom, fitness in self.fitness_cache.items() 
                if chrom in remaining_chromosomes
            }
            logger.info(f"Cache cleaned: {before_cache_size} -> {len(self.fitness_cache)} entries")

            # Создание нового поколения (мутация + кроссовер)
            logger.info("Creating new generation...")
            new_generation = []
            
            while len(new_generation) < len(new_population):
                parent1, parent2 = random.sample(new_population, 2)
                child = parent1.crossover_ox(parent2)
                if random.random() < 0.5: 
                    
                    child.mutate()
                
                new_generation.append(child)
                logger.debug(f"Created child chromosome {id(child)}")
            
            logger.info(f"Created {len(new_generation)} new chromosomes")

            self.chromosomes = new_population + new_generation
            logger.info(f"New population size: {len(self.chromosomes)} chromosomes")
            
            
            gen_time = (datetime.now() - gen_start_time).total_seconds()
            logger.info(f"Generation completed in {gen_time:.2f} seconds")
                
    def cached_fitness(self, c: Chromosome) -> float:
        
        if c in self.fitness_cache:
            
            return self.get_fitness_cache()[c]
        
        
        fitness = c.fitness()
        self.get_fitness_cache()[c] = fitness
        return fitness

    def best_chromosome(self) -> Chromosome:
        best = max(self.chromosomes, key=lambda c: c.fitness())
        logger.info(f"\n\n\n\n=== BEST CHROMOSOME ===")
        logger.info(f"Fitness: {best.fitness():.4f}")
        logger.info(f"Sequence: {[box.id for box in best.sequence]}")
        logger.info(f"Orientations: {best.orientations}")
        
        total_time = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        
        return best
    

    def get_fitness_cache(self):
        
        
        return self.fitness_cache
