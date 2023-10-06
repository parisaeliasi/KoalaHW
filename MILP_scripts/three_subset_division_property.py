from collections import Counter
import gurobipy as gp
from gurobipy import *
import math
import time

ROUNDS                  = 2
STATE_SIZE              = 257
PARTIAL_ROUNDS          = STATE_SIZE
DIVERSIFIER_SIZE        = 64
NUMBER_OF_GROUPS        = DIVERSIFIER_SIZE // 2
BITS_IN_GROUP           = 4
VALUE_FOR_EXPANDED_PART = 0

core_operation_injection = [
    0x8, # (0, 0) |-> (1, 0, 0, 0)
    0x4, # (0, 1) |-> (0, 1, 0, 0)
    0x2, # (1, 0) |-> (0, 0, 1, 0) 
    0x1  # (1, 1) |-> (0, 0, 0, 1)
]

core_operation_round = [
	0x000,
	0x003,
	0x004,
	0x006,
	0x009,
	0x00a,
	0x00d,
	0x00f,
	0x011,
	0x012,
	0x014,
	0x016,
	0x018,
	0x01b,
	0x01d,
	0x01f,
	0x020,
	0x022,
	0x024,
	0x027,
	0x029,
	0x02b,
	0x02d,
	0x02e,
	0x030,
	0x032,
	0x035,
	0x036,
	0x039,
	0x03b,
	0x03c,
	0x03f,
	0x041,
	0x042,
	0x045,
	0x047,
	0x048,
	0x04b,
	0x04c,
	0x04e,
	0x050,
	0x053,
	0x055,
	0x057,
	0x059,
	0x05a,
	0x05c,
	0x05e,
	0x061,
	0x063,
	0x065,
	0x066,
	0x068,
	0x06a,
	0x06c,
	0x06f,
	0x071,
	0x073,
	0x074,
	0x077,
	0x078,
	0x07a,
	0x07d,
	0x07e,
	0x081,
	0x082,
	0x084,
	0x086,
	0x088,
	0x08b,
	0x08d,
	0x08f,
	0x090,
	0x093,
	0x094,
	0x096,
	0x099,
	0x09a,
	0x09d,
	0x09f,
	0x0a0,
	0x0a2,
	0x0a5,
	0x0a6,
	0x0a9,
	0x0ab,
	0x0ac,
	0x0af,
	0x0b0,
	0x0b2,
	0x0b4,
	0x0b7,
	0x0b9,
	0x0bb,
	0x0bd,
	0x0be,
	0x0c0,
	0x0c3,
	0x0c5,
	0x0c7,
	0x0c9,
	0x0ca,
	0x0cc,
	0x0ce,
	0x0d1,
	0x0d2,
	0x0d5,
	0x0d7,
	0x0d8,
	0x0db,
	0x0dc,
	0x0de,
	0x0e1,
	0x0e3,
	0x0e4,
	0x0e7,
	0x0e8,
	0x0ea,
	0x0ed,
	0x0ee,
	0x0f1,
	0x0f3,
	0x0f5,
	0x0f6,
	0x0f8,
	0x0fa,
	0x0fc,
	0x0ff,
	0x100,
	0x102,
	0x104,
	0x107,
	0x109,
	0x10b,
	0x10d,
	0x10e,
	0x110,
	0x112,
	0x115,
	0x116,
	0x119,
	0x11b,
	0x11c,
	0x11f,
	0x120,
	0x123,
	0x124,
	0x126,
	0x129,
	0x12a,
	0x12d,
	0x12f,
	0x131,
	0x132,
	0x134,
	0x136,
	0x138,
	0x13b,
	0x13d,
	0x13f,
	0x141,
	0x143,
	0x145,
	0x146,
	0x148,
	0x14a,
	0x14c,
	0x14f,
	0x151,
	0x153,
	0x154,
	0x157,
	0x158,
	0x15a,
	0x15d,
	0x15e,
	0x161,
	0x162,
	0x165,
	0x167,
	0x168,
	0x16b,
	0x16c,
	0x16e,
	0x170,
	0x173,
	0x175,
	0x177,
	0x179,
	0x17a,
	0x17c,
	0x17e,
	0x180,
	0x182,
	0x185,
	0x186,
	0x189,
	0x18b,
	0x18c,
	0x18f,
	0x190,
	0x192,
	0x194,
	0x197,
	0x199,
	0x19b,
	0x19d,
	0x19e,
	0x1a1,
	0x1a2,
	0x1a4,
	0x1a6,
	0x1a8,
	0x1ab,
	0x1ad,
	0x1af,
	0x1b0,
	0x1b3,
	0x1b4,
	0x1b6,
	0x1b9,
	0x1ba,
	0x1bd,
	0x1bf,
	0x1c1,
	0x1c3,
	0x1c4,
	0x1c7,
	0x1c8,
	0x1ca,
	0x1cd,
	0x1ce,
	0x1d1,
	0x1d3,
	0x1d5,
	0x1d6,
	0x1d8,
	0x1da,
	0x1dc,
	0x1df,
	0x1e0,
	0x1e3,
	0x1e5,
	0x1e7,
	0x1e9,
	0x1ea,
	0x1ec,
	0x1ee,
	0x1f1,
	0x1f2,
	0x1f5,
	0x1f7,
	0x1f8,
	0x1fb,
	0x1fc,
	0x1fe
]

