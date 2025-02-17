import math
from random import randint, random, sample, shuffle

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
    floor_punishment_weight: int = 2
    corridor_punishment_weight: int = 1


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
        self.max_temp = self.config.initial_temp

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
            self.product_to_corridors[self.corridor_skus[index]].append(corridor_key) # trocar isso aqui para ter a quantidade tambem

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

            self.allocate_boxes_to_corridors(box, wave, corridors_copy)


    def allocate_boxes_to_corridors(self, box: Box, wave: int, corridors: Dict[str, Corridor] = None, is_random = False) -> None:
        for product in box.products:
            product_quantity_remaining = product.quantity

            while product_quantity_remaining > 0:
                corridor_id, corridor, remaining = self.find_corridor(
                    product.sku, product_quantity_remaining, corridors, is_random
                )

                if not corridor_id:
                    raise Exception("Corridor not found")

                box.add_corridor(corridor_id, product.sku)
                self.waves[wave].add_corridor(corridor_id, box.id, product.sku, product_quantity_remaining)
                product_quantity_remaining = remaining

    def find_corridor(self, sku: str, quantity: int, corridors: Dict[str, Corridor] = None, is_random = False) -> Tuple[str, Corridor, int]:
        possible_corridors = self.product_to_corridors.get(sku, [])
        if is_random:
            shuffle(possible_corridors)
        for corridor_id in possible_corridors:
            corridor = corridors[corridor_id]
            remaining = corridor.consume_product(sku, quantity)
            if remaining is not None:
                return corridor_id, corridor, remaining
        return None, None, None

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

    def get_boxes_from_wave(self, wave: Wave) -> List[Box]: # mudar aqui
        boxes_corridors = self.get_boxes_ids_from_wave(wave)
        return [self.boxes[box_id] for box_id in boxes_corridors]

    def get_boxes_ids_from_wave(self, wave: Wave):
        boxes_corridors = set()
        for corridor in wave.corridors.keys():
            boxes_corridors.update(wave.corridors[corridor].keys())
        return boxes_corridors

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
        def get_number_of_corridors_to_swap(wave: Wave):
            max_swaps = len(wave.corridors.keys()) // 2
            temp_ratio = self.temperature / self.max_temp
            return randint(1, max(1, int(max_swaps * temp_ratio)))
        neighbor_solution = current_solution.copy()
        for wave_id, wave in neighbor_solution.items():
            num_corridors_picks = get_number_of_corridors_to_swap(wave)
            print(list(wave.corridors.keys()).sort())
            corridors_keys = list(wave.corridors.keys())
            corridors_keys.sort()
            sorted_corridors = sample(corridors_keys, num_corridors_picks)
            wave_box_product_quantity = dict[str, int]
            # remover os corredores selecionados e baguncar a ordem para forcar a escolher novos dentro dos que dispoem os produtos
            for corridor in sorted_corridors:
                # vou ter que saber quais produtos da caixa vou ter que realocar
                # atualizar os corredores e produtos disponiveis, pois retirei o corredor
                boxes = wave.remove_corridor(corridor)
                wave_box_product_quantity = {key: wave_box_product_quantity.get(key, 0) + boxes.get(key, 0) for key in set(wave_box_product_quantity) | set(boxes)}
                # wave_box_product_quantity = {key: wave_product_quantity.get(key, 0) + products_quantity.get(key, 0) for key in set(wave_product_quantity) | set(products_quantity)}
                # escolher um corredor aleatorio para alocar os produtos
            #print(wave_box_product_quantity)
            # for sku, quantity in wave_product_quantity.items():
            #     self.allocate_boxes_to_corridors(self.boxes[wave.boxes[0]], wave_id, self.corridors, True)


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
            box_classes = {self.boxes[bid].wave_class for bid in self.get_boxes_ids_from_wave(wave)}
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
            return random() < math.exp(delta / self.temperature)

    def calculate_fo_for_solution(self, solution):
        original_waves = self.waves.copy()
        cost = self.calculate_fo(solution)
        self.waves = original_waves
        return cost