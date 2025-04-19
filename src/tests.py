import unittest
import random
from box import Box
from pallet import Pallet
from genetics import Chromosome, Population
from typing import List, Tuple
import os
import tempfile
import logging

# Отключаем логирование во время тестов
logging.disable(logging.CRITICAL)

class TestBox(unittest.TestCase):
    def test_box_creation(self):
        box = Box(1, 10, 20, 30)
        self.assertEqual(box.id, 1)
        self.assertEqual(box.d1, 10)
        self.assertEqual(box.d2, 20)
        self.assertEqual(box.d3, 30)
    
    def test_box_volume(self):
        box = Box(1, 2, 3, 4)
        self.assertEqual(box.volume(), 24)

class TestPallet(unittest.TestCase):
    def setUp(self):
        self.pallet = Pallet(0, 0, 0, 100, 100, 100)
    
    def test_pallet_initialization(self):
        self.assertEqual(self.pallet.x1, 0)
        self.assertEqual(self.pallet.y1, 0)
        self.assertEqual(self.pallet.z1, 0)
        self.assertEqual(self.pallet.x2, 100)
        self.assertEqual(self.pallet.y2, 100)
        self.assertEqual(self.pallet.z2, 100)
        self.assertEqual(len(self.pallet.subpallets), 1)
        self.assertEqual(len(self.pallet.boxes), 0)
    
    def test_total_volume(self):
        self.assertEqual(self.pallet.total_volume(), 100*100*100)
    
    def test_try_add_success(self):
        box = Box(1, 10, 10, 10)
        result = self.pallet.try_add(box, 0)
        self.assertTrue(result)
        self.assertEqual(len(self.pallet.boxes), 1)
        self.assertEqual(self.pallet.occupied_volume(), 1000)
    
    def test_try_add_failure(self):
        box = Box(1, 101, 101, 101)
        result = self.pallet.try_add(box, 0)
        self.assertFalse(result)
        self.assertEqual(len(self.pallet.boxes), 0)
    
    def test_occupied_volume(self):
        box1 = Box(1, 10, 10, 10)
        box2 = Box(2, 20, 20, 20)
        self.pallet.try_add(box1, 0)
        self.pallet.try_add(box2, 0)
        self.assertEqual(self.pallet.occupied_volume(), 10*10*10 + 20*20*20)
    
    def test_generate_orientations(self):
        box = Box(1, 10, 20, 30)
        orientations = self.pallet._generate_orientations(box)
        self.assertEqual(len(orientations), 6)
        self.assertIn((10, 20, 30), orientations)
        self.assertIn((30, 20, 10), orientations)
    
    def test_update_subpallets(self):
        box = Box(1, 30, 30, 30)
        self.pallet.try_add(box, 0)
        self.assertGreater(len(self.pallet.subpallets), 1)

class TestChromosome(unittest.TestCase):
    def setUp(self):
        self.boxes = [Box(1, 10, 10, 10), Box(2, 20, 20, 20), Box(3, 30, 30, 30)]
        self.pallet_dim = (100, 100, 100)
    
    def test_chromosome_initialization(self):
        chrom = Chromosome(self.boxes, self.pallet_dim)
        self.assertEqual(len(chrom.sequence), 3)
        self.assertEqual(len(chrom.orientations), 3)
        self.assertEqual(chrom.pallet_dimensions, self.pallet_dim)
    
    def test_chromosome_fitness(self):
        chrom = Chromosome(self.boxes, self.pallet_dim)
        fitness = chrom.fitness()
        self.assertGreaterEqual(fitness, 0)
        self.assertLessEqual(fitness, 1)
    
    def test_chromosome_mutate(self):
        chrom = Chromosome(self.boxes, self.pallet_dim)
        original_sequence = chrom.sequence.copy()
        original_orientations = chrom.orientations.copy()
        
        chrom.mutate()
        
        # Проверяем, что мутация изменила ориентации или последовательность
        self.assertTrue(
            chrom.orientations != original_orientations or 
            chrom.sequence != original_sequence
        )
    
    def test_chromosome_crossover(self):
        parent1 = Chromosome(self.boxes, self.pallet_dim)
        parent2 = Chromosome(self.boxes, self.pallet_dim)
        
        child = parent1.crossover(parent2)
        
        self.assertEqual(len(child.sequence), len(self.boxes))
        self.assertEqual(len(child.orientations), len(self.boxes))
        self.assertEqual(set(box.id for box in child.sequence), {1, 2, 3})
    
    def test_chromosome_crossover_ox(self):
        parent1 = Chromosome(self.boxes, self.pallet_dim)
        parent2 = Chromosome(self.boxes, self.pallet_dim)
        
        child = parent1.crossover_ox(parent2)
        
        self.assertEqual(len(child.sequence), len(self.boxes))
        self.assertEqual(len(child.orientations), len(self.boxes))
        self.assertEqual(set(box.id for box in child.sequence), {1, 2, 3})
    
   

