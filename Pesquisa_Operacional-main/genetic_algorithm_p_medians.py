import copy
import random
import math
from ManipuladorArquivo import ManipuladorArquivo
from ordered_crossover import ordered_crossover


def decisao(probabilidade):
    return random.random() < probabilidade


class GeneticAlgorithm:
    def __init__(
        self,
        n,
        I,
        m,
        J,
        p,
        distancias,
        n_populacao_inicial=100,
        taxa_elitismo=0.10,
        tamanho_populacao=30,
        taxa_cruzamento=0.3,
        taxa_mutacao=0.2,
        n_geracoes=1000,
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
        self.n_populacao_inicial = n_populacao_inicial
        self.taxa_elitismo = taxa_elitismo
        self.tamanho_populacao = tamanho_populacao
        self.taxa_cruzamento = taxa_cruzamento
        self.taxa_mutacao = taxa_mutacao
        self.n_geracoes = n_geracoes
        self.populacao = self.gerar_populacao_inicial()

    def gerar_populacao_inicial(self):
        # gerar uma populacao inicial aleatoria
        populacao = []
        for i in range(self.n_populacao_inicial):
            facilidades_aleatorias = random.sample(range(self.m), self.p)
            populacao.append(facilidades_aleatorias)
        return populacao

    def define_atendimento(self, facilidades):
        # definir o atendimento de cada cliente
        # cada cliente deve ser atendido pela facilidade mais proxima
        # cada cliente e atendido por apenas uma facilidade
        xij = [None] * self.n
        facilidades_abertas = facilidades
        for i in range(self.n):
            menor_distancia = float("inf")
            for j in facilidades_abertas:
                if self.distancias[j][i] < menor_distancia:
                    menor_distancia = self.distancias[j][i]
                    xij[i] = j
        return xij

    def fitness(self, s):
        # para cada cliente, somar a distancia entre ele e a facilidade que o atende
        # a funcao objetivo e maximizar a soma das distancias da distancia minima entre cada facilidade e cada cliente
        xij = self.define_atendimento(s)
        custo = 0
        for i, j in enumerate(xij):
            custo += self.distancias[j][i]
        return custo

    def classificar_individuos(self):
        self.populacao.sort(key=self.fitness, reverse=True)

    def mutacao(self, individuo):
        individuo_mutado = copy.deepcopy(individuo)
        quantidade_genes_mutados = random.choices(
            [5, 10, 20], weights=[80, 15, 5], k=1
        )[0]
        facilidades_possiveis = [i for i in range(self.m) if i not in individuo_mutado]
        facilidades_escolhidas = random.sample(
            facilidades_possiveis, quantidade_genes_mutados
        )
        index_facilidades_mutadas = random.sample(
            range(len(individuo_mutado)), quantidade_genes_mutados
        )
        for i, j in zip(index_facilidades_mutadas, facilidades_escolhidas):
            individuo_mutado[i] = j
        return individuo_mutado

    def selecionar_individuos(self):
        tamanho_elite = int(len(self.populacao) * self.taxa_elitismo)
        populacao_restante = self.populacao[tamanho_elite:]
        populacao_selecionada = self.populacao[:tamanho_elite]
        taxa_de_selecao = 0.6
        while len(populacao_selecionada) < self.tamanho_populacao:
            for individuo in populacao_restante:
                if decisao(taxa_de_selecao):
                    populacao_selecionada.append(individuo)
                    taxa_de_selecao = taxa_de_selecao * 0.80
        self.populacao = populacao_selecionada

    def cruzar_individuos(self, individuo1, individuo2):
        filho1, filho2 = ordered_crossover(individuo1, individuo2)
        return filho1, filho2

    def cruzar_populacao(self):
        tamanho_reprodutores = int(len(self.populacao) * self.taxa_cruzamento)
        reprodutores = copy.deepcopy(self.populacao[:tamanho_reprodutores])
        if len(reprodutores) % 2 != 0:
            reprodutores.append(reprodutores[0])
        for i in range(0, len(reprodutores), 2):
            filho_1, filho_2 = self.cruzar_individuos(
                reprodutores[i], reprodutores[i + 1]
            )
            if decisao(self.taxa_mutacao):
                filho_1 = self.mutacao(filho_1)
            if decisao(self.taxa_mutacao):
                filho_2 = self.mutacao(filho_2)
            self.populacao.append(filho_1)
            self.populacao.append(filho_2)

    def fazer_mutacao(self):
        pass

    def executar(self):
        self.classificar_individuos()
        for _ in range(self.n_geracoes):
            self.selecionar_individuos()
            self.cruzar_populacao()
            self.classificar_individuos()
        return self.fitness(self.populacao[0])
