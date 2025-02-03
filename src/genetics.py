import random
from pallet import Pallet
from box import Box
from typing import List, Tuple

class Chromosome:
    def __init__(self, boxes: List[Box], pallet_dimensions: Tuple[int, int, int]):
        self.boxes = boxes
        self.pallet_dimensions = pallet_dimensions
        self.sequence = random.sample(boxes, len(boxes))  # Случайная последовательность коробок
        self.orientations = [random.choice([0, 1, 2, 3, 4, 5]) for _ in range(len(boxes))]  # Случайные ориентации

    def fitness(self) -> float:
        pallet = Pallet(0, 0, 0, *self.pallet_dimensions)
        for box, orientation in zip(self.sequence, self.orientations):
            if not pallet.try_add(box, orientation):
                break
        return pallet.occupied_volume() / pallet.total_volume()

    def mutate(self):
        # Мутация: меняем местами две случайные коробки
        idx1, idx2 = random.sample(range(len(self.sequence)), 2)
        self.sequence[idx1], self.sequence[idx2] = self.sequence[idx2], self.sequence[idx1]
        self.orientations[idx1], self.orientations[idx2] = self.orientations[idx2], self.orientations[idx1]

        # Мутация: изменяем ориентацию случайной коробки
        idx = random.randint(0, len(self.sequence) - 1)
        self.orientations[idx] = random.choice([0, 1, 2, 3, 4, 5])

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome(self.boxes, self.pallet_dimensions)
        split = random.randint(1, len(self.sequence) - 1)
        
        # Первая часть берется от первого родителя
        child.sequence = self.sequence[:split]
        child.orientations = self.orientations[:split]
        
        # Вторая часть заполняется коробками и ориентациями из второго родителя
        for i, box in enumerate(other.sequence):
            if box not in child.sequence:
                child.sequence.append(box)
                child.orientations.append(other.orientations[i])
        
        return child

class Population:
    def __init__(self, size: int, boxes: List[Box], pallet_dimensions: Tuple[int, int, int]):
        self.chromosomes = [Chromosome(boxes, pallet_dimensions) for _ in range(size)]

    def evolve(self, generations: int):
        for _ in range(generations):
            # Селекция: выбираем лучшие хромосомы
            self.chromosomes.sort(key=lambda c: c.fitness(), reverse=True)
            self.chromosomes = self.chromosomes[:len(self.chromosomes) // 2]

            # Кроссовер и мутация
            new_generation = []
            while len(new_generation) < len(self.chromosomes):
                parent1, parent2 = random.sample(self.chromosomes, 2)
                child = parent1.crossover(parent2)
                child.mutate()
                new_generation.append(child)

            self.chromosomes += new_generation

    def best_chromosome(self) -> Chromosome:
        return max(self.chromosomes, key=lambda c: c.fitness())