class TestPopulation(unittest.TestCase):
    def setUp(self):
        self.boxes = [Box(i, 10+i, 10+i, 10+i) for i in range(1, 6)]
        self.pallet_dim = (100, 100, 100)
        self.pop_size = 10
    
    def test_population_initialization(self):
        pop = Population(self.pop_size, self.boxes, self.pallet_dim)
        self.assertEqual(len(pop.chromosomes), self.pop_size)
        
        # Проверяем, что половина хромосом отсортирована
        sorted_count = sum(
            1 for chrom in pop.chromosomes 
            if [box.volume() for box in chrom.sequence] == 
               sorted([box.volume() for box in chrom.sequence], reverse=True)
        )
        self.assertEqual(sorted_count, self.pop_size // 2)
    
    def test_cached_fitness(self):
        pop = Population(self.pop_size, self.boxes, self.pallet_dim)
        chrom = pop.chromosomes[0]
        
        # Первый вызов должен вычислить fitness
        fitness1 = pop.cached_fitness(chrom)
        
        # Второй вызов должен взять значение из кэша
        fitness2 = pop.cached_fitness(chrom)
        
        self.assertEqual(fitness1, fitness2)
        self.assertEqual(len(pop.get_fitness_cache()), 1)
    
    def test_evolve(self):
        pop = Population(self.pop_size, self.boxes, self.pallet_dim)
        initial_best = pop.best_chromosome().fitness()
        
        pop.evolve(5)
        
        new_best = pop.best_chromosome().fitness()
        self.assertGreaterEqual(new_best, initial_best)
    
    def test_best_chromosome(self):
        pop = Population(self.pop_size, self.boxes, self.pallet_dim)
        best = pop.best_chromosome()
        
        self.assertIsInstance(best, Chromosome)
        self.assertEqual(len(best.sequence), len(self.boxes))
    
    def test_fitness_cache_cleaning(self):
        pop = Population(self.pop_size, self.boxes, self.pallet_dim)
        
        # Вычисляем fitness для всех хромосом
        for chrom in pop.chromosomes:
            pop.cached_fitness(chrom)
        
        initial_cache_size = len(pop.get_fitness_cache())
        
        # Эволюция должна очистить кэш для удалённых хромосом
        pop.evolve(1)
        
        new_cache_size = len(pop.get_fitness_cache())
        self.assertLess(new_cache_size, initial_cache_size)

class TestIntegration(unittest.TestCase):
    def test_full_integration(self):
        # Создаем тестовые данные
        boxes = [Box(1, 20, 20, 20), Box(2, 30, 30, 30), Box(3, 10, 10, 10)]
        pallet_dim = (100, 100, 100)
        
        # Создаем популяцию
        pop = Population(10, boxes, pallet_dim)
        
        # Запускаем эволюцию
        pop.evolve(5)
        
        # Получаем лучшую хромосому
        best = pop.best_chromosome()
        
        # Проверяем результаты
        self.assertIsInstance(best, Chromosome)
        self.assertGreater(best.fitness(), 0)
        
        # Пробуем уложить коробки на паллету
        pallet = Pallet(0, 0, 0, *pallet_dim)
        for box, orientation in zip(best.sequence, best.orientations):
            pallet.try_add(box, orientation)
        
        # Проверяем, что хотя бы одна коробка была уложена
        self.assertGreater(len(pallet.boxes), 0)
        self.assertGreater(pallet.occupied_volume(), 0)

if __name__ == '__main__':
    unittest.main()