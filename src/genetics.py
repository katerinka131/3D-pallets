import random
from pallet import Pallet
from box import Box
from typing import List, Tuple
import concurrent.futures

class Chromosome:
    def __init__(self, boxes: List[Box], pallet_dimensions: Tuple[int, int, int], sorted=False):
        self.boxes = boxes
        self.pallet_dimensions = pallet_dimensions
        
        if sorted:
            self.sequence = boxes[:]  # Используем переданный порядок, не перемешивая
        else:
            self.sequence = random.sample(boxes, len(boxes))  # Случайный порядок

        self.orientations = [random.choice([0, 1, 2, 3, 4, 5]) for _ in range(len(boxes))]

    def __repr__(self):
        box_ids = [box.id for box in self.sequence]
        return f"Chromosome(box_ids={box_ids}, orientations={self.orientations})"

    def fitness(self) -> float:
        pallet = Pallet(0, 0, 0, *self.pallet_dimensions)
        for box, orientation in zip(self.sequence, self.orientations):
            if not pallet.try_add(box, orientation):
                continue
        return pallet.occupied_volume() / pallet.total_volume()

    def mutate(self):
        num_boxes = len(self.sequence)

        # Меняем ориентации у 10% коробок
        for _ in range(num_boxes // 10 + 1):  
            idx = random.randint(0, num_boxes - 1)
            self.orientations[idx] = random.choice([0, 1, 2, 3, 4, 5])

        # Переставляем 5% коробок местами
        num_swaps = max(1, num_boxes // 20)
        swap_indices = random.sample(range(num_boxes), num_swaps * 2)
        for i in range(0, len(swap_indices), 2):
            idx1, idx2 = swap_indices[i], swap_indices[i+1]
            self.sequence[idx1], self.sequence[idx2] = self.sequence[idx2], self.sequence[idx1]

        # Иногда инвертируем небольшой отрезок
        if random.random() < 0.2:
            start, end = sorted(random.sample(range(num_boxes), 2))
            self.sequence[start:end] = self.sequence[start:end][::-1]

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

class Population:
    def __init__(self, size: int, boxes: List[Box], pallet_dimensions: Tuple[int, int, int]):
        self.chromosomes = []
        sorted_boxes = sorted(boxes, key=lambda box: box.volume(), reverse=True)

        # Половина хромосом с отсортированными коробками
        for _ in range(size // 2):
            chromosome = Chromosome(sorted_boxes, pallet_dimensions, sorted=True)
            self.chromosomes.append(chromosome)

        # Вторая половина - случайные
        for _ in range(size - len(self.chromosomes)):  
            chromosome = Chromosome(boxes, pallet_dimensions)
            self.chromosomes.append(chromosome)

        self.fitness_cache = dict()
        
        # Вывод созданных хромосом
        # print("\nInitial population chromosomes:")
        # for i, chrom in enumerate(self.chromosomes, 1):
        #     print(f"Chromosome {i}: {chrom}")

    def evolve(self, generations: int):
        for gen in range(generations):
            
            
            # Вычисление fitness
            with concurrent.futures.ThreadPoolExecutor() as executor:
                fitness_values = list(executor.map(self.cached_fitness, self.chromosomes))
            fitness_values = list(zip(fitness_values, self.chromosomes))
            fitness_values.sort(key=lambda x: x[0], reverse=True)
            
            
            
            # Отбор лучших
            self.chromosomes = [c for _, c in fitness_values[:len(self.chromosomes) // 2]]
            
            # Создание нового поколения
            new_generation = []
            while len(new_generation) < len(self.chromosomes):
                parent1, parent2 = random.sample(self.chromosomes, 2)
                child = parent1.crossover(parent2)
                child.mutate()
                new_generation.append(child)
            
            self.chromosomes += new_generation
            
            

    def cached_fitness(self, c: Chromosome) -> float:
        if c in self.fitness_cache:
            return self.fitness_cache[c]
        self.fitness_cache[c] = c.fitness()
        return self.fitness_cache[c]

    def best_chromosome(self) -> Chromosome:
        best = max(self.chromosomes, key=lambda c: c.fitness())
        print(f"\nBest chromosome found: {best}")
        return best