# Returns True if the sum of the m'th output bit is unknown and False otherwise.
def exists_division_trail_over_construction(group_number, k, bit_number):
    #print("Entering exists_division_trail_over_construction")

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    model = gp.Model('kirby_injection_and_rounds', env=env)

    # Diversifier input of 64 bits to construction.
    # Indexing is as follows: (group, bit).
    d = model.addVars(NUMBER_OF_GROUPS - group_number, 2, vtype=GRB.BINARY, name='d')

    # Copies of inputs.
    # Indexing is as follows: (group, left input or right input of AND gate, bit).
    c = model.addVars(NUMBER_OF_GROUPS - group_number, 2, BITS_IN_GROUP, vtype=GRB.BINARY, name='c')

    # Output of non-linear layer of injection function.
    # Indexing is as follows: (group, AND-gate).
    n = model.addVars(NUMBER_OF_GROUPS - group_number, BITS_IN_GROUP, vtype=GRB.BINARY, name='n')

    # Input of bit permutation of injection function.
    b_in = model.addVars(BITS_IN_GROUP * NUMBER_OF_GROUPS, vtype=GRB.BINARY, name='b_in')

    # Output of bit permutation of injection function.
    b_out = model.addVars(STATE_SIZE, vtype=GRB.BINARY, name='b_out')
        
    # Set input vector.
    # We only care about the d[i, j] s.t. i >= group_number. For those, copy the appropriate k[i] (the first 4*group_number bits of k[i] are irrelevant here)
    model.addConstrs(d[i, j] == k[BITS_IN_GROUP*group_number + 2*i + j] for i in range(NUMBER_OF_GROUPS - group_number) for j in range(2))

    for i in range(NUMBER_OF_GROUPS - group_number):
        # Copy constraints.
        for j in range(2):
            model.addConstr(c.sum(i, j, '*') == d[i, j])

        # Constraints for the layer of AND gates.
        for j in range(4):
            model.addConstr(c[i, 0, j] + c[i, 1, j] >= n[i, j])
            model.addConstr(c[i, 0, j] + c[i, 1, j] <= 2*n[i, j])

    # Set t[i] equal to k[i] for i < 4*group_number, set the other t[i] equal to n[i, j] outputs.
    model.addConstrs(b_in[i] == k[i] for i in range(BITS_IN_GROUP * group_number))
    model.addConstrs(b_in[i] == n[(i // BITS_IN_GROUP) - group_number, i % BITS_IN_GROUP] for i in range(BITS_IN_GROUP * group_number, BITS_IN_GROUP * NUMBER_OF_GROUPS))

    # Constraints for the bit permutation.
    model.addConstrs(b_out[i] == b_in[BITS_IN_GROUP * (i % NUMBER_OF_GROUPS) + (i // NUMBER_OF_GROUPS)] for i in range(BITS_IN_GROUP * NUMBER_OF_GROUPS))
    model.addConstrs(b_out[i] == VALUE_FOR_EXPANDED_PART for i in range(BITS_IN_GROUP * NUMBER_OF_GROUPS, STATE_SIZE))

    # Indexing is as follows: (round, bit).

    # Intermediate states.
    s = model.addVars(ROUNDS + 1, STATE_SIZE, vtype=GRB.BINARY, name='s')

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

    # Set state at the beginning of round 0.
    model.addConstrs(s[0, i] == b_out[i] for i in range(STATE_SIZE))

    for i in range(ROUNDS):
        # Constraints for pi.
        model.addConstrs(p[i, j] == s[i, (121*j) % STATE_SIZE] for j in range(STATE_SIZE))
        # Constraints for theta.
        model.addConstrs(u[i, j] + v[i, j] + w[i, j] == p[i, j] for j in range(STATE_SIZE)) # Copies.
        model.addConstrs(t[i, j] == u[i, j] + v[i, (j+3) % STATE_SIZE] + w[i, (j+10) % STATE_SIZE] for j in range(STATE_SIZE)) # XOR.
        # Constraints for chi.
        model.addConstrs(x[i, j] + y[i, j] + z[i, j]  == t[i, j] for j in range(STATE_SIZE)) # Copies.
        model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] >= a[i, j] for j in range(STATE_SIZE)) # AND gate.
        model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] <= 2*a[i, j] for j in range(STATE_SIZE)) # AND gate.
        model.addConstrs(x[i, j] + a[i, j]  == s[i + 1, j] for j in range(STATE_SIZE)) # XOR.

    # Set output vector.
    model.addConstrs(s[ROUNDS, i] == 1 if i == bit_number else s[ROUNDS, i] == 0 for i in range(STATE_SIZE))

    model.optimize()
    if model.status == GRB.OPTIMAL:
        return True
    
    return False

def getDependencies(i):
    return [ 
            (i +  1) % STATE_SIZE, 
            (i +  2) % STATE_SIZE,
            (i +  3) % STATE_SIZE,
            (i +  4) % STATE_SIZE,
            (i +  5) % STATE_SIZE,
            (i + 10) % STATE_SIZE,
            (i + 11) % STATE_SIZE,
            (i + 12) % STATE_SIZE
           ]

# Returns true if the sum of the m'th output bit is unknown and False otherwise.
def exists_division_trail_over_partial_rounds(round_number, partial_round_number, k, bit_number):
    #print("Entering exists_division_trail_over_partial_rounds")
    #print(k)

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    model = gp.Model('kirby_rounds_only', env=env)

    # Indexing is as follows: (round, bit).

    # Intermediate states.
    s = model.addVars(ROUNDS - round_number + 1, STATE_SIZE, vtype=GRB.BINARY, name='s')

    # Output of pi of round i.
    p = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='p')

    # Output of theta of round i.
    t = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='t')

    # Auxiliary variables for copies inside of theta and chi of round i.
    u = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='u')
    v = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='v')
    w = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='w')
    x = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='x')
    y = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='y')
    z = model.addVars(ROUNDS - round_number, STATE_SIZE, vtype=GRB.BINARY, name='z')

    # Auxiliary variables for AND gate inside of chi of round i.
    a = model.addVars(ROUNDS, STATE_SIZE, vtype=GRB.BINARY, name='a')

    # Constraints for pi.
    model.addConstrs(p[0, i] == k[(121*i) % STATE_SIZE] for i in range(STATE_SIZE))

    I = list(range(partial_round_number))
    J = list(range(partial_round_number, STATE_SIZE))
    c = model.addVars(STATE_SIZE, STATE_SIZE, vtype=GRB.BINARY, name='c')
    for i in range(STATE_SIZE):
        e = p[0, i] - c[i, i]

        for j in J:
            if i in getDependencies(j):
                e -= c[i, j]
        model.addConstr(e == 0)

    theta = model.addVars(STATE_SIZE, 3, vtype=GRB.BINARY, name='theta')
    theta_two = model.addVars(STATE_SIZE, 2, vtype=GRB.BINARY, name='theta_two')
    and_gate = model.addVars(STATE_SIZE, vtype=GRB.BINARY, name='and_gate')
                
    # Constraints for theta.
    model.addConstrs(theta[j, l] == c[(j + l) % STATE_SIZE, j] + c[(j + l + 3) % STATE_SIZE, j] + c[(j + l + 10) % STATE_SIZE, j] for l in range(3) for j in J) # XOR.
    # Constraints for theta_two duplication.
    model.addConstrs(theta_two[j, 0] + theta_two[j, 1] == theta[j, 2] for j in J)
    # Constraints for AND gate.
    model.addConstrs(theta[j, 1] + theta_two[j, 1] >=   and_gate[j] for j in J) # AND gate.
    model.addConstrs(theta[j, 1] + theta_two[j, 1] <= 2*and_gate[j] for j in J) # AND gate.
    # Constraints for output of first round.
    model.addConstrs(s[1, j] == theta[j, 0] + theta_two[j, 0] + and_gate[j] for j in J) # XOR.
    model.addConstrs(s[1, i] == c[i, i] + k[STATE_SIZE + i] for i in I)

    for i in range(1, ROUNDS - round_number):
        # Constraints for pi.
        model.addConstrs(p[i, j] == s[i, (121*j) % STATE_SIZE] for j in range(STATE_SIZE))
        # Constraints for theta.
        model.addConstrs(u[i, j] + v[i, j] + w[i, j] == p[i, j] for j in range(STATE_SIZE)) # Copies.
        model.addConstrs(t[i, j] == u[i, j] + v[i, (j+3) % STATE_SIZE] + w[i, (j+10) % STATE_SIZE] for j in range(STATE_SIZE)) # XOR.
        # Constraints for chi.
        model.addConstrs(x[i, j] + y[i, j] + z[i, j]  == t[i, j] for j in range(STATE_SIZE)) # Copies.
        model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] >= a[i, j] for j in range(STATE_SIZE)) # AND gate.
        model.addConstrs(y[i, (j+1) % STATE_SIZE] + z[i, (j + 2) % STATE_SIZE] <= 2*a[i, j] for j in range(STATE_SIZE)) # AND gate.
        model.addConstrs(x[i, j] + a[i, j]  == s[i + 1, j] for j in range(STATE_SIZE)) # XOR.

    # Set output unit vector.
    model.addConstrs(s[ROUNDS - round_number, i] == 1 if i == bit_number else s[ROUNDS - round_number, i] == 0 for i in range(STATE_SIZE))


    model.write("inspection.lp")

    model.optimize()
    if model.status == GRB.OPTIMAL:
        return True

    #model.computeIIS()
    #model.write("model.ilp")  

    return False

