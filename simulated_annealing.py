import random
import math

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
        J,
        I,
        K,
        P,
        C,
        W=6000,
        initial_temp=1000,
        alpha=0.99,
        sa_max=10,
    ):
        self.J = J  # Conjunto das ondas
        self.I = I  # Conjunto das caixas
        self.K = K  # Conjunto dos corredores
        self.P = P  # Conjunto dos produtos
        self.C = C  # Conjunto de classes de onda
        self.W = W  # Capacidade máxima de produtos da onda
        self.facilidades = []
        self.best_solution = None
        self.actual_cost = 0
        self.solution_cost = 0
        self.initial_temp = initial_temp
        self.temperature = self.initial_temp
        self.alpha = alpha
        self.sa_max = sa_max
        # test

        # preciso saber qual caixa foi aloca a qual onda
        # e quais corredores serão usados pela onda

        # se uma onda usa um corredor, ja posso marcar ele como utilizado
        # array de binarios para marcar se o corredor foi utilizado
        # uma solucao sera formada por

    def gerar_solucao_inicial_gulosa(self):
        facilidades = sorted(
            range(self.m), key=lambda x: sum(self.distancias[x]), reverse=True
        )
        return facilidades

    def gerar_solucao_inicial_aleatoria(self):
        # gerar uma solucao inicial aleatoria
        facilidades = random.sample(range(self.m), self.m)
        return facilidades

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

    def executa(self):
        facilidades = self.gerar_solucao_inicial_gulosa()
        self.facilidades = facilidades
        self.best_solution = facilidades
        self.actual_cost = self.funcao_objetivo(facilidades)
        self.solution_cost = self.actual_cost
        print("*" * 50)
        print(f"Custo da solucao inicial: {self.actual_cost}")
        while self.temperature > 0.1:
            for _ in range(self.sa_max):
                vizinho = self.vizinhanca()
                custo_vizinho = self.funcao_objetivo(vizinho)
                if self.aceita_melhora(custo_vizinho):
                    self.facilidades = vizinho
                    self.actual_cost = custo_vizinho
                    if custo_vizinho > self.funcao_objetivo(self.best_solution):
                        self.best_solution = vizinho
                        self.solution_cost = custo_vizinho
            self.atualiza_temperatura()
        facilidades_abertas = self.best_solution[: self.p]
        print(f"Melhor solucao: \n{facilidades_abertas}")
        print(f"Custo da melhor solucao: {self.solution_cost}")
        print("*" * 50)
        return self.solution_cost
