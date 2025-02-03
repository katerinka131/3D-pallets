from input_reader import test_read_input, read_file
from genetics import Population
from pallet import Pallet
from draw import visualize_pallet
from box import Box 
def main():
    box_dimensions, pallet_dimensions = test_read_input()
    boxes = [Box(id, d1, d2, d3) for id, d1, d2, d3 in box_dimensions]
    pallet = Pallet(0, 0, 0, *pallet_dimensions)

    # Генетический алгоритм
    population = Population(20, boxes, pallet_dimensions)
    population.evolve(100)
    best_chromosome = population.best_chromosome()

    #boxes = read_file(data.csv)
    

    # Укладка коробок по лучшей хромосоме
    print("\nЛучшая хромосома:")
    print(f"Последовательность коробок: {[box.id for box in best_chromosome.sequence]}")
    print(f"Ориентации коробок: {best_chromosome.orientations}")

    for box, orientation in zip(best_chromosome.sequence, best_chromosome.orientations):
        print(f"\nПопытка укладки коробки {box.id} с ориентацией {orientation}:")
        if pallet.try_add(box, orientation):
            print(f"Коробка {box.id} успешно добавлена!")
            # visualize_pallet(pallet)  # Визуализируем после каждой коробки
        else:
            print(f"Коробка {box.id} не может быть добавлена.")
        pallet.print_status()

    # Выводим значение функции приспособленности
    fitness_value = best_chromosome.fitness()
    print(f"\nФункция приспособленности (отношение объёма коробок к объёму паллеты): {fitness_value:.2f}")

if __name__ == "__main__":
    main()