#   Copyright 2021 Mario Guzzi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
'''
Created on Oct. 22, 2021

@author: Mario Guzzi
'''

import numpy as np
from collections import defaultdict

#==============================================================================================#
# class qbGrid: Qubit Grid for processing and optimizing sequences using a BQM method          #
#                                                                                              #
# Defines a grid of rows and columns of qbit variables and provides mapping to each var id     #
# Provides for stacking multiple qubos for independant constraint inspection                   #
# Application of linear and quadratic constraints to a named qubo                              #
#                                                                                              #
#==============================================================================================#

class qbGrid:
    
    def newQubo(self,name=None):
        disposable = (name is None)
        
        # Initialize
        Q=defaultdict(float)
        # Removed because unnessary and bloats memory on large problems 
        #for i in range(self.qubits):
        #    for j in range(self.qubits):
        #        Q[(i,j)] = 0.0
                
        # If disposable, return it now.

        if ( disposable ): return (Q)
    
        # Otherwise store it
        
        if ( name not in self.Qubos ):
            self.Qubos[name] = Q
            
        return(Q)
                    
    def getQubo(self,name):
        if ( name not in self.Qubos ):
            return (self.newQubo(name))
        return (self.Qubos[name])
    
    def info(self):
        print("Allocated",self.qubits,"qubo variables",self.set.min(),"to",self.set.max())
        print("         ",self.flags.size,"start flags",self.flags.min(),"to",self.flags.max() )
        add = np.array(self.additional)
        if ( add.size > 0 ):
            print("         ",add.size,"additional variables",add.min(),"to",add.max())
        #print("         ",self.ancil.size,"start ancillaries",self.ancil.min(),"to",self.ancil.max() )
            
    def clearQubos(self):
        if ( self.Qubos is not None):     
            self.Qubos.clear()
            
    def __init__(self,rows=1,cols=1):
        self.rows = rows
        self.cols = cols
        self.N = rows * cols
        
        # Board qubits
        self.set = np.array(list(range(self.N)))
        # Flag qubits
        self.flags = np.array(range(rows)) + self.N
        # Ancillary qubits for start flags
        #self.ancil = np.array(range(rows)) + self.N + self.flags.size
        # High Order variables 
        self.qubits = max(self.flags)+1 # Next variable id available
        self.additional = []            # new variables allocated through higher order conversions
        self.highOrders = {}            # Mapping of higher order products to an existing conversion
        

        #self.info()
        
        # Board and Transposed Board
        self.board = np.array(self.set).reshape(self.rows,self.cols)
        self.trans = self.board.T 

        #
        # Dictionary of Qubos
        # 
        
        self.Qubos = {}
        
        # Graph for weights 
        #self.G = nx.DiGraph()
        
        self.constant = 0.0
        # Normalization weight factor
        self.normal = 1.0
    
    def setNorm(self,n):
        self.normal = n
        
    def normalize(self,w):
        return( w * self.normal )
    
    def getOrg(self,r,c):
        return (r * self.cols + c)
    
    def getqb(self,r,c):
        return list([self.getOrg(r,c)])

    # Get row wise groups of qubits
    def getr(self,r,s=0):
        if ( s == 0 ): s = self.cols
        return self.board[r][:s]
    
    # Get column wise groups of qubits
    def getc(self,c,s=0):
        if ( s == 0 ): s = self.rows
        return self.trans[c][:s]
    
    # Get a list of all rows
    def getr_all(self, s=0):
        if ( s == 0 ): s = self.cols
        return np.array([r[:s] for r in self.board])
        
    def get(self,row,col,group,step,times):
        origin = self.getOrg(row,col)
        result = []
        for t in range(times):
            result.extend(self.set[origin:origin+group])
            origin += step
        return result
    
    def getcols(self,row,col,nrow=1,ncol=1):
        result = []
        for c in range(ncol):
            origin = self.getOrg(row,col+c)
            grp = []
            for r in range(nrow):
                item = self.set[origin:origin+1]
                origin += self.cols
                grp.extend(item)
            result.append(grp)
        return result

    def getallrows(self,row,col,nrow=1,ncol=1):
        result = []
        for r in range(nrow):
            origin = self.getOrg(row+r,col)
            result.extend(self.set[origin:origin+ncol])
        return result

    def getrows(self,row,col,nrow=1,ncol=1):
        result = []
        for r in range(nrow):
            origin = self.getOrg(row+r,col)
            result.append(self.set[origin:origin+ncol])
        return result
    
    # Flatten a list of list of qubit into a single list
    def flat(self,qubits):
        return [item for sublist in qubits for item in sublist]

        
    # nodeQubits: return the variable numbers applicable to a list of nodes (regardless of the cycle step)
    
    def nodeqb(self,nodes):
        qubits = []
        #for r in range(self.rows):
        for (r,n) in nodes:
            qubits.extend(self.getqb(r,n))
        return (qubits)
            
    # Apply constraint to given qubit set
    # use quadCoeff to build qlc
    # Ex: applyConst(quadCoeff().getEqual(4),self.get(r,c,count))
    # To apply a row constraint to all rows, call applyConst for each row
    
    def applyConst(self,qlc,qbits,lg=1.0,qubo="constraint"):
        Q = self.getQubo(qubo)
        (c_q,c_l,c_c) = qlc
        self.constant += c_c
        for q1 in qbits:
            # set Linear
            Q[(q1,q1)] += c_l * lg
            for q2 in qbits:
                if ( q2 > q1 ):
                    # Set quadratic
                    Q[(q1,q2)] += c_q * lg
                    
    def applyPen(self,pen,qubits,qubo="constraint"):
        Q = self.getQubo(qubo)
        for q1 in qubits:
            # set Linear
            Q[(q1,q1)] += pen

    def applyDistinctPairwisePen(self, penh, penJ ,qb1, qb2,qubo="constraint"):
        Q = self.getQubo(qubo)
        for q1 in qb1:
            # set Linear
            Q[(q1,q1)] += penh
            for q2 in qb2:
                if ( q2 > q1 ):
                    if ( q1 != q2 ):
                        Q[(q1,q2)] += penJ