def bit_product(x, u):
    # Calculate x^u.
    if (x & u) == u:
        return 1
    return 0

def compute_anf(a):
    n = int(math.log2(len(a)))

    # Input is the value vector `a' of a Boolean function f.
    # Apply Moebius transform to value vector.
    for i in range(n):
        sz = (2 ** i)
        pos = 0
        while pos < len(a):
            for j in range(sz):
                a[pos + sz + j] = (a[pos + j] + a[pos + sz + j]) % 2
            pos = pos + (2 * sz)

    # b[u] is the coefficient of x^u in f.
    return a

def is_at_most(u, v):
    # Test whether u <= v or not.
    for i in range(len(u)):
        if u[i] > v[i]:
            return False

    return True

def is_lower_bounded(v, K):
    for k in K:
        if is_at_most(k, v):
            return True        

    return False

def reduce0(K):
    R = []
    for k in K:
        if not is_lower_bounded(k, R):
            R.append(k)

    return R

def reduce1(K, L):
    R = []
    for l in L:
        if not is_lower_bounded(l, K):
            R.append(l)

    return R

def convert_int_to_list(u, n):
    return [int(x) for x in bin(u)[2:].zfill(n)] 

def division_trails_over_vectorial_boolean_function(anf, n, m, K, l):
    #print("Entering division_trails_over_vectorial_boolean_function")

    K_new = []
    L_new = []
    for u in range(2 ** m):
        for v in range(2 ** n):
            # anf[u] is the ANF of F^u.
            # and[u][v] is the coefficient of x^v in F^u.
            if anf[u][v] == 1:
                u_list = convert_int_to_list(u, m)
                v_list = convert_int_to_list(v, n)
                # If there exists a k in K s.t. k <= v, then u becomes unknown.
                if is_lower_bounded(v_list, K):
                    K_new.append(u_list)
                # If S-box^u[l] == 1, then L.append(u)
                elif v_list == l:  
                    L_new.append(u_list)
                # else:
                #   bit is balanced.

    K_new = reduce0(K_new)
    L_new = reduce1(K_new, L_new)

    return (K_new, L_new)

