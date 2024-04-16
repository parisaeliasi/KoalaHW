import math
import gurobipy as gp
from gurobipy import GRB
from collections import Counter

ROUNDS         = 14
STATE_SIZE     = 32
WORD_SIZE      = STATE_SIZE // 2
PARTIAL_ROUNDS = WORD_SIZE + 1

# Returns true if the sum of the m'th output bit is unknown and False otherwise.
def exists_division_trail(round_number, partial_round_number, k, bit_number):
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    model = gp.Model('simon', env=env)

    l = model.addVars(ROUNDS + 1, WORD_SIZE, vtype=GRB.BINARY, name='l')
    r = model.addVars(ROUNDS + 1, WORD_SIZE, vtype=GRB.BINARY, name='r')
    c = model.addVars(ROUNDS, 3, WORD_SIZE, vtype=GRB.BINARY, name='c')
    a = model.addVars(ROUNDS, WORD_SIZE, vtype=GRB.BINARY, name='a')
      
    for i in range(round_number, ROUNDS):
        # Branches
        model.addConstrs(r[i + 1, j] + c[i, 0, j] + c[i, 1, j] + c[i, 2, j] == l[i, j] for j in range(WORD_SIZE))

        # AND gate
        model.addConstrs(c[i, 0, (j + 1) % WORD_SIZE] + c[i, 1, (j + 8) % WORD_SIZE] >= a[i, j] for j in range(WORD_SIZE))
        model.addConstrs(c[i, 0, (j + 1) % WORD_SIZE] + c[i, 1, (j + 8) % WORD_SIZE] <= 2*a[i, j] for j in range(WORD_SIZE))

        # XOR
        model.addConstrs(r[i, j] + a[i, j] + c[i, 2, (j + 2) % WORD_SIZE] == l[i + 1, j] for j in range(WORD_SIZE)) 

    # Force the first partial_round_number partial rounds to be equal to the identity function. 
    model.addConstrs(l[round_number + 1, i] == r[round_number, i] for i in range(partial_round_number))
        
    # Set input vector.
    model.addConstrs(l[round_number, i] == k[i] for i in range(WORD_SIZE))
    model.addConstrs(r[round_number, i] == k[WORD_SIZE + i] for i in range(WORD_SIZE))

    # Set output vector.
    model.addConstrs(l[ROUNDS, i] == 1 if i == bit_number else l[ROUNDS, i] == 0 for i in range(WORD_SIZE))
    model.addConstrs(r[ROUNDS, i] == 1 if WORD_SIZE + i == bit_number else r[ROUNDS, i] == 0 for i in range(WORD_SIZE))

    model.optimize()
    if model.status == GRB.OPTIMAL:
        return True
    
    return False

def bit_product(x, u):
    # Calculate x^u.
    if (x & u) == u:
        return 1
    return 0

def compute_anf(a, n):
    # Input is the value vector `a' of a Boolean function f.
    # Apply Moebius transform to value vector.
    for i in range(n):
        sz = (2 ** i)
        pos = 0
        while pos < (2 ** n):
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

def division_trails_over_sbox(anf, n, K, l):
    K_new = []
    L_new = []
    for u in range(2 ** n):
        for v in range(2 ** n):
            # anf[u] is the ANF of S-box^u.
            if anf[u][v] == 1:
                u_list = convert_int_to_list(u, n)
                v_list = convert_int_to_list(v, n)
                # If S-box^u[v] == 1 for some v in V, then K_new.append(u)
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

def swap(K):
    R = []
    for k in K:
        R.append(k[WORD_SIZE:] + k[0:WORD_SIZE])

    return R

def bbdp_propagate_accurate(anf, n, partial_round_number, L):
    # Despite K being the empty set, the output K can still contain vectors, because they are created by L as
    # the result of addition with the secret key.
    # This happens for i == WORD_SIZE (or STATE_SIZE?).

    K = []
    if partial_round_number == PARTIAL_ROUNDS - 1:
        for i in range(WORD_SIZE, STATE_SIZE):
            for l in L:
                if l[i] == 0:
                    K.append(l[0:i] + [1] + l[i+1:])      
        L = reduce1(K, L)

        K = swap(K)
        L = swap(L)
    else:
        L_counter = Counter()
        for l in L:
            l_sbox_input = [l[(partial_round_number + 1) % WORD_SIZE], 
                            l[(partial_round_number + 8) % WORD_SIZE], 
                            l[(partial_round_number + 2) % WORD_SIZE], 
                            l[WORD_SIZE + partial_round_number]]
            _, L_sbox_output = division_trails_over_sbox(anf, n, [], l_sbox_input)
            for l_sbox_output in L_sbox_output:
                l_updated = l.copy()
                l_updated[(partial_round_number + 1) % WORD_SIZE] = l_sbox_output[0] 
                l_updated[(partial_round_number + 8) % WORD_SIZE] = l_sbox_output[1]
                l_updated[(partial_round_number + 2) % WORD_SIZE] = l_sbox_output[2]
                l_updated[WORD_SIZE + partial_round_number]       = l_sbox_output[3]
                L_counter[tuple(l_updated)] = (L_counter[tuple(l_updated)] + 1) % 2
        L = [list(l) for l in L_counter if L_counter[l] == 1]

    return (K, L) 

