import random
import math


class SimulatedAnnealing:
    def __init__(
        self,
        n,
        I,
        m,
        J,
        p,
        distancias,
        temperatura_inicial=1000,
        alpha=0.99,
        sa_max=10,
    ):
        self.n = n  # numero de clientes
        self.I = I  # conjunto de clientes
        self.m = m  # numero de facilidades
        self.J = J  # conjunto das facilidades candidatas
        self.p = p  # numero de facilidades a serem abertas
        self.distancias = (
            distancias  # matriz de distancias entre a facilidade j e o cliente i
        )
        self.facilidades = []
        self.melhor_solucao = None
        self.custo_atual = 0
        self.custo_solucao = 0
        self.temperatura_inicial = temperatura_inicial
        self.temperatura = self.temperatura_inicial
        self.alpha = alpha
        self.sa_max = sa_max

    def gerar_solucao_inicial_gulosa(self):
        # usar estrategia gulosa
        # pegar as facilidades, cujo a soma das distancias para os clientes seja a maior
        # e que ainda nao foram abertas
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
        if self.temperatura > 0.5 * self.temperatura_inicial:
            pesos = [0.6, 0.30, 0.10]
        elif self.temperatura > 0.2 * self.temperatura_inicial:
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
        if custo_vizinho > self.custo_atual:
            return True
        else:
            # utiliza o criterio de metropolis
            delta = custo_vizinho - self.custo_atual
            return random.random() < math.exp(delta / self.temperatura)

    def atualiza_temperatura(self):
        # atualiza a temperatura
        # utiliza o fast simulated annealing
        self.temperatura = self.temperatura * self.alpha

    def executa(self):
        facilidades = self.gerar_solucao_inicial_gulosa()
        self.facilidades = facilidades
        self.melhor_solucao = facilidades
        self.custo_atual = self.funcao_objetivo(facilidades)
        self.custo_solucao = self.custo_atual
        print("*" * 50)
        print(f"Custo da solucao inicial: {self.custo_atual}")
        while self.temperatura > 0.1:
            for _ in range(self.sa_max):
                vizinho = self.vizinhanca()
                custo_vizinho = self.funcao_objetivo(vizinho)
                if self.aceita_melhora(custo_vizinho):
                    self.facilidades = vizinho
                    self.custo_atual = custo_vizinho
                    if custo_vizinho > self.funcao_objetivo(self.melhor_solucao):
                        self.melhor_solucao = vizinho
                        self.custo_solucao = custo_vizinho
            self.atualiza_temperatura()
        facilidades_abertas = self.melhor_solucao[: self.p]
        print(f"Melhor solucao: \n{facilidades_abertas}")
        print(f"Custo da melhor solucao: {self.custo_solucao}")
        print("*" * 50)
        return self.custo_solucao
