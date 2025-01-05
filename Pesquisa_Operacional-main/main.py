from ManipuladorArquivo import ManipuladorArquivo
from simulated_annealing_p_medians import SimulatedAnnealing
import matplotlib.pyplot as plt
import time

if __name__ == "__main__":
    ma = ManipuladorArquivo("pmed40.txt.table.p56.B")
    distancias = ma.obter_distancias_facilidades()
    n = ma.obter_n_clients()
    I = ma.obter_clientes()
    m = ma.obter_m_facilities()
    J = ma.obter_facilidades()
    p = ma.obter_p_desired_facilities()
    custos = []
    tempos = []
    for i in range(10):
        tempo_inicial = time.time()
        sa = SimulatedAnnealing(n, I, m, J, p, distancias, 10000, 0.99, 20)
        custos.append(sa.executa())
        tempo_final = time.time()
        tempos.append(tempo_final - tempo_inicial)
    execucoes = [i for i in range(len(custos))]
    plt.plot(execucoes, custos, "ro")
    plt.xlabel("Iteração")
    plt.ylabel("Custo")
    plt.title("Custo x Iteração")
    plt.savefig("custo_x_iteracao.png")

    plt.clf()
    plt.plot(execucoes, tempos)
    plt.xlabel("Iteração")
    plt.ylabel("Tempo (s)")
    plt.title("Tempo x Iteração")
    plt.savefig("tempo_x_iteracao.png")