def injection_permute(v):
    r = [0] * 128
    for i in range(4):
        for j in range(32):
            r[32*i + j] = v[4*j + i]

    return r

def bbdp_propagate_accurate_injection(core_operation_injection_dict, group_number, L):
    #print("Entering bbdp_propagate_accurate_injection")

    if group_number == NUMBER_OF_GROUPS:
        R = []
        for l in L:
            # Permute and expand.
            R.append(injection_permute(l) + ([VALUE_FOR_EXPANDED_PART] * (STATE_SIZE - 128)))
        L = R

        # DONT ADD KEY MATERIAL AT THE END, BUT INTRODUCE ASAP, ONE BLOCK OF KEY BITS AFTER EACH PARTIAL ROUND
        # MIGHT LEAD TO TWO SUBSET TRAILS QUICKER

        # Add key material, which leads to vectors for which the sum is unknown.
        K = []
        for i in range(128, STATE_SIZE):
            for l in L:
                if l[i] == 0:
                    K.append(l[0:i] + [1] + l[i+1:])
        
        # Reduce K and L.
        K = reduce0(K) # Not sure if this call is necessary.
        L = reduce1(K, L)

        return (K, L)
    else:
        L_counter = Counter()
        n = group_number * 4

        # Propagate each l in L individually.
        for l in L:
            # Propagate l through the non-linear layer of the injection function.
            V = core_operation_injection_dict[tuple(l[n:n+2])]

            for v in V:
                v = l[:n] + v + l[n+2:]  
                L_counter[tuple(v)] += 1

        # Only keep those l in the new L with odd multiplicity
        # 2 bits input.
        L = [list(l) for l, count in L_counter.items() if count % 2 == 1]

        # Add key material, which leads to vectors for which the sum is unknown.
        K = []
        for i in range(n, n+4):
            for l in L:
                if l[i] == 0:
                    K.append(l[0:i] + [1] + l[i+1:])
        
        # Reduce K and L.
        K = reduce0(K) # Not sure if this call is necessary.
        L = reduce1(K, L)

        return (K, L)

