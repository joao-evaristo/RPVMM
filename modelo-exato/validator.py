import itertools

def valida_resultado(q_pi, Q_pka, corridor_indices, I, J, P, K, A, Z_j, x_ij, t_kaj, E_pkaj, C_i):
    erros = []

    # Valida capacidade máxima de cada onda
    for j in J:
        total_pecas_onda = sum(q_pi[p, i] * x_ij[i, j].x for p in P for i in I)
        if total_pecas_onda > 6000:
            erros.append(f"Onda {j} excede a capacidade máxima de 6000 peças com {total_pecas_onda} peças.")

    # Valida alocação única de caixas
    for i in I:
        total_alocado = sum(x_ij[i, j].x for j in J)
        if total_alocado != 1:
            erros.append(f"A caixa {i} não foi alocada a exatamente uma onda.")

    # Valida correspondência de classe
    for i in I:
        for j in J:
            if x_ij[i, j].x > 0.5 and C_i[i] != Z_j[j].x:
                erros.append(f"A caixa {i} (classe {C_i[i]}) foi alocada à onda {j} com classe {Z_j[j].x}.")

    # Valida corredores usados e produtos coletados
    for j in J:
        for k in K:
            for a in A:
                if t_kaj[k, a, j].x > 0.5:
                    total_produtos_corredor = sum(E_pkaj[p, k, a, j].x for p in P)
                    if total_produtos_corredor == 0:
                        erros.append(
                            f"O corredor {k} no andar {a} foi marcado como usado na onda {j}, mas nenhum produto foi coletado.")

    # Resultado da validação
    if not erros:
        print("O resultado do modelo é válido.")
    else:
        print("Erros encontrados na validação:")
        for erro in erros:
            print(f"- {erro}")
