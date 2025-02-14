import gurobipy as gp
from gurobipy import GRB
import itertools
import random
import csv
from validator import valida_resultado

def resolve_modelo(P, K, A, I, J, C, data_Q, q_pi_input):
    P1 = 1
    model = gp.Model()
    model.setParam("Heuristics", 0)
    model.setParam("Presolve", 0)

    # Atualizar Q_pka com base nos dados de entrada
    Q_pka = {(p, k, a): 0 for p in P for k in K for a in A}
    Q_pka.update(data_Q)

    corridor_indices = {k: idx + 1 for idx, k in enumerate(K)}
    C_to_index = {c: idx + 1 for idx, c in enumerate(C)}

    random.seed(42)

    # Dados q_pi fornecidos como entrada
    q_pi = q_pi_input

    # Gerar classes das caixas
    C_i = {i: random.choice(list(C_to_index.values())) for i in I}
    # Variáveis
    Z_j = model.addVars(J, vtype=GRB.INTEGER, lb=min(C_to_index.values()), ub=max(C_to_index.values()), name="Z_j")
    x_ij = model.addVars(I, J, vtype=GRB.BINARY, name="x_ij")
    t_kaj = model.addVars(K, A, J, vtype=GRB.BINARY, name="t_kaj")
    # Z_pkaj: Se algum produto foi escolhido em pkaj (Binário)
    Z_aj = model.addVars(A, J, vtype=GRB.BINARY, name="Z_aj")
    # Variável indicadora que será 1 se algum produto foi escolhido na onda j andar a (Binário)
    A_aj = model.addVars(A, J, vtype=GRB.BINARY, name="A_aj")
    print("terminou as variaveis")

    # E_pkaj: Quantity of product p picked from corridor k on floor a in wave j (InteiroNãoNegat.)
    E_pkaj = model.addVars(P, K, A, J, vtype=GRB.INTEGER, lb=0, name="E_pkaj")

    ## Variáveis da função objetivo
    # Maior número de corredor utilizado na onda j andar a
    G_ja = model.addVars(J, A, vtype=GRB.INTEGER, lb=0, ub=len(K), name="G_ja")
    # Menor número de corredor utilizado *
    L_ja = model.addVars(J, A, vtype=GRB.INTEGER, lb=0, ub=len(K), name="L_ja")

    # Constraints
    ## Capacity of waves
    model.addConstrs(
        (
            gp.quicksum(q_pi[p, i] * x_ij[i, j] for p in P for i in I) <= 6000
            for j in J
        ),
        name="wave_capacity"
    )

    # Add constraint: Each box is assigned to exactly one wave
    model.addConstrs(
        (gp.quicksum(x_ij[i, j] for j in J) == 1 for i in I),
        name="single_allocation"
    )

    for i in I:
        for j in J:
            # If x_ij[i,j] == 1 → C_i[i] == Z_j[j]
            model.addGenConstrIndicator(
                x_ij[i, j],  # Trigger variable
                True,  # Trigger when x_ij[i,j] == 1
                C_i[i] == Z_j[j],
                name=f"class_match_{i}_{j}"
            )

    # Add constraint: Sum of E_pkaj = Sum of q_pi * x_ij
    model.addConstrs(
        (
            gp.quicksum(E_pkaj[p, k, a, j] for a in A for k in K) ==
            gp.quicksum(q_pi[p, i] * x_ij[i, j] for i in I)
            for p in P
            for j in J
        ),
        name="picking_balance"
    )

    model.addConstrs(
        (
            gp.quicksum(E_pkaj[p, k, a, j] for j in J) <= Q_pka[p, k, a]
            for p in P
            for k in K
            for a in A
        ),
        name="max_picking_capacity"
    )
    for k in K:
        for a in A:
            for j in J:
                # If t_kaj = 0, then sum_p E_pkaj <= 0 (force t_kaj to 1 if sum_p E_pkaj > 0)
                model.addGenConstrIndicator(
                    t_kaj[k, a, j],  # Indicator variable
                    0,  # Trigger when t_kaj = 0
                    gp.quicksum(E_pkaj[p, k, a, j] for p in P) == 0,
                    name=f"t_kaj_zero_{k}_{a}_{j}"
                )
                model.addGenConstrIndicator(
                    t_kaj[k, a, j],  # Indicator variable
                    1,  # Trigger when t_kaj = 0
                    gp.quicksum(E_pkaj[p, k, a, j] for p in P) >= 1,
                    name=f"t_kaj_one_{k}_{a}_{j}"
                )

    for a in A:
        for j in J:
            # If t_kaj = 0, then sum_p E_pkaj <= 0 (force t_kaj to 1 if sum_p E_pkaj > 0)
            model.addGenConstrIndicator(
                Z_aj[a, j],  # Indicator variable
                0,  # Trigger when t_kaj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) == 0,
                name=f"Z_aj_zero_{a}_{j}"
            )
            model.addGenConstrIndicator(
                Z_aj[a, j],  # Indicator variable
                1,  # Trigger when t_kaj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) >= 1,
                name=f"Z_aj_one_{a}_{j}"
            )

    for a in A:
        for j in J:
            # If A_aj = 0, then sum_{p,k} E_pkaj <= 0 (force A_aj to 1 if sum > 0)
            model.addGenConstrIndicator(
                A_aj[a, j],  # Indicator variable
                0,  # Trigger when A_aj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) == 0,
                name=f"A_aj_zero_{a}_{j}"
            )
            model.addGenConstrIndicator(
                A_aj[a, j],  # Indicator variable
                1,  # Trigger when A_aj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) >= 1,
                name=f"A_aj_zero_{a}_{j}"
            )

    for a in A:
        for j in J:
            model.addGenConstrIndicator(
                Z_aj[a, j],
                0,
                G_ja[j, a] == 0,
                name=f"G_ja_lower_{a}_{j}"
            )
            for k in K:
                k_idx = corridor_indices[k]  # Map corridor name to index (e.g., 'Corridor1' → 1)
            # If E_pkaj > 0, then G_ja >= k_idx
            model.addGenConstrIndicator(
                t_kaj[k, a, j],  # Condition: E_pkaj > 0
                1,  # Trigger when condition is true
                G_ja[j, a] >= k_idx,  # Enforce G_ja >= k_idx
                name=f"G_ja_upper_{k}_{a}_{j}"
            )


    for a in A:
        for j in J:
            model.addGenConstrIndicator(
                Z_aj[a, j],
                0,
                L_ja[j, a] == 0,
                name=f"L_ja_lower_{a}_{j}"
            )
            for k in K:
                k_idx = corridor_indices[k]  # Map corridor name to index (e.g., 'Corridor1' → 1)
                # If E_pkaj > 0, then L_ja <= k_idx
                model.addGenConstrIndicator(
                    t_kaj[k, a, j],  # Condition: E_pkaj > 0
                    1,  # Trigger when condition is true
                    L_ja[j, a] <= k_idx,  # Enforce L_ja <= k_idx
                    name=f"L_ja_upper_{k}_{a}_{j}"
                )

    # Objective Function
    Z = gp.quicksum(
        (G_ja[j, a] - L_ja[j, a]) + P1 * A_aj[a, j] + gp.quicksum(t_kaj[k, a, j] for k in K)
        for a in A for j in J
    )
    model.setObjective(Z, sense=GRB.MINIMIZE)

    # Solve the model
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print("Solução ótima encontrada!")
        for j in J:  # Itera sobre as ondas
            print(f"\nOnda {j}:")

            # Lista de corredores usados na onda
            corredores_usados = [
                k for a in A for k in K if t_kaj[k, a, j].x >= 1
            ]

            # Lista de caixas alocadas na onda
            caixas_alocadas = [
                i for i in I if any(x_ij[i, j].x >= 1 for j in J)
            ]

            # Quantidade total de produtos escolhidos na onda
            quantidade_produtos = sum(
                E_pkaj[p, k, a, j].x for p in P for k in K for a in A
            )

            # Mapeamento corredor -> caixas
            corredor_caixa = {
                k: [
                    i for i in I
                    if any(E_pkaj[p, k, a, j].x > 0 for p in P for a in A)
                ]
                for k in K
            }

            print(f"  Corredores: {corredores_usados}")
            print(f"  Caixas: {caixas_alocadas}")
            print(f"  Quantidade de produtos: {quantidade_produtos}")
            print(f"  Corredor-caixa: {corredor_caixa}")

            csv_data = set()

            for j in J:  # Iterar sobre as ondas
                for i in I:  # Iterar sobre as caixas
                    for p in P:  # Iterar sobre os produtos
                        for k in K:  # Iterar sobre os corredores
                            for a in A:  # Iterar sobre os andares
                                # Filtrar somente caixas alocadas e com PECAS > 0
                                if x_ij[i, j].x > 0.5 and q_pi[p, i] > 0:
                                    if t_kaj[k, a, j].x > 0.5:  # Apenas se o corredor foi usado
                                        # Adicionar como tupla ao conjunto
                                        csv_data.add((
                                            j,  # ONDA
                                            i,  # CAIXA
                                            int(q_pi[p, i]),  # PECAS
                                            f"CLASSE_ONDA_{int(Z_j[j].x)}",  # CLASSE_ONDA
                                            p,  # SKU
                                            k,  # Corredor
                                            a  # Andar
                                        ))

                # Escrever o arquivo CSV
            with open("resultado_modelo_filtrado.csv", "w", newline="") as csvfile:
                fieldnames = ["ONDA", "CAIXA", "PECAS", "CLASSE_ONDA", "SKU", "Corredor", "Andar"]
                writer = csv.writer(csvfile)

                writer.writerow(fieldnames)  # Escrever cabeçalhos
                writer.writerows(csv_data)  # Escrever dados sem duplicatas

            # Validar o resultado
            valida_resultado(q_pi, Q_pka, corridor_indices, I, J, P, K, A, Z_j, x_ij, t_kaj, E_pkaj, C_i)

    else:
        print("Nenhuma solução encontrada.")