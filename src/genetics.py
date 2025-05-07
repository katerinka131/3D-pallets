import random
from pallet import Pallet
from box import Box
from typing import List, Tuple
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

class Chromosome:
    def __init__(self, boxes: List[Box], pallet_dimensions: Tuple[int, int, int], sorted_by_volume=False, sorted_by_area=False):
        self.boxes = boxes
        self.pallet_dimensions = pallet_dimensions
        
        if sorted_by_volume:
            # Сортировка по объему (d1*d2*d3)
            self.sequence = sorted(boxes, key=lambda box: box.volume(), reverse=True)
        elif sorted_by_area:
            # Сортировка по площади (d1*d2) для первой ориентации
            self.sequence = sorted(boxes, key=lambda box: box.d1 * box.d2, reverse=True)
        else:
            self.sequence = random.sample(boxes, len(boxes))
            
        self.orientations = [random.choice([0, 1]) for _ in range(len(boxes))]
    
    def __repr__(self):
        box_ids = [box.id for box in self.sequence]
        return f"Chromosome(box_ids={box_ids}, orientations={self.orientations})"
    
    def fitness(self) -> float:
        pallet = Pallet(self.pallet_dimensions[0], self.pallet_dimensions[1])
        
        for box, orientation in zip(self.sequence, self.orientations):
            pallet.try_add(box, orientation)
                
        pallet_volume = pallet.length * pallet.width * pallet.current_height
        
        return pallet.occupied_volume() / pallet_volume

    def mutate(self):
        num_boxes = len(self.sequence)
        
        for _ in range(max(1, num_boxes // 9)):
            idx = random.randint(0, num_boxes - 1)
            self.orientations[idx] = 1 - self.orientations[idx]
        
        # Мутация порядка
        for _ in range(max(1, num_boxes // 20)):
            idx1, idx2 = random.sample(range(num_boxes), 2)
            self.sequence[idx1], self.sequence[idx2] = self.sequence[idx2], self.sequence[idx1]
            self.orientations[idx1], self.orientations[idx2] = self.orientations[idx2], self.orientations[idx1]

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome(self.boxes, self.pallet_dimensions)
        split = random.randint(1, len(self.sequence) - 1)
        
        child.sequence = self.sequence[:split]
        child.orientations = self.orientations[:split]
        
        for box, orientation in zip(other.sequence, other.orientations):
            if box not in child.sequence:
                child.sequence.append(box)
                child.orientations.append(orientation)
        
        return child

    def crossover_ox(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome(self.boxes, self.pallet_dimensions)
        size = len(self.sequence)
        point1 = random.randint(0, size - 2)
        point2 = random.randint(point1 + 1, size - 1)
    
        segment = self.sequence[point1:point2]
        segment_orient = self.orientations[point1:point2]
        
        remaining_boxes = [box for box in other.sequence if box not in segment]
        remaining_orient = [
            other.orientations[i] 
            for i, box in enumerate(other.sequence) 
            if box not in segment
        ]
        
        child.sequence = remaining_boxes[:point1] + segment + remaining_boxes[point1:]
        child.orientations = remaining_orient[:point1] + segment_orient + remaining_orient[point1:]
        
        return child

class Population:
    def __init__(self, size: int, boxes: List[Box], pallet_dimensions: Tuple[int, int, int]):
        self.boxes = boxes
        self.pallet_dimensions = pallet_dimensions
        
        # Первая половина - отсортирована по объему
        sorted_boxes_volume = sorted(boxes, key=lambda box: box.volume(), reverse=True)
        self.chromosomes = [Chromosome(sorted_boxes_volume, pallet_dimensions, sorted_by_volume=True) 
                          for _ in range(8)]
        
        # Вторая половина - отсортирована по площади (d1*d2)
        sorted_boxes_area = sorted(boxes, key=lambda box: box.d1 * box.d2, reverse=True)
        self.chromosomes.extend([Chromosome(sorted_boxes_area, pallet_dimensions, sorted_by_area=True) 
                               for _ in range(8)])
        self.chromosomes.extend([Chromosome(boxes, pallet_dimensions) 
                               for _ in range(size - len(self.chromosomes))])
        
        self.best_fitness_per_generation = []

    def evolve(self, generations: int):
        for gen in range(generations):
            print(f"Generation {gen}")
            try:
                with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                    fitness_values = list(executor.map(Chromosome.fitness, self.chromosomes))
            except Exception as e:
                raise
            
            self.best_fitness_per_generation.append(max(fitness_values))
            
            # Отбираем лучшие
            sorted_chromosomes = sorted(zip(fitness_values, self.chromosomes), 
                                     key=lambda x: x[0], reverse=True)
            elite = [c for _, c in sorted_chromosomes[:len(self.chromosomes)//2]]
            
            # Создаем новое поколение
            new_generation = elite.copy()
            while len(new_generation) < len(self.chromosomes):
                parent1, parent2 = random.sample(elite, 2)
                child = parent1.crossover_ox(parent2)
                child.mutate()
                new_generation.append(child)
            
            self.chromosomes = new_generation
    
    def best_chromosome(self) -> Chromosome:
        return max(self.chromosomes, key=lambda c: c.fitness())