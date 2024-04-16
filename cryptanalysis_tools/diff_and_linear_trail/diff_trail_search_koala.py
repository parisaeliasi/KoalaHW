#!/usr/bin/env sage
# coding=utf-8

import sys
import random
import os
import time
from operator import xor
import gurobipy as gp
from gurobipy import GRB

KOALA_SIZE = 257
NBR_ROUND = 6

#create the Gurobi model
P = gp.Model("creat_equation")

#create all the necessary variable for model the cipher

#input of each round
x = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="x")

#output of each round (before the permutation of each half of the state)
y = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="y")

#activity partern : A[i] = 1 iif (0,0,1) = (x[i],x[i+1],x[i+2])
A = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="A")

#intermediate variable to compute both Xor
x1 = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="x1")
#x2 = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="x2")
x3 = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="x3")

xp = P.addVars(NBR_ROUND,KOALA_SIZE, vtype=GRB.BINARY, name="xp")



#return the value of a+plus mod half of the size of the state
def shiffte(a,plus):
    return (a+plus)%(KOALA_SIZE)
    
#add the non linear constraint for each bit of the round r
def NL_part(r):
    for i in range(KOALA_SIZE):
        create_NL(i,r)

#add the non linear constraint for bit a and b at round r
def create_NL(a,r):

    #modify the propagation rule to add the 2-bit xor at the end of the AND gate
    #constraint for the and
    P.addConstr(x3[r,(a+1)%KOALA_SIZE]+x3[r,(a+2)%KOALA_SIZE]-xp[r,a]>=0)

    #constraint for the non independency of 2 output bit depending on 3 input for the chi rotation value
    P.addConstr(-x3[r,a]+x3[r,(a+1)%KOALA_SIZE]-x3[r,(a+2)%KOALA_SIZE]-xp[r,a]+xp[r,(a+1)%KOALA_SIZE]>=-2)
    P.addConstr(-x3[r,a]+x3[r,(a+1)%KOALA_SIZE]-x3[r,(a+2)%KOALA_SIZE]+xp[r,a]-xp[r,(a+1)%KOALA_SIZE]>=-2)

    #add the 2-bit xor
    P.addConstr(-xp[r,a]+x3[r,a]+y[r,a]>=0)
    P.addConstr(xp[r,a]-x3[r,a]+y[r,a]>=0)
    P.addConstr(xp[r,a]+x3[r,a]-y[r,a]>=0)
    P.addConstr(-xp[r,a]-x3[r,a]-y[r,a]>=-2)

    P.addConstr(x[r+1,a]==y[r,a])
    
    #constraint for the non independency of 2 output bit depending on 3 input for any rotation value
    #P.addConstr(x3[r,a]+x3[r,b]-x3[r,b+(b-a) %H_SONIC_SIZE]-y[r,a]+y[r,b]>=-1)
    #P.addConstr(x3[r,a]+x3[r,b]-x3[r,b+(b-a) %H_SONIC_SIZE]-y[r,a]-y[r,b]>=-2)
    #P.addConstr(-x3[r,a]+x3[r,b]+x3[r,b+(b-a) %H_SONIC_SIZE]+y[r,a]-y[r,b]>=-1)
    #P.addConstr(-x3[r,a]+x3[r,b]+x3[r,b+(b-a) %H_SONIC_SIZE]-y[r,a]-y[r,b]>=-2)
    #P.addConstr(-x3[r,a]+x3[r,b]-x3[r,b+(b-a) %H_SONIC_SIZE]-y[r,a]+y[r,b]>=-2)
    #P.addConstr(-x3[r,a]+x3[r,b]-x3[r,b+(b-a) %H_SONIC_SIZE]+y[r,a]-y[r,b]>=-2)
    
    #P.addConstr(x[r,a]<=1)
    #P.addConstr(x[r,b]<=1)
    
#add the xor constraint for every bit at round r (left xor)        
def xor_theta(r):
    for i in range(KOALA_SIZE):
        xor_3_bit_left_new(i,r,0,3,10)
        #fork_3_bit_left_new(i,r,0,3,8)
                

#add the linear constraint for a 3 bit xor at round r beetween the output of then non-linear function at index a, the input of the round at index a+SLR and the input of the round at index a+half of the state 
def xor_3_bit_left_new(a,r,SLL1,SLL2,SLL3):
    P.addConstr(x1[r,shiffte(a,SLL1)]+x1[r,shiffte(a,SLL2)]+x1[r,shiffte(a,SLL3)]-x3[r,a]>=0)
    P.addConstr(-x1[r,shiffte(a,SLL1)]-x1[r,shiffte(a,SLL2)]-x1[r,shiffte(a,SLL3)]+x3[r,a]>=-2)
    P.addConstr(-x1[r,shiffte(a,SLL1)]+x1[r,shiffte(a,SLL2)]+x1[r,shiffte(a,SLL3)]+x3[r,a]>=0)
    P.addConstr(x1[r,shiffte(a,SLL1)]-x1[r,shiffte(a,SLL2)]+x1[r,shiffte(a,SLL3)]+x3[r,a]>=0)
    P.addConstr(x1[r,shiffte(a,SLL1)]+x1[r,shiffte(a,SLL2)]-x1[r,shiffte(a,SLL3)]+x3[r,a]>=0)
    P.addConstr(x1[r,shiffte(a,SLL1)]-x1[r,shiffte(a,SLL2)]-x1[r,shiffte(a,SLL3)]-x3[r,a]>=-2)
    P.addConstr(-x1[r,shiffte(a,SLL1)]-x1[r,shiffte(a,SLL2)]+x1[r,shiffte(a,SLL3)]-x3[r,a]>=-2)
    P.addConstr(-x1[r,shiffte(a,SLL1)]+x1[r,shiffte(a,SLL2)]-x1[r,shiffte(a,SLL3)]-x3[r,a]>=-2)

