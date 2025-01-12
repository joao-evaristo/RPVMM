import random
import math
from box import Box
from corridor import Corridor

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
        self.J = product_boxes["wave_class"]  # Conjunto das ondas
        self.I = product_boxes["box_id"]  # Conjunto das caixas
        self.K = stock_layout["corridor"]  # Conjunto dos corredores
        self.P = product_boxes["product_boxes_sku"]  # Conjunto dos produtos
        self.C = product_boxes["wave_class"]  # Conjunto de classes de onda
        self.F = stock_layout["floor"] # Conjunto dos andares
        self.M = product_boxes["box_pieces"] # Conjunto da quantidade de produtos
        self.L = stock_layout["sku"]  # Conjunto dos produtos nos corredores
        self.Q = stock_layout["pieces"]  # Conjunto da quantidade de produtos nos corredores
        self.W = w  # Capacidade máxima de produtos da onda
        self.boxes = {}
        self.corridors = {}
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

        # preciso saber qual caixa foi aloca a qual onda
        # e quais corredores serão usados pela onda
        # Uma caixa só pode ser atribuída a uma onda.
        # se uma onda usa um corredor, ja posso marcar ele como utilizado
        # se uma onda usa um corredor, e outra onda usa o mesmo corredor, penalizar
        # para calcular a funcao objetivo, usar um array de corredores utilizados

        # penalizacao
        # se uma onda usa mais de um andar, penalizar. somar uma variavel
        # se uma onda usa um corredor que ja foi usado por outra onda, penalizar. somar uma variavel

        # uma solucao sera formada por um array de
        # array de corredores, cada posição do array representa um corredor, e o valor da posição representa
        # a caixa alocada
        # array de ondas, cada posição do array representa uma onda, e o valor da posição representa a caixa alocada

    # def gerar_solucao_inicial_gulosa(self):
    #     facilidades = sorted(
    #         range(self.m), key=lambda x: sum(self.distancias[x]), reverse=True
    #     )
    #     return facilidades
    # vou ter que corrigir isso para reutilizar idices ja preenchidos
    def fill_boxes(self):
        # preencher o array de caixas
        current_box = self.I[0]
        current_box_index = 0
        for i in range(len(self.I)):
            current_box_id = self.I[i]

            # Check if the box already exists in the dictionary
            if current_box_id not in self.boxes:
                # If it doesn't exist, create a new box
                self.boxes[current_box_id] = Box(self.C[i])

            # Add the product to the existing or newly created box
            self.boxes[current_box_id].add_product(self.P[i], self.M[i])

    def fill_corridors(self):
        # preencher o array de corredores
        for index, current_corridor in enumerate(self.K):
            if f'{current_corridor}_{self.F[index]}' not in self.corridors:
                self.corridors[f'{current_corridor}_{self.F[index]}'] = Corridor(self.F[index])
            self.corridors[f'{current_corridor}_{self.F[index]}'].add_product(self.L[index], self.Q[index])

    def generate_initial_solution(self):
        # gerar solucao inicial gulosa pegando os corredores mais proximos do lado do corredor inicial.
        # Pega a primeira caixa, verifica e aloca no primeiro corredor que encontrar que satisfaça a demanda
        # considerar corredores impares tendo como vizinhos corredores impares vizinhos e corredores pares vizinhos
        #evitar avancar o andar, caso nao tenha mais estoque nos corredores do andar, sobe o andar
        corridors_copy = self.corridors.copy()
        boxes_copy = self.boxes.copy()
        for(i, box) in enumerate(boxes_copy):
            box = boxes_copy[self.I[i]]
        #initial_box = boxes_copy[self.I[0]]
            product = box.products[0]
            corridor_id, corridor = self.find_corridor(corridors_copy, product)
            if corridor_id:
                print(corridor_id)
        # conferir se deu certo
        # fazer atribuicoes dos corredores, ondas, etc
        #itera sobre os produtos da caixa
        #passa para a proxima caixa
        #assim em diante
        #passar organizado em impares e pares, todas as organizacoes em pre work
    def find_corridor(self, corridors, product):
        #pensar em deixar um dict ja com os possiveis corredores para cada produto
        # nao posso pensar em pegar apenas o corredor que atenda a demanda completa, porque pode ser parcial
        # encontrar o corredor mais proximo para atender a demanda do produto
        for corridor_id, corridor in corridors.items():
            has_consumed = corridor.consume_product(product.sku, product.quantity)
            if has_consumed:
                return corridor_id, corridor
        return None, None


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

    def funcao_objetivo(self, s):
        # para cada cliente, somar a distancia entre ele e a facilidade que o atende
        # a funcao objetivo e maximizar a soma das distancias da distancia minima entre cada facilidade e cada cliente
        xij = self.define_atendimento(s)
        custo = 0
        for i, j in enumerate(xij):
            custo += self.distancias[j][i]
        return custo

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