def isValidVectorForCompression(t):
    for i in range(STATE_SIZE):
        if t[121*i % STATE_SIZE] + t[i + STATE_SIZE] > 1:
            return False

    return True

def bbdp_propagate_accurate_partial_round(core_operation_round_dict, partial_round_number, L):
    #print("Entering bbdp_propagate_accurate_partial_round")

    T = []
    # Propagate each l individually and then only keep output vectors which occur an odd number of times.
    for l in L:
        # Craft input to the core function, taking the pi step function into account.
        l_core_operation_input = [l[(partial_round_number * 121 + 121) % STATE_SIZE], 
                                  l[(partial_round_number * 121 + 242) % STATE_SIZE], 
                                  l[(partial_round_number * 121 + 106) % STATE_SIZE], 
                                  l[(partial_round_number * 121 + 227) % STATE_SIZE], 
                                  l[(partial_round_number * 121 +  91) % STATE_SIZE], 
                                  l[(partial_round_number * 121 + 182) % STATE_SIZE], 
                                  l[(partial_round_number * 121 +  46) % STATE_SIZE], 
                                  l[(partial_round_number * 121 + 167) % STATE_SIZE]]
        
        # Find division trails that start from l over the core function.
        #print(l_core_operation_input)
        L_core_operation_output = core_operation_round_dict[tuple(l_core_operation_input)]
        #print(L_core_operation_output)

        # We keep track of (x_0, ..., x_{256}, F_0(x), ... F_{partial_round_number}(x))
        for l_core_operation_output in L_core_operation_output:
            l[(partial_round_number * 121 + 121) % STATE_SIZE] = l_core_operation_output[0]
            l[(partial_round_number * 121 + 242) % STATE_SIZE] = l_core_operation_output[1]
            l[(partial_round_number * 121 + 106) % STATE_SIZE] = l_core_operation_output[2]
            l[(partial_round_number * 121 + 227) % STATE_SIZE] = l_core_operation_output[3]
            l[(partial_round_number * 121 +  91) % STATE_SIZE] = l_core_operation_output[4]
            l[(partial_round_number * 121 + 182) % STATE_SIZE] = l_core_operation_output[5]
            l[(partial_round_number * 121 +  46) % STATE_SIZE] = l_core_operation_output[6]
            l[(partial_round_number * 121 + 167) % STATE_SIZE] = l_core_operation_output[7]
            T.append(l + [l_core_operation_output[8]])

    # Compress (x_0, ..., x_{256}, F_0(x), ..., F_{256}(x)) into (R_0(x), ..., R_{256}(x)), where $F_i(x) = R_i(x) ^ x_{121*i % STATE_SIZE}$.
    if partial_round_number == PARTIAL_ROUNDS - 1:    
        R = []
        for t in T:
            if isValidVectorForCompression(t):
                r = []
                for i in range(STATE_SIZE):
                    r.append(t[121*i % STATE_SIZE] + t[i + STATE_SIZE])
                R.append(r)
        T = R

    return ([], [list(l) for l, count in Counter([tuple(t) for t in T]).items() if count % 2 == 1])