def shuffle(r):
    for i in range(KOALA_SIZE):
        P.addConstr(x[r,i]==x1[r,(i*121) % KOALA_SIZE])
        #P.addConstr(x1[r,i]==x[r,(i*150) % KOALA_SIZE])
        

#add the constraint for the activity paterne for each bit in the left part of the inpput of round r
#we set the constraint to active an activity patern if there is a patterne 010 or 01110 since for linear weight
#the weight is the size of any sequence in between two 0 if it is even, and the size +1 if the size is odd
#therefore for even lenght the hamming weight will do the job, and for od length we consider the smallest sequence
#which are 010 and 01110, and for those we set to 1 the activity pattern
def set_odd(r):
    
    for i in range(KOALA_SIZE):        
        P.addConstr(x3[r,(i % KOALA_SIZE)]+x3[r,((i+1)%KOALA_SIZE)]-x3[r,((i+2)%KOALA_SIZE)]+A[r,i]>=0)
        P.addConstr(A[r,i]<=1)

#set the objectiv function for the number of round
#the objectiv function is to minimize the sum of the weight of left half input + 1 for each 010 and 01110 paterne
#the linear weight computed is a lower bound of the linear weight.
def set_obj(NBR_round):
    Q = 0
    for i in range(NBR_round):
        for j in range(KOALA_SIZE):
            Q += x3[i,j] + A[i,j]

    #P.addConstr(Q>=28)
    
    P.setObjective(Q,GRB.MINIMIZE)

#add the constraint for NBR_round of the round function with the rotation value specify as argument to the model P
def add_constraint(NBR_round):
    if(not (P.NumConstrs==0)):
        P.remove(P.getConstrs()[0:P.NumConstrs-1])
    
    R = x3[0,0]
    P.addConstr(R>=1)

    NL_part(0)
    set_odd(0)
    
    for i in range(1,NBR_round):
        shuffle(i)
        xor_theta(i)
        NL_part(i)
        set_odd(i)
    
    set_obj(NBR_round)
    

#!!this function can only be call after the optimization of the model!!
#
#This function print the trail with minimum weight find after minimization of the objectiv function
def print_trail(NBR_round):

    weight = P.ObjVal
    
    print("tot weight for "+str(NBR_round)+" = "+str(weight))

    list_a = []
    list_b = []
    
    #print a trail with min weight and iterate over all trail with min weight
    for i in range(NBR_round):
        print("A"+str(i)+":",end="          ")
        #print the state corresponding to the input of the non linear layer
        for j in range(KOALA_SIZE):
            if(x[i,j].getAttr('x')==1):
                print("1",end="")
                list_a.append([i,j])
            else:
                print("-",end="")
        
        print("\nC"+str(i)+" :",end="         ")
        for j in range(KOALA_SIZE):
            if(x1[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
        '''
        print("\nD"+str(i)+" :",end="         ")
        for j in range(KOALA_SIZE):
            if(x2[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
                
        print("\nA"+str(i)+"3:",end="         ")
        for j in range(KOALA_SIZE):
            if(x3[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
        print("\nS"+str(i)+"1:",end="         ")
        for j in range(KOALA_SIZE):
            if(x3[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
        print("\nS"+str(i)+"2:",end="         ")
        for j in range(KOALA_SIZE):
            if(x3[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
        '''
        print("\nB"+str(i)+" :",end="         ")
        for j in range(KOALA_SIZE):
            if(x3[i,j].getAttr('x')==1):
                print("1",end="")
                list_b.append([i,j])
            else:
                print("-",end="")
        '''
        print("\nS"+str(i)+"4:",end="         ")
        for j in range(KOALA_SIZE):
            if(s4[i,j].getAttr('x')==1):
                print("1",end="")
            else:
                print("-",end="")
       
        print("\nY"+str(i)+":",end="         ")
        for j in range(KOALA_SIZE):
            if(y[i,j].getAttr('x')==1):
                print("1",end="")
                
            else:
                print("-",end="")
        '''
        
        print()
        print()

    print("list index for active bit in x state")
    for i in list_a:
        print(i,end=", ")
    print("list index for active bit in y state")
    for i in list_b:
        print(i,end=", ")


#for a specific shifting rotation setup :
#SNL1 : shift non-linear 1
#SNL2 : shift non-linear 2
#SLR1 : shift linear right
#SLL1 : shift linear left 1
#SLL2 : shift linear left 2
# and for NBR_round, model and comput the minimum weight for any trail
def test_para(NBR_round):

    add_constraint(NBR_round);

    #set up the bound, wich mean that if the objectiv value goes below that value then the optimization stop
    #P.setParam(GRB.Param.BestObjStop,weight_min)
    
    #P.setParam(GRB.Param.Cutoff,20)

    #P.Params.timeLimit = 36000
    
    #write the model in a lp file
    #P.write("test_koala_dif_"+str(KOALA_SIZE)+"_"+str(NBR_round)+".lp")

    #return -1

    #set the flag to 1 in order to have live information about the optimization status
    #set the flag to 0 in order to have no information until the optimization finish
    P.setParam('OutputFlag',1)
    Sol = P.optimize()

    weight = P.ObjVal
    
    #testing the result according to the metric chosen
    print_trail(NBR_round)
    
    return weight

for Round in range(1,5):
    time_start = time.time()
    test_para(Round)
    time_end = time.time()
    print("Computation took " + time.strftime("%H:%M:%S", time.gmtime(time_end - time_start)) + " seconds.")
