import random
import os
import psutil
import logging
from pallet import Pallet
from box import Box
from typing import List, Tuple
import concurrent.futures
from datetime import datetime
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
# Настройка логирования


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
        pallet = Pallet(0, 0, 0, *self.pallet_dimensions)
        unplaced_boxes = []
        
        for box, orientation in zip(self.sequence, self.orientations):
            if not pallet.try_add(box, orientation):
                unplaced_boxes.append(box)

        for box in unplaced_boxes:
            for orientation in range(6):  
                if pallet.try_add(box, orientation):  # Если удалось добавить
                    break
        fitness = pallet.occupied_volume() / pallet.total_volume()
        
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
        child = Chromosome(self.boxes, self.pallet_dimensions)
        split = random.randint(1, len(self.sequence) - 1)
        
        child.sequence = self.sequence[:split]
        child.orientations = self.orientations[:split]
        
        for i, box in enumerate(other.sequence):
            if box not in child.sequence:
                child.sequence.append(box)
                child.orientations.append(other.orientations[i])
        
        
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
        
        self.chromosomes = []
        sorted_boxes = sorted(boxes, key=lambda box: box.volume(), reverse=True)

        for _ in range(size // 2):
            chromosome = Chromosome(sorted_boxes, pallet_dimensions, sorted=True)
            self.chromosomes.append(chromosome)

        # Вторая половина - случайные
        for _ in range(size - len(self.chromosomes)):  
            chromosome = Chromosome(boxes, pallet_dimensions)
            self.chromosomes.append(chromosome)

        self.fitness_cache = dict()
        self.best_fitness_per_generation = []

    

    def evolve(self, generations: int):
        
        for gen in range(generations):
            
            try:
                with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                    fitness_values = list(executor.map(Chromosome.fitness, self.chromosomes))
                
            except Exception as e:
                raise
            
            sorted_chromosomes = sorted(zip(fitness_values, self.chromosomes), 
                                  key=lambda x: x[0], reverse=True)
            new_population = [c for _, c in sorted_chromosomes[:7]]
            
            self.best_fitness_per_generation.append(max(fitness_values))
            
            new_generation = []
            
            while len(new_generation) < 13:
                parent1, parent2 = random.sample(new_population, 2)
                child = parent1.crossover_ox(parent2)
                if random.random() < 0.5: 
                    
                    child.mutate()
                
                new_generation.append(child)

            self.chromosomes = new_population + new_generation
            
            
                
    

    def best_chromosome(self) -> Chromosome:
        best = max(self.chromosomes, key=lambda c: c.fitness())
        
        
        return best
    

    
