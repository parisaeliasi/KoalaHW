import gurobipy as gp
from gurobipy import GRB
import time

ROUNDS           = 6
STATE_SIZE       = 257
NUMBER_OF_GROUPS = 32

env = gp.Env(empty=True)
env.setParam("OutputFlag", 0)
env.start()
model = gp.Model('kirby', env=env)

#### Variables related to injection function. ####

# Diversifier input of 64 bits to construction.
# Indexing is as follows: (group, bit).
d = model.addVars(NUMBER_OF_GROUPS, 2, vtype=GRB.BINARY, name='d')

# Copies of inputs.
# Indexing is as follows: (group, AND-gate, bit).
c = model.addVars(NUMBER_OF_GROUPS, 2, 4, vtype=GRB.BINARY, name='c')

# Output of non-linear layer of injection function.
# Indexing is as follows: (group, AND-gate).
n = model.addVars(NUMBER_OF_GROUPS, 4, vtype=GRB.BINARY, name='n')

# Output of bit permutation of injection function.
b = model.addVars(STATE_SIZE, vtype=GRB.BINARY, name='b')

#### Variables related to round function. ####
# Indexing is as follows: (round, bit).

# Output of round i.
s = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='s')

# Output of pi of round i.
p = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='p')

# Output of theta of round i.
t = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='t')

# Auxiliary variables for copies inside of theta and chi of round i.
u = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='u')
v = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='v')
w = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='w')
x = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='x')
y = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='y')
z = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='z')

# Auxiliary variables for AND gate inside of chi of round i.
a = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='a')

#### Constraints. In general, we leave out the inverters, because they are equivalent to an XOR with a constant (1). #### 

# Set injection function constraints.

# Copy constraints.
for i in range(NUMBER_OF_GROUPS):
    for j in range(2):
        model.addConstr(c.sum(i, j, '*') == d[i, j])

# Constraints for the layer of AND gates.
for i in range(NUMBER_OF_GROUPS):
    for j in range(4):
        model.addConstr(c[i, 0, j] + c[i, 1, j] >= n[i, j])
        model.addConstr(c[i, 0, j] + c[i, 1, j] <= 2*n[i, j])

# Constraints for the bit permutation.
model.addConstrs(b[i] == n[i % NUMBER_OF_GROUPS, i // NUMBER_OF_GROUPS] for i in range(4 * NUMBER_OF_GROUPS))
model.addConstrs(b[i] == 0 for i in range(4 * NUMBER_OF_GROUPS, STATE_SIZE))

# Set round function constraints.

for i in range(ROUNDS):
    # Constraints for pi.
    if i == 0:
        model.addConstrs(p[i, j] == b[(121*j) % STATE_SIZE] for j in range(STATE_SIZE))
    else:
        model.addConstrs(p[i, j] == s[i-1, (121*j) % STATE_SIZE] for j in range(STATE_SIZE))
    # Constraints for theta.
    model.addConstrs(u[i, j] + v[i, j] + w[i, j] == p[i, j] for j in range(STATE_SIZE)) # Copies.
    model.addConstrs(t[i, j] == u[i, j] + v[i, (j+3) % STATE_SIZE] + w[i, (j+10) % STATE_SIZE] for j in range(STATE_SIZE)) # XOR.
    # Constraints for chi.
    model.addConstrs(x[i, j] + y[i, j] + z[i, j]  == t[i, j] for j in range(STATE_SIZE)) # Copies.
    model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] >= a[i, j] for j in range(STATE_SIZE)) # AND gate.
    model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] <= 2*a[i, j] for j in range(STATE_SIZE)) # AND gate.
    model.addConstrs(x[i, j] + a[i, j]  == s[i, j] for j in range(STATE_SIZE)) # XOR.

# Set input vector.
model.addConstrs(d[i, j] == 1 for i in range(NUMBER_OF_GROUPS) for j in range(2))

# Set objective equal to the Hamming weight of the last vector in the division trail.
model.setObjective(s.sum(ROUNDS - 1, '*'), GRB.MINIMIZE)

# Save model for inspection.
model.write('kirby.lp')

# Callback fuction that checks whether the lower bound exceeds 1 or not. If it does, terminate the solver.
def checkLowerBound(model, where):
    if where == GRB.Callback.MIP:
        objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
        if objbnd > 1:
            print("objective bound = "+str(objbnd))
            model.terminate()

time_start = time.time()
print("Starting the solving process.")
unit_vectors_found = []
# To determine whether an integral distinguisher exists or not, we want to find STATE_SIZE unit vectors in the division property at the output.
while len(unit_vectors_found) < STATE_SIZE:
    # Solve the model, interrupting it when the lower bound exceeds 1.
    model.optimize(checkLowerBound)
    if model.status == GRB.OPTIMAL:
        if model.objVal != 1:
            print("Value of objective is not 1. Is this even possible with the custom termination? An integral distinguisher exists.")
            break
        else:
            for i in range(STATE_SIZE):
                if s[ROUNDS - 1, i].x == 1:
                    print("Found the " + str(i) + "'th unit vector")
                    unit_vectors_found.append(i)
                    print("Found " + str(len(unit_vectors_found)) + " out of " + str(STATE_SIZE) + " unit vectors.")
                    model.addConstr(s[ROUNDS - 1, i] == 0) # Set this unit vector to zero.
                    model.update()
                    break
    elif model.status == GRB.INTERRUPTED:
        print("Model was terminated. An integral distinguisher exists because not all unit vectors appear.")
        break
    else:
        print("Model could not be solved. This should not happen.") 
        break

time_end = time.time()
print("Computation took " + time.strftime("%H:%M:%S", time.gmtime(time_end - time_start)) + " seconds.")
print("Found the following unit vectors:")
unit_vectors_found.sort()
print(unit_vectors_found)
print("The number of unit vectors founds is equal to " + str(len(unit_vectors_found)))
print("Does the list contain duplicates? " + str(len(unit_vectors_found) != len(set(unit_vectors_found))))
