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
#==============================================================================================#
# s2fsched (c) 2020 Mario Guzzi                                                         #
#                                                                                              #
# class tripModel: Trip generator model class                                                  #
# Main solver controller class for single or multiple runs and results collection              #
#                                                                                              #
#                                                                                              #
#==============================================================================================#

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math

class tripModel:
    
    def __init__(self):
        # Profile Sections
        pass
    
    # Process as per the selected profile
    def process(self):
        pass
    
    def profileClear(self):
        pass
    
    #========================================================================================
    
    def annealer(self,A):
        self.A = A
        # Set up default values based on our best method thus far.
        # Do not change these values here, but instead update them within
        # benchmarking scripts
        QT = self.A.QT
        QT.params['const_bad'] = 4000000 #2000000        # Reduce bad station-station connections 
        QT.params['const_neg_gap'] = -100       # Reduce the number of reversals

        QT.params['const_pos_h'] = 120
        QT.params['const_ret_h'] = 120
        QT.params['const_pos_a'] = 240
        QT.params['const_ret_a'] = 240

        QT.params['const_must_start'] = -200000
        QT.params['const_cant_start'] = -2 * QT.params['const_must_start']

        QT.params['const_min_connect'] = 31     # Note: This minimum connect is only used for testing
                                                #       The true definition for connect time must include
                                                #       the additional knowledge of aircraft change which is
                                                #       not yet included. If two segments are operated by the
                                                #       same aircraft, then it is allowed to continue on within
                                                #       a 30 minute time frame (for example). If there is a 
                                                #       change of aircraft, usually a minimum connect time applies
                                                #       as is tested with the current min_connect capability
        QT.params['const_max_connect'] = 36*60  # Allow up to a certain amount of time for connections. If allowing multiple days
                                                # ensure crew rest will be sufficient.
        QT.params['const_max_fly_2X2'] = 14*60 # Default: Maximum flight time for combined 2 segments when no crew rest
        QT.params['const_min_prone_rest'] = 8*60 # Default: Amount of time in between segments that may qualify for a rest period
        QT.params['const_start'] = 90
        QT.params['const_stoptrip'] = 0

        # Rebuild the graph using current params
        QT.commitParams()
        
        return(self)
    
    def drawGraph(self):
        QT = self.A.QT
        viewG = QT.buildFltGraph(fltonly=True,view=True)
        #pos = nx.kamada_kawai_layout(viewG, dim=3)
        pos = nx.spring_layout(viewG,scale=5)
        plt.figure(1,figsize=(20*.75,10*.75)) 
        nx.draw_networkx(viewG,pos=pos,alpha=1)
        
    def printParams(self):
        QT = self.A.QT
        largest = max(len(k) for k in QT.params) + 1
        for k in QT.params:
            print(('{:' + str(largest)+ '}').format(k),QT.params[k])

    def inspectTables(self):
        QT = self.A.QT
        # Inspect Tables
        np.set_printoptions(suppress=True)
        #print("Gaps\n",QT.buildGaps())
        print("Gaps from G\n",QT.buildGapsFromG())
        #print("Connect\n", QT.buildConnect())
        print("ConnectFromG\n", QT.buildConnectFromG())
        print("MisConnectFromG\n", QT.buildMisconnectFromG())
        #print("ValidGaps\n", QT.buildValidGaps())
        print("ValidGapsFromG\n", QT.buildValidGapsFromG())
        print("HomeBase\n", QT.buildHomeBase())
        print("Station Weights\n", QT.buildStationWeights())
        print("EndPoint Weights\n", QT.buildEndPointWeights())

    # ===============================================================================================
    # Work in progress code - Will need to migrate to appropriate classes once proven
    #        estimateMaxObjective
    #        numQuboPairs
    #        rank
    # ===============================================================================================
    # Tuning Lagrange 
    #
    # We need to ensure that our Objective energy cannot overtake
    # Constraint energy levels
    # So we want to estimate the maximum value that our objective function can take
    # and create a base lagrange that is at least that value (plus a safety buffer)
    #
    # We have a few levels of constraints
    #
    # H1 - Structure constraints 
    # H2 - Polynomial to Quandratic constraints
    # H3 - Mis connection constraints
    # H4 - Objective which must not overlap the above two at any given time

    def estimateMaxObjective(self,QT):
        Vij_gaps = 0
        Vij_invalidgaps = 0
        Vij_objective = 0
        
        if '-gaps-' in QT.board.Qubos: Vij_gaps = QT.sumQij(QT.board.Qubos['-gaps-'])
        if 'objective' in QT.board.Qubos: Vij_objective = QT.sumQij(QT.board.Qubos['objective'])
        if 'invalid-gaps' in QT.board.Qubos: Vij_invalidgaps = QT.sumQij(QT.board.Qubos['invalid-gaps'])
        
        Vij = Vij_gaps + Vij_invalidgaps + Vij_objective
        
        #Vij = QT.sumQij(QT.board.Qubos['-gaps-']) + QT.sumQij(QT.board.Qubos['objective'])
        #Vii = QT.sumQii(QT.board.Qubos['-gaps-']) + QT.sumQii(QT.board.Qubos['objective'])
        V = Vij
        # Average pairwise value
        SV = math.sqrt(V)
        # Number of sequential pairs 
        NP = QT.board.cols - 1
        return(int(SV)*NP)

    # Compute Weight Boundaries to prevent cross over between objectives and constraints
    # (i.e setting our Lagrange parameters for a given data set)
    # Need Python 3.8
    def numQuboPairs(self,N):
        # Given the number of nodes, we want to compute
        # the number of Qubo pairs (Qij) we will have
        return( math.comb(int((N**2)/2),2) )

    def rank(self,v):
        return( math.ceil(math.log10(v)))

    # ===============================================================================================
    # Constraint weight preparation
    # ===============================================================================================

    class hamilWeights:
        H0 = 10000000   # Ancil weight. Use as a bias for high order to quadratic conversions
        HA = 10000000   # Structure constraints (rwo,cols)
        HC = 1.0        # Off base starts
        HB = 1.0        # Bias on misconnects   
        HD = 1.0        # bad gap weights
        LG = 1          # Not currently used
        HX = 1          # Calculated "undesirable instances" weight
        HXL = 1         # Calculated "undesirable instances" weight rank

        # digit tiers
        T1 = 0
        T2 = 0
        T3 = 0
        T4 = 0

    def calcBaseWeights(self):
        QT = self.A.QT
        
        N = QT.board.cols
        dayWeight = 1440

        original_bad_trip = QT.params['const_bad']
        
        # Clear Qubos

        QT.board.clearQubos()
        QT.params['const_bad'] = 0     # remove bad trip weight to isolate gaps only
        QT.commitParams()              # Rebuild the graph, dependant on the parameters

        # Objective contributions
        QT.applySegmentInitialContribution()                          # (6) 
        QT.applyValidGaps()                                           # (7)

        # Estimate Lagrange separator 
        # This value is used to set the bad_trip weight which will vary depending on
        # the number of nodes. Other lagranges will be determined by this ground value

        HX = self.estimateMaxObjective(QT)
        HX = max(HX, N * dayWeight )
        HXL = self.rank(HX)

        # Clear our estimation work
        QT.board.clearQubos()
        QT.params['const_bad'] = original_bad_trip  # Restore altered parameters  
        
        QT.commitParams()                  # Rebuild the graph, dependant on the parameters

        # Return the estimated weight for undesirable objective occurences
        return(HX,HXL)
    
    # Create the Hamiltonian Weights
    def makeHamilWeights(self,sigdigits=10):

        W = self.hamilWeights
        
        (W.HX,W.HXL) = self.calcBaseWeights()     
        
        # Max Sig Digits
        S = sigdigits
        W.HA = 10**S # structure
        W.H0 = W.HA    # Ancills    

        W.T1 = S
        W.T2 = int(S*0.025) #0.025 #int(S*0.80) # Second tier
        W.T3 = int(S*0.60)  # Third tier
        W.T4 = 1            # forth tier based on the objective spread

        W.HB = 10**W.T2 #4.5 #10**T2    # mis connects
        W.HC = 4.0 #10**T3    # bad starts
        W.HD = 1.0 # HX*75     # 10**T4 # bad gaps used in ValidGaps

        '''
        print("HX  :", W.HX)
        print("H0  :", W.H0)
        print("HA  :", W.HA)
        print("HB  :", W.HB)
        print("HC  :", W.HC)
        print("HD  :", W.HD)
        for i,T in enumerate([W.T1,W.T2,W.T3,W.T4]):
            print("T"+str(i+1)+"  :",T)

        '''
        
        return(W)
    
    def setConstraints(self):

        H = self.makeHamilWeights(7)
        
        QT = self.A.QT
        
        # Build final Qubos

        # Set structure constraints

        QT.applyOneNodePerRow(H.HA)                      # (1)
        QT.applyOneNodePerCol(H.HA)                      # (2)
        QT.applyMustStart(LG=100)                        # (3) TODO: Fix default weight and auto sizing
        #QT.applyCantStart()                             # (4)
        QT.applyNoMisconnect(qubo='misconnect',LG=H.HB)  # (5)
        QT.applyNoStartOffBase(qubo='badstarts',LG=H.HC) # (5b)

        # Objective contributions
        QT.applySegmentInitialContribution()             # (6) 
        QT.applyValidGaps(LG=H.HD)                       # (7)
        QT.applyStart(qubo='audit-CICO',P=H.H0)          # (8) Must come anywhere *after* ValidGaps

        #QT.applyStartInitialContribution(qubo='initial-starts')      # (6b) experimental. Trying to incentivise adding starts to remove negative gaps

    def inspectQubos(self):
        QT = self.A.QT
        # Inspect individual qubos
        for qubo in QT.board.Qubos.keys():
            ii = QT.sumQii(QT.board.Qubos[qubo])
            ij = QT.sumQij(QT.board.Qubos[qubo])
            print("Qubo: ", qubo, "Qii=", ii, "Qij=",ij)
            #print(QT.board.Qubos[qubo])
