import random
import math
from box import Box
from corridor import Corridor
from wave import Wave

# Definir qual caixa deve ser alocada a qual onda de forma que a área de picking média das ondas seja a
# menor possível, então além de atribuir uma caixa a uma onda é preciso definir quais corredores serão
# usados por cada caixa.

# Um produto pode estar em corredores diferentes e em andares diferentes.
# Uma onda pode ocupar mais de 1 andar, mas deve ser penalizadas por isso.
# Uma caixa só pode ser atribuída a uma onda.
# Evitar que ondas distintas ocupem os mesmos corredores.

class SimulatedAnnealing:
    def __init__(
        self,
        stock_layout,
        product_boxes,
        w=6000,
        initial_temp=1000,
        alpha=0.99,
        sa_max=10,
    ):
        self.product_boxes = product_boxes["box_id"]  # Conjunto das caixas
        self.stock_corridors = stock_layout["corridor"]  # Conjunto dos corredores
        self.products = product_boxes["product_boxes_sku"]  # Conjunto dos produtos
        self.wave_classes = product_boxes["wave_class"]  # Conjunto de classes de onda
        self.F = stock_layout["floor"] # Conjunto dos andares
        self.M = product_boxes["box_pieces"] # Conjunto da quantidade de produtos
        self.L = stock_layout["sku"]  # Conjunto dos produtos nos corredores
        self.Q = stock_layout["pieces"]  # Conjunto da quantidade de produtos nos corredores
        self.W = w  # Capacidade máxima de produtos da onda
        self.boxes = {}
        self.corridors = {}
        self.product_to_corridors = {}
        self.waves = {}
        self.floor_punishment_weight = 2
        self.corridor_punishment_weight = 1
        self.best_solution = None
        self.actual_cost = 0
        self.solution_cost = 0
        self.initial_temp = initial_temp
        self.temperature = self.initial_temp
        self.alpha = alpha
        self.sa_max = sa_max
        self.corridor_boxes = []
        self.wave_boxes = []
        self.floor_punishment = 0
        self.corridor_punishment = 0

    def fill_boxes(self):
        for i, current_box_id in enumerate(self.product_boxes):
            current_box_id = int(current_box_id)
            if current_box_id not in self.boxes:
                self.boxes[current_box_id] = Box(self.wave_classes[i])
            self.boxes[current_box_id].add_product(self.products[i], self.M[i])

        print(self.boxes.keys())

    def fill_corridors(self):
        for index, current_corridor in enumerate(self.stock_corridors):
            corridor_key = f'{current_corridor}_{self.F[index]}'
            if corridor_key not in self.corridors:
                self.corridors[corridor_key] = Corridor(self.F[index])
            self.corridors[corridor_key].add_product(
                sku=self.L[index],
                quantity=self.Q[index],
            )
            if self.L[index] not in self.product_to_corridors:
                self.product_to_corridors[self.L[index]] = []
            self.product_to_corridors[self.L[index]].append(corridor_key)


    def generate_initial_solution(self):
        def reset_wave(wave, wave_products_quantity, current_wave_class, box):
            wave += 1
            wave_products_quantity = 0
            current_wave_class = box.wave_class
            return wave, wave_products_quantity, current_wave_class

        corridors_copy = self.corridors.copy()
        boxes_copy = self.boxes.copy()
        wave = 0
        wave_products_quantity = 0
        current_wave_class = self.wave_classes[0]

        for box_id, box in boxes_copy.items():
            total_products_box = box.get_total_products()

            if wave_products_quantity + total_products_box > self.W or box.wave_class != current_wave_class:
                wave, wave_products_quantity, current_wave_class = reset_wave(
                    wave, wave_products_quantity, current_wave_class, box
                )

            if wave not in self.waves:
                self.waves[wave] = Wave(current_wave_class)

            box.set_wave(wave)
            self.waves[wave].add_box(box_id, total_products_box)

            for product in box.products:
                product_quantity_remaining = product.quantity

                while product_quantity_remaining > 0:
                    corridor_id, corridor, remaining = self.find_corridor(
                        product.sku, product_quantity_remaining
                    )

                    if not corridor_id:
                        raise Exception("Corridor not found")

                    wave_products_quantity += product.quantity
                    product_quantity_remaining = remaining
                    box.add_corridor(corridor_id)
                    self.waves[wave].insert_corridor(corridor_id)


    def find_corridor(self, sku, quantity):
        possible_corridors = self.product_to_corridors.get(sku, [])
        for corridor_id in possible_corridors:
            corridor = self.corridors[corridor_id]
            remaining = corridor.consume_product(sku, quantity)
            if remaining or remaining == 0:
                return corridor_id, corridor, remaining
        return None, None, None

    def calculate_area(self, wave: Wave):
        max_min_even_corridor = wave.max_min_even_corridor
        max_min_odd_corridor = wave.max_min_odd_corridor
        area = 0
        for floor in set(wave.floors):
            if floor in max_min_even_corridor:
                area += max_min_even_corridor[floor][0] - max_min_even_corridor[floor][1]
            if floor in max_min_odd_corridor:
                area += max_min_odd_corridor[floor][0] - max_min_odd_corridor[floor][1]
        return area

    def calculate_punishment_floor(self, wave: Wave):
        return len(wave.floors) * self.floor_punishment_weight

    def calculate_punishment_corridor(self, wave: Wave, corridors_used):
        corridors_already_used = wave.corridors.intersection(corridors_used)
        return len(corridors_already_used) * self.corridor_punishment_weight

    def calculate_fo(self):
        total_waves = len(self.waves)
        total_area = 0
        floor_punishment = 0
        corridor_punishment = 0
        corridors_used = set()
        for wave in self.waves.values():
            total_area += self.calculate_area(wave)
            floor_punishment += self.calculate_punishment_floor(wave)
            corridor_punishment += self.calculate_punishment_corridor(wave, corridors_used)
            corridors_used.update(wave.corridors)
        average_area = total_area / total_waves
        print(average_area)
        fo = average_area + floor_punishment + corridor_punishment
        print(fo)
        return fo

    # pensar em como vou fazer para gerar a vizinhança
    # uma ideia é trocar uma caixa de uma onda por outra caixa de outra onda
    # ou trocar o corredor
    # tem que validar se a solucao e valida ( atende os criterios de caixa, onda, classe, etc)


    def define_atendimento(self, facilidades):
        # definir o atendimento de cada cliente
        # cada cliente deve ser atendido pela facilidade mais proxima
        # cada cliente e atendido por apenas uma facilidade
        xij = [None] * self.n
        facilidades_abertas = facilidades[: self.p]
        for i in range(self.n):
            menor_distancia = float("inf")
            for j in facilidades_abertas:
                if self.distancias[j][i] < menor_distancia:
                    menor_distancia = self.distancias[j][i]
                    xij[i] = j
        return xij

    def vizinhanca(self):
        # gerar uma vizinhanca da solucao atual
        # trocar uma facilidade aberta por uma fechada
        # ou vice versa
        vizinho = self.facilidades.copy()
        # definir pesos para cada tipo de troca
        if self.temperature > 0.5 * self.initial_temp:
            pesos = [0.6, 0.30, 0.10]
        elif self.temperature > 0.2 * self.initial_temp:
            pesos = [0.8, 0.15, 0.05]
        else:
            pesos = [0.9, 0.09, 0.01]
        # determinar o número de trocas com base em pesos
        trocas = random.choices([1, 2, 3], weights=pesos, k=1)[0]
        # obter amostra exclusiva de facilidades a serem trocadas
        facilidades_trocadas = random.sample(range(self.p), trocas)

        for facilidade_sai in facilidades_trocadas:
            facilidade_entra = random.randint(self.p, self.m - 1)
            vizinho[facilidade_sai], vizinho[facilidade_entra] = (
                vizinho[facilidade_entra],
                vizinho[facilidade_sai],
            )

        return vizinho

    def aceita_melhora(self, custo_vizinho):
        # aceitar a solucao vizinha se ela for melhor
        # ou se ela for pior, mas a probabilidade de aceitar for maior que um numero aleatorio entre 0 e 1
        if custo_vizinho > self.actual_cost:
            return True
        else:
            # utiliza o criterio de metropolis
            delta = custo_vizinho - self.actual_cost
            return random.random() < math.exp(delta / self.temperature)

    def atualiza_temperatura(self):
        # atualiza a temperatura
        # utiliza o fast simulated annealing
        self.temperature = self.temperature * self.alpha

    # def executa(self):
    #     self.best_solution = facilidades
    #     self.actual_cost = self.funcao_objetivo(facilidades)
    #     self.solution_cost = self.actual_cost
    #     print("*" * 50)
    #     print(f"Custo da solucao inicial: {self.actual_cost}")
    #     while self.temperature > 0.1:
    #         for _ in range(self.sa_max):
    #             vizinho = self.vizinhanca()
    #             custo_vizinho = self.funcao_objetivo(vizinho)
    #             if self.aceita_melhora(custo_vizinho):
    #                 self.facilidades = vizinho
    #                 self.actual_cost = custo_vizinho
    #                 if custo_vizinho > self.funcao_objetivo(self.best_solution):
    #                     self.best_solution = vizinho
    #                     self.solution_cost = custo_vizinho
    #         self.atualiza_temperatura()
    #     facilidades_abertas = self.best_solution[: self.p]
    #     print(f"Melhor solucao: \n{facilidades_abertas}")
    #     print(f"Custo da melhor solucao: {self.solution_cost}")
    #     print("*" * 50)
    #     return self.solution_cost
