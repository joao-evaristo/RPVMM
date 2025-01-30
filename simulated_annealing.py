import random
import math
from box import Box
from corridor import Corridor
from wave import Wave
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Definir qual caixa deve ser alocada a qual onda de forma que a área de picking média das ondas seja a
# menor possível, então além de atribuir uma caixa a uma onda é preciso definir quais corredores serão
# usados por cada caixa.

# Um produto pode estar em corredores diferentes e em andares diferentes.
# Uma onda pode ocupar mais de 1 andar, mas deve ser penalizadas por isso.
# Uma caixa só pode ser atribuída a uma onda.
# Evitar que ondas distintas ocupem os mesmos corredores.

@dataclass
class Config:
    max_wave_capacity: int = 6000
    initial_temp: float = 1000
    alpha: float = 0.99
    sa_max: int = 300
    floor_punishment_weight: int = 0
    corridor_punishment_weight: int = 0


class SimulatedAnnealing:
    def __init__(
            self,
            stock_layout: Dict[str, List],
            product_boxes: Dict[str, List],
            config: Config = Config()
    ):
        self.product_boxes = product_boxes["box_id"]
        self.stock_corridors = stock_layout["corridor"]
        self.products = product_boxes["product_boxes_sku"]
        self.wave_classes = product_boxes["wave_class"]
        self.floors = stock_layout["floor"]
        self.box_pieces = product_boxes["box_pieces"]
        self.corridor_skus = stock_layout["sku"]
        self.corridor_pieces = stock_layout["pieces"]
        self.config = config

        self.boxes: Dict[int, Box] = {}
        self.corridors: Dict[str, Corridor] = {}
        self.product_to_corridors: Dict[str, List[str]] = defaultdict(list)
        self.waves: Dict[int, Wave] = {}

        self.best_solution = None
        self.actual_cost = 0
        self.solution_cost = 0
        self.temperature = self.config.initial_temp

    def fill_boxes(self) -> None:
        for i, current_box_id in enumerate(self.product_boxes):
            current_box_id = int(current_box_id)
            if current_box_id not in self.boxes:
                self.boxes[current_box_id] = Box(current_box_id, self.wave_classes[i])
            self.boxes[current_box_id].add_product(self.products[i], self.box_pieces[i])

    def fill_corridors(self) -> None:
        for index, current_corridor in enumerate(self.stock_corridors):
            corridor_key = f'{current_corridor}_{self.floors[index]}'
            if corridor_key not in self.corridors:
                self.corridors[corridor_key] = Corridor(self.floors[index])
            self.corridors[corridor_key].add_product(
                sku=self.corridor_skus[index],
                quantity=self.corridor_pieces[index],
            )
            self.product_to_corridors[self.corridor_skus[index]].append(corridor_key)

    def generate_initial_solution(self) -> None:
        def reset_wave(wave: int, box: Box) -> Tuple[
            int, int, str]:
            wave += 1
            wave_products_quantity = 0
            current_wave_class = box.wave_class
            self.waves[wave] = Wave(current_wave_class)
            return wave, wave_products_quantity, current_wave_class

        corridors_copy = self.corridors.copy()
        wave = 0
        current_wave_class = self.wave_classes[0]

        for box_id, box in self.boxes.items():
            if wave not in self.waves:
                self.waves[wave] = Wave(current_wave_class)

            total_products_box = box.get_total_products()
            if self.waves[wave].total_products + total_products_box > self.config.max_wave_capacity or box.wave_class != current_wave_class:
                wave, wave_products_quantity, current_wave_class = reset_wave(
                    wave, box
                )

            box.set_wave(wave)
            self.waves[wave].add_box(box_id, total_products_box)

            self.allocate_products_to_corridors(box, wave, corridors_copy)


    def allocate_products_to_corridors(self, box: Box, wave: int, corridors: Dict[str, Corridor] = None) -> None:
        for product in box.products:
            product_quantity_remaining = product.quantity

            while product_quantity_remaining > 0:
                corridor_id, corridor, remaining = self.find_corridor(
                    product.sku, product_quantity_remaining, corridors
                )

                if not corridor_id:
                    raise Exception("Corridor not found")

                product_quantity_remaining = remaining
                box.add_corridor(corridor_id, product.sku)
                self.waves[wave].insert_corridor(corridor_id, box.id)

    def find_corridor(self, sku: str, quantity: int, corridors: Dict[str, Corridor] = None) -> Tuple[str, Corridor, int]:
        possible_corridors = self.product_to_corridors.get(sku, [])
        for corridor_id in possible_corridors:
            corridor = corridors[corridor_id]
            remaining = corridor.consume_product(sku, quantity)
            if remaining is not None:
                return corridor_id, corridor, remaining
        return None, None, None

    # def calculate_fo(self) -> float:
    #     total_waves = len(self.waves)
    #     total_area = 0
    #     floor_punishment = 0
    #     corridor_punishment = 0
    #     corridors_used = set()
    #
    #     for wave in self.waves.values():
    #         total_area += self.calculate_area(wave)
    #         floor_punishment += self.calculate_punishment_floor(wave)
    #         corridor_punishment += self.calculate_punishment_corridor(wave, corridors_used)
    #         corridors_used.update(wave.corridors)
    #
    #     average_area = total_area / total_waves
    #     fo = average_area + floor_punishment + corridor_punishment
    #     return fo

    def calculate_area(self, wave: Wave) -> int:
        area = 0
        for floor in set(wave.floors):
            if floor in wave.max_min_even_corridor:
                area += wave.max_min_even_corridor[floor][0] - wave.max_min_even_corridor[floor][1]
            if floor in wave.max_min_odd_corridor:
                area += wave.max_min_odd_corridor[floor][0] - wave.max_min_odd_corridor[floor][1]
        return area

    def calculate_punishment_floor(self, wave: Wave) -> int:
        return len(wave.floors) * self.config.floor_punishment_weight

    def calculate_punishment_corridor(self, wave: Wave, corridors_used: set) -> int:
        corridors_wave = set(wave.corridors.keys())
        corridors_already_used = corridors_wave.intersection(corridors_used)
        return len(corridors_already_used) * self.config.corridor_punishment_weight

    def validate_solution(self, waves: Dict[int, Wave]) -> bool:
        for wave in waves.values():
            wave_boxes = self.get_boxes_from_wave(wave)
            if wave.total_products > self.config.max_wave_capacity:
                return False
            if len(set([box.wave_class for box in wave_boxes])) > 1:
                return False
            for box in wave_boxes:
                if box.wave != wave:
                    return False
        return True

    def get_boxes_from_wave(self, wave: Wave) -> List[Box]:
        return [self.boxes[box_id] for box_id in wave.boxes]

    def simulated_annealing(self):
        self.generate_initial_solution()
        current_solution = self.waves.copy()
        current_cost = self.calculate_fo(current_solution)
        best_solution = current_solution
        best_cost = current_cost

        iteration = 0
        while self.temperature > 1 and iteration < self.config.sa_max:
            neighbor_solution = self.generate_neighbor(current_solution)
            neighbor_cost = self.calculate_fo_for_solution(neighbor_solution)
            print(f"Current cost: {current_cost}, Neighbor cost: {neighbor_cost}, iteration: {iteration}")

            if self.accept_solution(current_cost, neighbor_cost):
                current_solution = neighbor_solution
                current_cost = neighbor_cost

                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost

            self.temperature *= self.config.alpha
            iteration += 1

        self.waves = best_solution
        self.best_solution = best_solution
        self.solution_cost = best_cost
        print(f"\nBest cost: {self.solution_cost}")

    def generate_neighbor(self, current_solution):
        # Create a deep copy of the current solution's waves
        neighbor_solution = {}
        for wave_id, wave in current_solution.items():
            new_wave = Wave(wave.wave_class)
            new_wave.boxes = set(wave.boxes)
            new_wave.total_products = wave.total_products
            new_wave.corridors = {ck: set(cs) for ck, cs in wave.corridors.items()}
            new_wave.floors = set(wave.floors)
            new_wave.max_min_even_corridor = {k: v.copy() for k, v in wave.max_min_even_corridor.items()}
            new_wave.max_min_odd_corridor = {k: v.copy() for k, v in wave.max_min_odd_corridor.items()}
            neighbor_solution[wave_id] = new_wave

        # Select a random box to move
        box_id = random.choice(list(self.boxes.keys()))
        box = self.boxes[box_id]
        original_wave_id = None

        # Find which wave in the neighbor solution contains the box
        for wave_id, wave in neighbor_solution.items():
            if box_id in wave.boxes:
                original_wave_id = wave_id
                break
        if original_wave_id is None:
            return neighbor_solution  # Box not found in any wave (shouldn't happen)

        # Remove box from original wave
        original_wave = neighbor_solution[original_wave_id]
        original_wave.remove_box(box)
        # If original wave is empty, remove it
        if not original_wave.boxes:
            del neighbor_solution[original_wave_id]

        # Choose target wave: existing or new
        possible_target_ids = [wid for wid in neighbor_solution.keys() if wid != original_wave_id]
        if possible_target_ids:
            target_wave_id = random.choice(possible_target_ids)
        else:
            target_wave_id = max(neighbor_solution.keys(), default=0) + 1
            neighbor_solution[target_wave_id] = Wave(box.wave_class)
        target_wave = neighbor_solution[target_wave_id]

        # Add box to target wave
        target_wave.add_box(box.id, box.get_total_products())
        for corridor_key in box.get_corridors():
            target_wave.insert_corridor(corridor_key, box.id)

        # Update the box's wave assignment in the neighbor solution (not in the original boxes)
        # Note: In the current setup, this might not persist, so consider tracking assignments separately.
        # For this example, assume the wave's box set correctly represents assignments.

        return neighbor_solution

    # Update calculate_fo to include penalties for class mismatch and capacity overflow
    def calculate_fo(self, waves) -> float:
        total_waves = len(waves)
        if total_waves == 0:
            return float('inf')

        total_area = 0
        floor_punishment = 0
        corridor_punishment = 0
        class_punishment = 0
        capacity_punishment = 0
        corridors_used = set()

        for wave in waves.values():
            # Class mismatch penalty
            box_classes = {self.boxes[bid].wave_class for bid in wave.boxes}
            if len(box_classes) > 1:
                class_punishment += 1000  # Adjust weight as needed
            elif wave.wave_class not in box_classes:
                class_punishment += 1000

            # Capacity penalty
            if wave.total_products > self.config.max_wave_capacity:
                excess = wave.total_products - self.config.max_wave_capacity
                capacity_punishment += excess * 10  # Adjust weight

            total_area += self.calculate_area(wave)
            floor_punishment += self.calculate_punishment_floor(wave)
            corridor_punishment += self.calculate_punishment_corridor(wave, corridors_used)
            corridors_used.update(wave.corridors.keys())

        average_area = total_area / total_waves
        fo = (average_area + floor_punishment + corridor_punishment
              + class_punishment + capacity_punishment)
        return fo

    def accept_solution(self, current_cost, neighbor_cost):
        if neighbor_cost < current_cost:
            return True
        else:
            delta = neighbor_cost - current_cost
            return random.random() < math.exp(delta / self.temperature)

    def calculate_fo_for_solution(self, solution):
        original_waves = self.waves.copy()
        cost = self.calculate_fo(solution)
        self.waves = original_waves
        return cost

    # pensar em como vou fazer para gerar a vizinhança
    # uma ideia é trocar uma caixa de uma onda por outra caixa de outra onda
    # ou trocar o corredor
    # tem que validar se a solucao e valida ( atende os criterios de caixa, onda, classe, etc)


    # Permitir que solucoes que nao cumpram as restricoes, mas colocando uma alta penalizacao
    # o que permite um maior leque de alteracoes e evita que o algoritmo fique preso em um minimo local