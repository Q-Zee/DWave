#!/usr/bin/env python
# coding: utf-8

#    # DWave 8 Queens Problem - CDL Quantum 2020
#    
#    An attempt at solving the 8 Queens problemusing 4 quadratic constraints.
#    
#    Code also makes an attempt at a more general N queens on a square board of size S
#    

# In[1]:


import networkx as nx
from collections import defaultdict
from dimod import BinaryQuadraticModel
from tabu import TabuSampler        
from dwave.system import DWaveSampler, EmbeddingComposite
import neal
import numpy as np


# In[2]:


#
# Problem: Generate valid chess board configuartions using exactly 8 queens where none of the queens
#          take the other using standard queen movement rules. 
#
# 
#            

# Using a 8x8 board, we define two states: queen on a square or not on a square

# Rules
# 1 - There must be exactly 8 queens on the board 
# 2 - The number of queens on any row must be < 2
# 3 - The number of queens on any column must be < 2
# 4 - The number of queens in any diagonal must be < 2

# 

class board:

    def __init__(self,board_size=8,n_queens=8, LG=1, useQPU=False, useNeal=False, n_reads=100, chain=1):
        self.S = board_size
        self.N = board_size**2
        self.n_queens = n_queens
        self.Q = defaultdict(int)
        self.LG = LG
        self.useQPU = useQPU
        self.useNeal = useNeal
        self.n_reads = n_reads
        self.chain = chain
        self.offset = 0
    
    def qubit_id(self,r,c):
        return( r * self.S + c)

    # Must have n queens on the board
    def apply_const1(self, LG=1):
        linr = -((2*self.n_queens)+1)
        quad = 2
        offs = self.n_queens**2
        self.offset += offs
        
        for r in range(self.S):
            for c in range(self.S):
                indx = self.qubit_id(r,c)
                #print(r,c,indx)
                self.Q[(indx,indx)] += self.LG * linr
                for jndx in range(indx+1,self.N):
                    self.Q[(indx,jndx)] += self.LG * quad
        #print(self.Q)
    
    # Do not allow 2 or more on one row
    
    def apply_const2(self, LG=1):
        linr = -4  # We want less than 2 per row (0 or 1 is acceptable)
        quad = 4
        offs = 0
        self.offset += offs
        
        for r in range(self.S):
            for c in range(self.S):
                indx = self.qubit_id(r,c)
                self.Q[(indx,indx)] += self.LG * linr
                for c2 in range(self.S):
                    jndx = self.qubit_id(r,c2)
                    self.Q[(indx,jndx)] += self.LG * quad
    
    # Do not allow 2 or more on one column
    
    def apply_const3(self, LG=1):
        linr = -4  # We want less than 2 per row (0 or 1 is acceptable)
        quad = 4
        offs = 0
        self.offset += offs
        
        for r in range(self.S):
            for c in range(self.S):
                indx = self.qubit_id(r,c)
                self.Q[(indx,indx)] += self.LG * linr
                for r2 in range(self.S):
                    if ( r != r2 ):
                        jndx = self.qubit_id(r2,c)
                        self.Q[(indx,jndx)] += self.LG * quad

    # Do not allow 2 or more on one diagonal
    # We do this by scanning each position and looking for a second
    # position that is on a diagonal (|x1-x2| == |y1-y2|)
    
    def apply_const4(self, LG=1):
        linr = -4  # We want less than 2 per diag (0 or 1 is acceptable)
        quad = 4
        offs = 0
        self.offset += offs
        
        for r1 in range(self.S):
            for c1 in range(self.S):
                indx = self.qubit_id(r1,c1)
                #self.Q[(indx,indx)] += self.LG * linr
                for r2 in range(self.S):
                    for c2 in range(self.S):
                        if ( not ( (c1==c2)and(r1==r2))):
                            jndx = self.qubit_id(r2,c2)
                            #self.Q[(jndx,jndx)] += self.LG * linr
                            if ( abs(r1-r2) == abs(c1-c2)):
                                if ( indx != jndx ):
                                    self.Q[(indx,jndx)] += self.LG * quad
                                
    def getQ(self):
        return(self.Q)
    
    def printQ(self):
        for r in range(self.N):
            for c in range(self.N):
                if ( c>=r ):
                    if ( [n] == 1):
                        print('. Q ', end='')
                    else:
                        print('....', end='')
                else:
                    print('    ')
                print("|")
    def getSamples(self):
        return(self.sampleset)
    
    def solve(self):


        if ( self.useQPU ):
            sampler = EmbeddingComposite(DWaveSampler(solver={'qpu': True}))
            sampleset = sampler.sample_qubo(self.Q, num_reads=self.n_reads,chain_strength = self.chain)
        elif ( self.useNeal ): 
            bqm = BinaryQuadraticModel.from_qubo(self.Q, offset=self.offset)
            sampler = neal.SimulatedAnnealingSampler()
            sampleset = sampler.sample(bqm, num_reads = self.n_reads, chain_strength = self.chain)
        else:
            bqm = BinaryQuadraticModel.from_qubo(self.Q, offset=self.offset)
            sampler = TabuSampler()
            sampleset = sampler.sample(bqm, num_reads = self.n_reads, chain_strength = self.chain)

        self.sampleset = sampleset;

    def printBoard(self,result):
        
        variables = result[0]
        energy = result[1]
        print("\nEnergy %f" % (energy))
        for r in range(self.S):
            for c in range(self.S):
                n = self.qubit_id(r,c)
                if ( variables[n] == 1):
                    print('| Q ', end='')
                else:
                    if ( r==c):
                        print('|.o.', end='')
                    else:
                        print('|...', end='')
            print("|")

    def printAll(self, max=10):
        for res in self.sampleset.data():
            #print(res[0])
            self.printBoard(res)
            max = max - 1
            if ( max == 0 ): break


# # Prepare the problem size: S squares wide, N queens

# In[3]:


cb = board(board_size=8,n_queens=8, useQPU=False, useNeal = False, n_reads = 250, chain=7)


# # Apply the constraints
# 
# 

# In[4]:


cb.apply_const1(LG=1)  # We want n queens

cb.apply_const2(LG=1)  # We want no more than 1 per row

cb.apply_const3(LG=1)  # We want no more than 1 per col

cb.apply_const4(LG=1)  # We want no more than 1 per diag

#print(max(cb.getQ().values()))
#print(cb.getQ())


# # Solve and print results

# In[5]:


cb.solve()
cb.printAll(max = 3)
print(cb.getSamples())


# In[ ]:





# In[ ]:




