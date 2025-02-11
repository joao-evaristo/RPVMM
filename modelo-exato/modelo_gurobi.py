import gurobipy as gp
from gurobipy import GRB
import itertools
import random

model = gp.Model()
model.setParam("Heuristics", 0)
model.setParam("Presolve", 0)

# Dados e Parâmetros
P = ['Product1', 'Product2']
K = ['Corridor1', 'Corridor2', 'Corridor3']
A = ['Floor1', 'Floor2']
I = ['Box1', 'Box2', 'Box3']
J = ['Wave1', 'Wave2']
C = ['Class1', 'Class2']

data_Q = {
    ('Product1', 'Corridor1', 'Floor1'): 100,
    ('Product1', 'Corridor2', 'Floor1'): 200,
    ('Product2', 'Corridor1', 'Floor1'): 150,
    ('Product2', 'Corridor2', 'Floor2'): 250,
}

Q_pka = {(p, k, a): 0 for p in P for k in K for a in A}
Q_pka.update(data_Q)

corridor_indices = {'Corridor1': 1, 'Corridor2': 2, 'Corridor3': 3}
C_to_index = {'Class1': 1, 'Class2': 2}

random.seed(42)

# Gerando Caixas
q_pi = {}
for p in P:
    for i in I:
        q_pi[(p, i)] = random.randint(0, 20)

print("q_pi (Product, Box): Quantity")
for (p, i), q in q_pi.items():
    print(f"q_{p}_{i}: {q}")


C_i = {}
for i in I:
    C_i[i] = random.choice([1, 2])  # Class indices (1=Class1, 2=Class2)

print("\nC_i (Box): Class")
for i, c in C_i.items():
    print(f"C_{i}: {c}")

P1 = 1
# Variáveis


# Z_j: Classe de onda da onda j (Inteiro)
Z_j = model.addVars(J, vtype=GRB.INTEGER, lb=min(C_to_index.values()), ub=max(C_to_index.values()), name="Z_j")

# x_ij: Indica se a caixa i foi alocada a onda j (Binário)
x_ij = model.addVars(I, J, vtype=GRB.BINARY, name="x_ij")

# t_kaj: Se algum produto foi escolhido do corredor k no andar a e na onda j (Binário)
t_kaj = model.addVars(K, A, J, vtype=GRB.BINARY, name="t_kaj")
# Z_pkaj: Se algum produto foi escolhido em pkaj (Binário) 
Z_pkaj = model.addVars(P, K, A, J, vtype=GRB.BINARY, name="Z_pkaj")
# Variável indicadora que será 1 se algum produto foi escolhido na onda j andar a (Binário) 
A_aj = model.addVars(A, J, vtype=GRB.BINARY, name="A_aj")

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
            True,        # Trigger when x_ij[i,j] == 1
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
                0,               # Trigger when t_kaj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P) == 0,
                name=f"t_kaj_zero_{k}_{a}_{j}"
            )
            model.addGenConstrIndicator(
                t_kaj[k, a, j],  # Indicator variable
                1,               # Trigger when t_kaj = 0
                gp.quicksum(E_pkaj[p, k, a, j] for p in P) >= 1,
                name=f"t_kaj_zero_{k}_{a}_{j}"
            )
for p in P:
	for k in K:
		for a in A:
		    for j in J:
		        # If t_kaj = 0, then sum_p E_pkaj <= 0 (force t_kaj to 1 if sum_p E_pkaj > 0)
		        model.addGenConstrIndicator(
		            Z_pkaj[p, k, a, j],  # Indicator variable
		            0,               # Trigger when t_kaj = 0
		            gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) == 0,
		            name=f"Z_pkaj_zero_{p}_{k}_{a}_{j}"
		        )
		        model.addGenConstrIndicator(
		            Z_pkaj[p, k, a, j],  # Indicator variable
		            1,               # Trigger when t_kaj = 0
		            gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) >= 1,
		            name=f"Z_pkaj_zero_{p}_{k}_{a}_{j}"
		        )


for a in A:
    for j in J:
        # If A_aj = 0, then sum_{p,k} E_pkaj <= 0 (force A_aj to 1 if sum > 0)
        model.addGenConstrIndicator(
            A_aj[a, j],  # Indicator variable
            0,           # Trigger when A_aj = 0
            gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) == 0,
            name=f"A_aj_zero_{a}_{j}"
        )
        model.addGenConstrIndicator(
            A_aj[a, j],  # Indicator variable
            1,           # Trigger when A_aj = 0
            gp.quicksum(E_pkaj[p, k, a, j] for p in P for k in K) >= 1,
            name=f"A_aj_zero_{a}_{j}"
        )

for k in K:
    k_idx = corridor_indices[k]  # Map corridor name to index (e.g., 'Corridor1' → 1)
    for a in A:
        for j in J:
            for p in P:
                # If E_pkaj > 0, then G_ja >= k_idx
                model.addGenConstrIndicator(
                    t_kaj[k, a, j],  # Condition: E_pkaj > 0
                    1,                         # Trigger when condition is true
                    G_ja[j, a] >= k_idx,       # Enforce G_ja >= k_idx
                    name=f"G_ja_lower_{p}_{k}_{a}_{j}"
                )
                model.addGenConstrIndicator(
                    t_kaj[k, a, j],  # Condition: E_pkaj > 0
                    0,                         # Trigger when condition is true
                    G_ja[j, a] >= 0,       # Enforce L_ja <= k_idx
                    name=f"G_ja_lower_{p}_{k}_{a}_{j}"
                )

for k in K:
    k_idx = corridor_indices[k]  # Map corridor name to index (e.g., 'Corridor1' → 1)
    for a in A:
        for j in J:
            for p in P:
                # If E_pkaj > 0, then L_ja <= k_idx
                model.addGenConstrIndicator(
                    Z_pkaj[p, k, a, j],  # Condition: E_pkaj > 0
                    1,                         # Trigger when condition is true
                    L_ja[j, a] <= k_idx,       # Enforce L_ja <= k_idx
                    name=f"L_ja_upper_{p}_{k}_{a}_{j}"
                )
                model.addGenConstrIndicator(
                    Z_pkaj[p, k, a, j],  # Condition: E_pkaj > 0
                    0,                         # Trigger when condition is true
                    L_ja[j, a] == 0,       # Enforce L_ja <= k_idx
                    name=f"L_ja_upper_{p}_{k}_{a}_{j}"
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
	print("Optimal solution found:")
	for j in J:
		for a in A:
			print(f"Wave {j}, Floor {a}:")
			print(f"  G_ja = {G_ja[j, a].x}, L_ja = {L_ja[j, a].x}, A_aj = {A_aj[a, j].x}")
			print(f"  Corridors used: {[k for k in K if t_kaj[k, a, j].X >= 1]}")

	for j_idx, j in enumerate(J,1):
		for a_idx, a in enumerate(A,1):
			print(f"L_{j_idx}{a_idx}: {L_ja[j, a].X}") # Menor corredor da onda
			print(f"G_{j_idx}{a_idx}: {G_ja[j, a].X}") # Maior corredor, se nao escolhidos sao nulos
			for k_idx, k in enumerate(K,1):
				print(f"t_{k_idx}{a_idx}{j_idx}: {t_kaj[k,a,j].X}") # Binario onda/andar corredor item escolhido. QUantos corredores foram visitados 
				for p_idx, p in enumerate(P,1):
					print(f"E_{p_idx}{k_idx}{a_idx}{j_idx}: {E_pkaj[p,k,a,j].X}") # Quantidade associada ao pkj quantidade escolhudo do produto
else:
    print("No solution found.")