def bbdp(anf, n, K, L, bit_number): 
    for round_number in range(ROUNDS):
        for partial_round_number in range(PARTIAL_ROUNDS):
            for k in K:
                if exists_division_trail(round_number, partial_round_number, k, bit_number):
                    # Stopping rule 1.
                    return -1;               
                # else:
                #   remove k from K
            # If this line is reached, K has become the empty set.
            L_after_pruning = []
            for l in L:
                if exists_division_trail(round_number, partial_round_number, l, bit_number): 
                   L_after_pruning.append(l)

            if len(L_after_pruning) == 0:
                # Stopping rule 2.
                return 0
    
            # We do not need the round number here, as the rounds are all the same.
            K, L = bbdp_propagate_accurate(anf, n, partial_round_number, L_after_pruning)
    return 1

def test_bit_product():
    assert bit_product(0x0, 0x0) == 1, "test_bit_product failed."
    assert bit_product(0x5, 0x9) == 0, "test_bit_product failed."

def test_compute_anf():
    a = [0, 1, 0, 0, 0, 1, 1, 1]
    b = compute_anf(a, 3)
    assert b == [0, 1, 0, 1, 0, 0, 1, 0], "test_compute_anf failed."

def test_is_at_most():
    u = [0, 1, 0] 
    v = [1, 0, 1]
    assert not is_at_most(u, v), "test_is_at_most failed."    
    v = [1, 1, 1]
    assert is_at_most(u, v), "test_is_at_most failed."    

def test_is_lower_bounded():
    v = [1, 0, 0]
    K = [[1, 0, 0], [0, 0, 1]]
    assert is_lower_bounded(v, K), "test_is_lower_bounded failed."

def test_reduce0():
    assert reduce0([[0, 1], [1, 1]]) == [[0, 1]], "test_reduce0 failed."
    assert reduce0([[1, 1], [1, 1]]) == [[1, 1]], "test_reduce0 failed."

def test_reduce1():
    assert reduce1([], [[1, 1, 0, 0]]) == [[1, 1, 0, 0]], "test_reduce1 failed."
    assert reduce1([[0, 1]], [[1, 0]]) == [[1, 0]], "test_reduce1 failed."
    assert reduce1([[0, 1]], [[1, 1]]) == [], "test_reduce1 failed."

def test_division_trails_over_sbox():
    sbox = [0x0, 0x1, 0x3, 0x2, 0x4, 0x5, 0x7, 0x6, 0x8, 0x9, 0xb, 0xa, 0xd, 0xc, 0xe, 0xf]
    anf = [[]] * 16
    for u in range(16):
        value_vector = list(map(bit_product, sbox, [u] * 16))
        anf[u] = compute_anf(value_vector, 4)

    K = []
    l = [1, 1, 0, 0]
    K_new, L_new = division_trails_over_sbox(anf, 4, K, l)
    assert K_new == [], "test_division_trails_over_sbox failed."
    assert set(map(tuple, L_new)) == set(map(tuple, [[1, 1, 0, 0], [0, 0, 0, 1], [1, 0, 0, 1], [0, 1, 0, 1], [1, 1, 0, 1]])), "test_division_trails_over_sbox failed."
    K = [[1, 0, 0, 0]]
    l = [1, 1, 0, 0]
    K_new, L_new = division_trails_over_sbox(anf, 4, K, l)
    assert set(map(tuple, K_new)) == set(map(tuple, [[1, 0, 0, 0], [0, 0, 0, 1]])), "test_division_trails_over_sbox failed."
    assert set(map(tuple, L_new)) == set(map(tuple, [])), "test_division_trails_over_sbox failed."

def test_swap():
    assert swap([[1] * WORD_SIZE + [0] * WORD_SIZE]) == [[0] * WORD_SIZE + [1] * WORD_SIZE], "test_swap failed."

