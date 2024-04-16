import gurobipy as gp
from gurobipy import GRB, or_
import sys

def setMonomial(I, n):
    L = [0] * n
    for i in I:
        L[i] = 1
    return L

ROUNDS           = int(sys.argv[1])
STATE_SIZE       = 257
NUMBER_OF_GROUPS = 32
DATA_SIZE        = NUMBER_OF_GROUPS * 2

data_vector = setMonomial([int(i) for i in sys.argv[3].split(",")], DATA_SIZE)
key_vector  = setMonomial([int(i) for i in sys.argv[4].split(",")], STATE_SIZE)
coordinate  = int(sys.argv[2])

env = gp.Env(empty=True)
env.setParam("OutputFlag", 0)
env.start()
model = gp.Model('kirby', env=env)

model.setParam(GRB.Param.PoolSearchMode, 2)
model.setParam(GRB.Param.PoolSolutions, 200000)

#### Variables related to injection function. ####

# Key input. 
k = model.addVars(STATE_SIZE, vtype=GRB.BINARY, name='k')

# Diversifier input of 64 bits to construction.
# Indexing is as follows: (group, bit).
d = model.addVars(NUMBER_OF_GROUPS, 2, vtype=GRB.BINARY, name='d')

# Copies of inputs.
# Indexing is as follows: (group, AND-gate, bit).
c = model.addVars(NUMBER_OF_GROUPS, 2, 4, vtype=GRB.BINARY, name='c')
and_gate_input = model.addVars(NUMBER_OF_GROUPS, 2, 4, vtype=GRB.BINARY, name='and_gate_input')

# Output of non-linear layer of injection function.
# Indexing is as follows: (group, AND-gate).
n = model.addVars(NUMBER_OF_GROUPS, 4, vtype=GRB.BINARY, name='n')

#### Variables related to round function. ####

# Output of round i.
s = model.addVars(ROUNDS + 1, STATE_SIZE, vtype=GRB.BINARY, name='s')

# Output of pi of round i.
p = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='p')

# Output of theta of round i.
t = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='t')

# Output of iota of round i.
iota = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='iota')

# Auxiliary variables for copies inside of theta and chi of round i.
u = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='u')
v = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='v')
w = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='w')
x = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='x')
y = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='y')
z = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='z')
z2 = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='z2')

# Auxiliary variables for AND gate inside of chi of round i.
a = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='a')

# Set input vectors.
model.addConstrs(d[i, j] == data_vector[2*i + j] for i in range(NUMBER_OF_GROUPS) for j in range(2))
model.addConstrs(k[i]    == key_vector[i]        for i in range(STATE_SIZE))

# Set injection function constraints.

# Copy constraints.
for i in range(NUMBER_OF_GROUPS):
    for j in range(2):
        model.addConstr(d[i, j] == or_([c[i, j, 0], c[i, j, 1], c[i, j, 2], c[i, j, 3]]))

# Constraints for the layer of AND gates.
for i in range(NUMBER_OF_GROUPS):
    model.addConstr(c[i, 0, 0] <= and_gate_input[i, 0, 0])
    model.addConstr(c[i, 1, 0] <= and_gate_input[i, 1, 0])
    model.addConstr(c[i, 0, 1] <= and_gate_input[i, 0, 1])
    model.addConstr(c[i, 1, 1] == and_gate_input[i, 1, 1])
    model.addConstr(c[i, 0, 2] == and_gate_input[i, 0, 2])
    model.addConstr(c[i, 1, 2] <= and_gate_input[i, 1, 2])
    model.addConstr(c[i, 0, 3] == and_gate_input[i, 0, 3])
    model.addConstr(c[i, 1, 3] == and_gate_input[i, 1, 3])
    for j in range(4):
        model.addConstr(n[i, j] == and_gate_input[i, 0, j])
        model.addConstr(n[i, j] == and_gate_input[i, 1, j])

# Constraints for the bit permutation.
model.addConstrs(s[0, i] == k[i] + n[i % NUMBER_OF_GROUPS, i // NUMBER_OF_GROUPS] for i in range(4 * NUMBER_OF_GROUPS))
model.addConstrs(s[0, i] == k[i] for i in range(4 * NUMBER_OF_GROUPS, STATE_SIZE))

# Set round function constraints.
for i in range(ROUNDS):
    # Constraints for pi.
    model.addConstrs(p[i, j] == s[i, (121*j) % STATE_SIZE] for j in range(STATE_SIZE))
    # Constraints for theta.
    model.addConstrs(p[i, j] == or_([u[i, j], v[i, j], w[i, j]]) for j in range(STATE_SIZE)) # Copies.
    model.addConstrs(t[i, j] == u[i, j] + v[i, (j+3) % STATE_SIZE] + w[i, (j+10) % STATE_SIZE] for j in range(STATE_SIZE)) # XOR.
    # Constraints for iota.
    model.addConstrs(t[i, j] == iota[i, j] if j != 0 else t[i, j] <= iota[i, j] for j in range(STATE_SIZE))
    model.addConstrs(iota[i, j] == or_([x[i, j], y[i, j], z[i, j], z2[i, j]]) for j in range(STATE_SIZE)) # Copies.
    # Constraints for chi.
    model.addConstrs(a[i, j] == y[i, (j+1) % STATE_SIZE] for j in range(STATE_SIZE)) # AND gate.
    model.addConstrs(a[i, j] == z[i, (j+2) % STATE_SIZE] for j in range(STATE_SIZE))
    model.addConstrs(s[i + 1, j] == x[i, j] + a[i, j] + z2[i, (j+2) % STATE_SIZE] for j in range(STATE_SIZE)) # XOR.

model.addConstrs(s[ROUNDS, i] == 1 if i == coordinate else s[ROUNDS, i] == 0 for i in range(STATE_SIZE))

model.optimize()

# Print number of solutions stored
nSolutions = model.SolCount
print('Number of solutions equals', nSolutions)
print('Coefficient is', nSolutions % 2)

#for sol in range(nSolutions):
    #model.setParam(GRB.Param.SolutionNumber, sol)

    #all_vars = model.getVars()
    #values = model.getAttr("Xn", all_vars)
    #names = model.getAttr("VarName", all_vars)

    #for name, val in zip(names, values):
        #print(f"{name} = {val}")