# Determine the coefficient of bit m in the output. 
# This coefficient is 0, 1, or unknown (when dependent on the key).
def bbdp(core_operation_injection_dict, core_operation_round_dict, K, L, bit_number): 
    #print("Entering bbdp")

    for group_number in range(NUMBER_OF_GROUPS + 1):
        print("Injection. Iteration number {}. Size of K is {} and L is {}.".format(group_number, len(K), len(L)))
        for k in K:
            if exists_division_trail_over_construction(group_number, k, bit_number):
                # Stopping rule 1.
                return -1;               
            # else:
            #   remove k from K
        # If this line is reached, K has become the empty set.
    
        L_after_pruning = []
        for l in L:
            if exists_division_trail_over_construction(group_number, l, bit_number): 
               L_after_pruning.append(l)
    
        if len(L_after_pruning) == 0:
            # Stopping rule 2.
            return 0
    
        #print("Length of L after pruning is {}.".format(len(L_after_pruning)))
    
        K, L = bbdp_propagate_accurate_injection(core_operation_injection_dict, group_number, L_after_pruning)

    for round_number in range(ROUNDS):
        for partial_round_number in range(PARTIAL_ROUNDS):
            #print(round_number, partial_round_number)
            print("Rounds. Iteration number is ({}, {}). Size of K is {} and L is {}.".format(round_number, partial_round_number, len(K), len(L)))
            for k in K:
                if exists_division_trail_over_partial_rounds(round_number, partial_round_number, k, bit_number):
                    # Stopping rule 1.
                    return -1;               
                # else:
                #   remove k from K
            # If this line is reached, K has become the empty set.

            L_after_pruning = []
            #print("Printing L")
            for l in L:
                #print("l: ")
                #for i in range(len(l)):
                #    if l[i] != 0: print(i)

                if exists_division_trail_over_partial_rounds(round_number, partial_round_number, l, bit_number): 
                   L_after_pruning.append(l)

            if len(L_after_pruning) == 0:
                # Stopping rule 2.
                return 0

            #print("Printing L_after_pruning")
            #for l in L_after_pruning:
            #    print("l: ")
            #    for i in range(len(l)):
            #        if l[i] != 0: print(i)

            #print("Length of L after pruning is {}.".format(len(L_after_pruning)))
    
            K, L = bbdp_propagate_accurate_partial_round(core_operation_round_dict, partial_round_number, L_after_pruning)
    return 1