def test_bbdp_propagate_accurate():
    sbox = [0x0, 0x1, 0x3, 0x2, 0x4, 0x5, 0x7, 0x6, 0x8, 0x9, 0xb, 0xa, 0xd, 0xc, 0xe, 0xf]
    anf = [[]] * 16
    for u in range(16):
        value_vector = list(map(bit_product, sbox, [u] * 16))
        anf[u] = compute_anf(value_vector, 4)

    l = [0] * STATE_SIZE 
    i = 0
    l[(i + 1) % WORD_SIZE] = 1
    l[(i + 8) % WORD_SIZE] = 1
    l[(i + 2) % WORD_SIZE] = 0
    l[WORD_SIZE + i] = 0
    K, L = bbdp_propagate_accurate(anf, 4, i, [l])
    assert K == [], "test_bbdp_propagate_accurate failed."
    l1 = [0] * STATE_SIZE
    l1[(i + 1) % WORD_SIZE] = 1
    l1[(i + 8) % WORD_SIZE] = 1
    l1[(i + 2) % WORD_SIZE] = 0
    l1[WORD_SIZE + i] = 0
    l2 = [0] * STATE_SIZE
    l2[(i + 1) % WORD_SIZE] = 0
    l2[(i + 8) % WORD_SIZE] = 0
    l2[(i + 2) % WORD_SIZE] = 0
    l2[WORD_SIZE + i] = 1
    l3 = [0] * STATE_SIZE
    l3[(i + 1) % WORD_SIZE] = 1
    l3[(i + 8) % WORD_SIZE] = 0
    l3[(i + 2) % WORD_SIZE] = 0
    l3[WORD_SIZE + i] = 1
    l4 = [0] * STATE_SIZE
    l4[(i + 1) % WORD_SIZE] = 0
    l4[(i + 8) % WORD_SIZE] = 1
    l4[(i + 2) % WORD_SIZE] = 0
    l4[WORD_SIZE + i] = 1
    l5 = [0] * STATE_SIZE
    l5[(i + 1) % WORD_SIZE] = 1
    l5[(i + 8) % WORD_SIZE] = 1
    l5[(i + 2) % WORD_SIZE] = 0
    l5[WORD_SIZE + i] = 1
    assert Counter(map(tuple, L)) == Counter(map(tuple, [l1, l2, l3, l4, l5])), "test_division_trails_over_sbox failed."

    l1 = [1] * STATE_SIZE
    l1[(i + 1) % WORD_SIZE] = 0
    l1[(i + 8) % WORD_SIZE] = 1
    l1[(i + 2) % WORD_SIZE] = 1
    l1[WORD_SIZE + i] = 0

    l2 = [1] * STATE_SIZE
    l2[(i + 1) % WORD_SIZE] = 0
    l2[(i + 8) % WORD_SIZE] = 1
    l2[(i + 2) % WORD_SIZE] = 0
    l2[WORD_SIZE + i] = 1

    K, L = bbdp_propagate_accurate(anf, 4, i, [l1, l2])

    l3 = l1.copy()
    l4 = l3.copy()
    l4[WORD_SIZE] = 1

    assert K == [], "test_bbdp_propagate_accurate failed."
    assert Counter(map(tuple, L)) == Counter(map(tuple, [l3, l4])), "test_bbdp_propagate_accurate failed."

    i = PARTIAL_ROUNDS - 1
    K, L = bbdp_propagate_accurate(anf, 4, i, [l3, l4])
    k = [1] * STATE_SIZE
    k[WORD_SIZE + 1] = 0

    assert K == [k], "test_bbdp_propagate_accurate failed."
    assert L == swap([l3]), "test_bbdp_propagate_accurate failed."

def test_exists_division_trail():
    # Assumes Simon32 and 14 rounds
    k = [0] + [1] * 31
    # There exists a trail from k to e_m for any m.
    for bit_number in range(32):
        assert exists_division_trail(0, 0, k, bit_number), "test_exists_division_trail failed."

def main():
    n = 4
    sbox = [0x0, 0x1, 0x3, 0x2, 0x4, 0x5, 0x7, 0x6, 0x8, 0x9, 0xb, 0xa, 0xd, 0xc, 0xe, 0xf]
    anf = [[]] * 16
    for u in range(2 ** n):
        value_vector = list(map(bit_product, sbox, [u] * (2 ** n)))
        anf[u] = compute_anf(value_vector, n)

    K = [[1] * STATE_SIZE]
    L = [[0] + ([1] * (STATE_SIZE - 1))]
    for bit_number in range(STATE_SIZE):
        print("Bit " + str(bit_number) + ":" + str(bbdp(anf, n, K, L, bit_number)))

if __name__ == "__main__":
    print("Running tests.")

    test_bit_product()
    test_compute_anf()
    test_is_at_most()
    test_is_lower_bounded()
    test_reduce0()
    test_reduce1()
    test_division_trails_over_sbox()
    test_swap()
    test_bbdp_propagate_accurate()
    test_exists_division_trail()

    print("All tests passed.")
    
    print("Running main.")

    main()