def setMonomial(I, n):
    L = [0] * n
    for i in I:
        L[i] = 1
    return L

def main():
    # Write F for the core operation of the injection function, i.e., the layer of AND gates and inverters, which maps two bits to four bits.
    # The entry anf_injection[u] represents the ANF of F^u.
    anf_injection = [[]] * (2 ** 4)
    for u in range(2 ** 4):
        value_vector = list(map(bit_product, core_operation_injection, [u] * (2 ** 4)))
        anf_injection[u] = compute_anf(value_vector)

    print("Precomputing division trails of core operation of injection function.")
    # Precompute division trails of the core operation of the injection function.
    # Store them in a dictionary.
    core_operation_injection_dict = dict()
    for i in range(2 ** 2):
        l = convert_int_to_list(i, 2)
        _, L = division_trails_over_vectorial_boolean_function(anf_injection, 2, 4, [], l)
        core_operation_injection_dict[tuple(l)] = L

    # Write F for the core operation of the round function, which maps nine bits to nine bits.
    # The entry anf_round[u] represents the ANF of F^u.
    anf_round = [[]] * (2 ** 9)
    for u in range(2 ** 9):
        value_vector = list(map(bit_product, core_operation_round, [u] * (2 ** 9)))
        anf_round[u] = compute_anf(value_vector)
 
    print("Precomputing division trails of core operation of function.")
    # Precompute division trails of the core operation of the round function.
    # Store them in a dictionary.
    core_operation_round_dict = dict()
    for i in range(2 ** 8):
        l = convert_int_to_list(i, 8)
        _, L = division_trails_over_vectorial_boolean_function(anf_round, 8, 9, [], l)
        core_operation_round_dict[tuple(l)] = L

    # SET THE INPUT DIVISION PROPERTY BELOW.
    # Because we know the input set, we set K equal to the empty set, i.e., there are no unknowns.
    # We trace the propagation of the monomial X_0 * ... * X_{63} through the construction.
    K = []
    L = [setMonomial(list(range(64)), 64)]

    for bit_number in range(STATE_SIZE):
        time_start = time.time()
        print("Bit " + str(bit_number) + ": " + str(bbdp(core_operation_injection_dict, core_operation_round_dict, K, L, bit_number)))
        time_end = time.time()
        print("Computation for this bit took " + time.strftime("%H:%M:%S", time.gmtime(time_end - time_start)) + " seconds.")

if __name__ == "__main__":
    print("Running main.")
    main()
