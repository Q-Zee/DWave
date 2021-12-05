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
import networkx as nx

from quzzi.qbgrid import qbGrid
from quzzi.qzquad import *

#from qztrips.qbGrid import qbGrid
#from qzquad import quadCoeff
#from qzquad import highOrderExpression

#from collections import defaultdict

#==============================================================================================#
# s2fsched (c) 2020 Mario Guzzi                                                         #
#                                                                                              #
# class QuboTrips: Trip generator constraints preparer for tripAnneal                          #
#                                                                                              #
#                                                                                              #
#                                                                                              #
#==============================================================================================#

class QuboTrips:
    # Todo: Turn these into a dictionary
    #self.params['const_bad'] = 100000
    #const_must_start = -20000
    #const_cant_start = -2 * const_must_start
    #const_CI = 60
    #const_CO = 30
    #const_pos_h = 120
    #const_ret_h = 120
    #const_pos_a = 240 
    #const_ret_a = 240 
    
    def __init__(self,tripAnneal,n_nodes,norm=1000):

        self.Ann = tripAnneal # Provide access to data set graph and contents
        self.norm = 1.0/norm
        self.board = qbGrid(n_nodes,n_nodes)

        self.params = {}
        self.params['const_start'] = 90      # Initial Cost of using a start
        self.params['const_bad'] = 100000
        self.params['const_must_start'] = -20000
        self.params['const_cant_start'] = -2 * self.params['const_must_start']
        self.params['const_CI'] = 60
        self.params['const_CO'] = 30
        self.params['const_pos_h'] = 120
        self.params['const_ret_h'] = 120
        self.params['const_pos_a'] = 240 
        self.params['const_ret_a'] = 240 
        self.params['const_neg_gap'] = -100
        
        self.params['const_min_connect'] = 0
        self.params['const_max_connect'] = 36*60 # Default: Assumes single day trips only. Disallows crew rest
        self.params['const_max_fly_2X2'] = 14*60 # Default: Maximum flight time for combined 2 segments when no crew rest
        self.params['const_min_prone_rest'] = 8*60 # Default: Amount of time in between segments that may qualify for a rest period
        
        self.G = self.buildFltGraph()

        self.finalQ = None
        
        

    # Build Graph - Must be called after parameters have been set
    
    def commitParams(self):
        self.G = self.buildFltGraph()
    
    # This is required to create a single final normalized qubo 
    def commitQubo(self):
        self.finalQ = self.problemQubo()
    
    # This is the call that the solver needs to make to get the problem Qubo
    def finalQubo(self):
        if ( self.finalQ is None ): self.commitQubo()
        return( self.finalQ )
    
    # Construct the final problem Qubo to solve
    # This is the Qubo to send to the annealer.
    
    def problemQubo(self):
        FinalQubo = self.board.newQubo()

        for qubo in self.board.Qubos.keys():
            Q = self.normalizeQubo(self.board.Qubos[qubo])
            FinalQubo = self.sumQubo( FinalQubo, Q )
        return (FinalQubo)
        
    # Constraints
    # Each of these constraints represent one Hamiltonian with a scaling Lagrange parameter LG
    
    def applyOneNodePerRow(self,LG=1,qubo='constraint'):
        for r in range(self.board.rows):
            self.board.applyConst(quadCoeff().getEqual(1),self.board.getr(r),LG,qubo)

    def applyOneNodePerCol(self,LG=1,qubo='constraint'):
        for c in range(self.board.cols):
            self.board.applyConst(quadCoeff().getEqual(1),self.board.getc(c),LG,qubo)

    def applyMustStart(self,LG=1,qubo='constraint'):
        self.board.applyConst((0,self.params['const_must_start'],0),[self.board.flags[0]],LG,qubo)
        
    def applyCantStart(self,LG=1,qubo='constraint'):
        self.board.applyConst((0,self.params['const_cant_start'],0),[self.board.flags[self.board.rows-1]],LG,qubo)
    
    def applyStartAncil(self,LG=1,qubo='cubic'):
        for r in range(self.board.rows):
            self.board.applyConst(quadCoeff().getBothOrNothing(),[self.board.flags[r],self.board.ancil[r]],LG,qubo)
        
    #
    # Utility to convert Qubo to an array
    #
    
    def getQuboArray(self,Q):
        # Obtain dimensions
        nr = 0
        nc = 0
        for e in Q:
            (i,j) = e
            nr = max(nr,i)
            nc = max(nc,j)
        nr += 1
        nc += 1
        
        # Build array
        arr = np.zeros((nr,nc))
        for (r,c) in Q:
            arr[r,c] = Q[(r,c)] / self.norm
        return(arr)

    
    #
    # Utility to print a Qubo
    #
    
    def printQubo(self,Q, nodes=None):
        # Print the Qubo
        QArr = self.getQuboArray(Q)
        (max_r, max_c) = QArr.shape
        # If no nodes specified use all nodes
        if (nodes is None): nodes = range(min(max_r,self.board.qubits-1))
        print("Print Qubo: nodes = ", nodes)
        for r in nodes:
            for c in nodes:
                if ( c >= r ):
                    val = int(QArr[r,c])
                    if ( val != 0 ): 
                        print( "{:+6d}".format(int(QArr[r,c])),end=' ')
                    else:
                        print("      ", end=' ')
                else:
                    #print( "{:+6d}".format(0), end=' ')
                    print("      ", end=' ')
            print("")
            
    #
    # Utility to add two Qubos together
    # 
    def sumQubo(self,Q1,Q2):
        Q = defaultdict(float)
        for e in Q2: Q[e] = 0.0    # Create keys from Q2
        for e in Q1: Q[e] = Q1[e]  # Copy from Q1
        for e in Q2: Q[e] += Q2[e] # Add Q2
        return ( Q )

    #
    # Normalization of a Qubo. 
    # Use this on an Objectives Qubo to prepare adding other normalized Qubos
    #
    def normalizeQubo(self,Q):
        normQ = {}
        for e in Q: normQ[e] = Q[e] * self.norm
        return(normQ)
    
    # Apply an initial Qii (negative value)
    # Use this to set the Linear Qii of one or more qubits to an initial ground state
    # Create to set the ground state of a single flight segment as a means to encourage adding it to 
    # a solution (because all segments must be used) and prepare for raising energy as segments are sequenced
    # together.
    #
    # ** This method enforces that the L weight will be negative. Therefore we enforce -abs(L)
    #    Only use to set an initial state
    #
    # Goes to the Objectives Qubo
    #
    
    def ApplySingleInitialContribution(self, qubits, L, qubo='objective' ): # Applies -L
        Q = self.board.getQubo(qubo)
        for q in qubits:
            Q[q,q] += -abs(L) # This is done on purpose to prevent playing with signs erroneously

    # Apply a pairwise contribution Qij (positive value)
    #
    def ApplyPairwiseContribution(self, qubits, Qij, qubo='objective' ): # Applies +Qij
        Q = self.board.getQubo(qubo)
        for (q1,q2) in qubits:
            if ( q1>q2 ): (q1,q2) = (q2,q1)
            Q[(q1,q2)] += abs(Qij) # abs() is done on purpose to prevent playing with signs erroneously
    
    # Cancel a previously applied contribution for a new condition
    
    def CancelPairwiseContribution(self, qubits, Qij, qubo='objective' ): # Applies -Qij
        Q = self.board.getQubo(qubo)
        for (q1,q2) in qubits:
            if ( q1>q2 ): (q1,q2) = (q2,q1)
            Q[(q1,q2)] += -(Qij)  # This is done on purpose to prevent playing with signs erroneously
    
    #
    # Apply Cubic as Quadratic function. 
    #
    # Uses the formula : axyz = aw(x+y+z-2) for (a < 0) where w is an ancillary bit
    # Uses the formula : axyz = a { w(x+y+z-1) + (xy + yz + zx) - (x + y + z ) + 1 } for (a > 0) where w is an ancillary bit
    #
    # 
    
    def ApplyTripleContribution(self, qubits, Qijk, qubo='cubic' ): # Applies -Qijk (adapted to quadratic)
        Q = self.board.getQubo(qubo)

        # Apply for Qijk < 0 method
        if ( Qijk < 0 ):
            for (qx,qy,qz,qw) in qubits:
                # Apply awx quad coeff
                Q[tuple(sorted([qw,qx]))] += Qijk   
                # Apply awy quad coeff
                Q[tuple(sorted([qw,qy]))] += Qijk   
                # Apply awz quad coeff
                Q[tuple(sorted([qw,qz]))] += Qijk   
                # Apply aw(-2) linear coeff
                Q[tuple(sorted([qw,qw]))] += (-2) * Qijk   
                
        elif ( Qijk > 0 ):   # Apply formula for Qijk > 0
            for (qx,qy,qz,qw) in qubits:
                # Apply quadratics: wx + wy + wz + xy + yz + zx
                Q[tuple(sorted([qw,qx]))] += Qijk   
                Q[tuple(sorted([qw,qy]))] += Qijk   
                Q[tuple(sorted([qw,qz]))] += Qijk   
                Q[tuple(sorted([qx,qy]))] += Qijk   
                Q[tuple(sorted([qy,qz]))] += Qijk   
                Q[tuple(sorted([qz,qx]))] += Qijk   
                # Apply linears: -w -x -y -z
                Q[tuple(sorted([qw,qw]))] += (-1) * Qijk   
                Q[tuple(sorted([qx,qx]))] += (-1) * Qijk   
                Q[tuple(sorted([qy,qy]))] += (-1) * Qijk   
                Q[tuple(sorted([qz,qz]))] += (-1) * Qijk   
                # TODO: How to apply constants: +1 ??

    #
    # Apply High Order Function (will replace TripleContribution when testing completed) 
    #
    # 
    
    def ApplyHighOrderContribution(self, qubits, Qijk_z, qubo='high-order', P=1 ): # Applies -Qijklmno...z
        Q = self.board.getQubo(qubo)
        # Get the next variable id we can use
        Y = self.board.qubits
        e = highOrderExpression(Qijk_z,qubits,self.board.highOrders)
        #e.print()
        #e.elaborate()
        #print("Next Variable before reduction", Y)
        Y = e.reduceExpression(P,Y)
        #print("Next Variable after reduction", Y)
        self.board.highOrders = e.substitutions
        #print(self.board.highOrders)
        #e.elaborate()
        e.applyQubo(Q) # Apply the weights to the given Qubo
        #Q = self.sumQubo( self.board.getQubo(qubo) , e.qubo() )
        self.board.additional.extend(e.newvars)
        self.board.qubits = Y
        #return(Q)

                
    #
    # get gap between two segments
    # 
    #
    
    def getGap(self,s1,s2):
        if ( s2.obj.task_id > s1.obj.task_id ):
            
            t1 = s1.obj.deptime + (s1.obj.depday * 1440) + s1.obj.ft # arrival day-time of segment 1
            t2 = s2.obj.deptime + (s2.obj.depday * 1440)             # departure day-time of segment 2
            gap = t2 - t1

            return (gap)
        return(0)
    
    # Get a gap considering the minimum connect time
    # If the minimum is not met, return the negative value of the gap
    def getMinGap(self,s1,s2):
        gap = self.getGap(s1,s2)
        if ( (gap > 0 ) and (gap < self.params['const_min_connect'])): gap -= self.params['const_min_connect']
        return (gap)
    
    #=============================================================================================================================
    # Build Segment Gaps Array from graph G
    # We store the "bad" gaps as negative values to differenciate from the valid gap weights
    #
    # 
    
    def buildGapsFromG(self, LG=1):
        grid = np.zeros(self.board.N).reshape(self.board.rows,self.board.cols)
        grid -= LG * self.params['const_bad'] # Initialize all gaps as a costly choice, however use a negative value to distinguish from actual gaps
        for s1, s2, gap in self.G.edges.data("weight"):
            if ( s1.isSegment() and s2.isSegment() ):
                n1 = s1.obj.task_id-1
                n2 = s2.obj.task_id-1
                grid[n1,n2] = gap 
        return(grid)

    
    #
    # Build Segment Gaps Array using the available DataSet
    #
    
    def buildGaps(self):
        grid = np.zeros(self.board.N).reshape(self.board.rows,self.board.cols)
        for s1 in self.Ann.segments: # from node
            for s2 in self.Ann.segments: # to node
                if ( s2.obj.task_id > s1.obj.task_id ):
                    #grid[s1.obj.id-1,s2.obj.id-1] = max(0,s2.obj.deptime - s1.obj.arrtime) 
                    grid[s1.obj.task_id-1,s2.obj.task_id-1] = max(0,self.getGap(s1,s2)) + (min(0,self.getGap(s1,s2)) * (self.params['const_neg_gap']))
        return(grid)

    # ================================================================================================================================
    # Build the connect stations truth table from G
    # Includes Sta to Sta and MinConnect conditions
    #
    def buildConnectFromG(self):
        grid = np.zeros(self.board.N).reshape(self.board.rows,self.board.cols)
        for s1, s2, gap in self.G.edges.data("weight"):
            if ( s1.isSegment() and s2.isSegment()):
                n1 = s1.obj.task_id-1
                n2 = s2.obj.task_id-1
                grid[n1,n2] = True 
        return(grid)
    
    # ========================================================================================
    # Build misconnections grid from non-existant edges in graph
    #
    
    def buildMisconnectFromG(self):
        grid = np.zeros(self.board.N).reshape(self.board.rows,self.board.cols)
        for n1,n2 in self.nextNodePair(self.Ann.segments,self.Ann.segments, self.noEdgesNodePair, self.G, unique=False):
            #print(self.Ann.FD.formatSegment(n1,0),"<= no connect =>", self.Ann.FD.formatSegment(n2,0))
            grid[n1.obj.task_id-1,n2.obj.task_id-1] = True 
        return(grid)        
    
    # Build the connect stations truth table
    #
    def buildConnect(self):
        grid = np.zeros(self.board.N).reshape(self.board.rows,self.board.cols)
        for s1 in self.Ann.segments: # from node
            for s2 in self.Ann.segments: # to node
                if ( s2.obj.task_id > s1.obj.task_id ):
                    grid[s1.obj.task_id-1,s2.obj.task_id-1] = (s2.obj.dep == s1.obj.arr)
        return(grid)
    
    # =============================================================================================================================
    # Build valid connecting gaps from G
    #
    def buildValidGapsFromG(self, LG=1):
        #return( self.buildConnectFromG() * self.buildGapsFromG() )
        return(  self.buildGapsFromG(LG=LG) )
    
    # Build valid connecting gaps
    #
    def buildValidGaps(self):
        return( self.buildConnect() * self.buildGaps() )
    
    # ==============================================================================================================================
    #
    def buildHomeBase(self):
        grid = np.zeros((self.board.rows,2))
        for s1 in self.Ann.segments:
            grid[s1.obj.task_id-1,0] = ( s1.obj.dep in self.Ann.HomeBases )
            grid[s1.obj.task_id-1,1] = ( s1.obj.arr in self.Ann.HomeBases )
        return(grid)
        
    # Build Station ground state contribution weights per segment
    #
    def buildStationWeights(self):
        grid = self.buildHomeBase()
        wgts = np.zeros(self.board.rows)
        for r in range(self.board.rows): 
            wgts[r] = (grid[r,0] * self.params['const_pos_h']) + ((1-grid[r,0]) * self.params['const_pos_a']) + (grid[r,1] * self.params['const_ret_h']) + ((1-grid[r,1]) * self.params['const_ret_a']) 
        return(wgts)
    
    # Build Station ground state contribution weights per segment end point
    #
    def buildEndPointWeights(self):
        grid = self.buildHomeBase()
        wgts = np.zeros((self.board.rows,2))
        for r in range(self.board.rows): 
            wgts[r,0] = (grid[r,0] * self.params['const_pos_h']) + ((1-grid[r,0]) * self.params['const_pos_a']) 
            wgts[r,1] = (grid[r,1] * self.params['const_ret_h']) + ((1-grid[r,1]) * self.params['const_ret_a']) 
        return(wgts)

    # Apply Misconnect Constraints
    # Any segment pair that has no graph edges are given a pairwise weight of bad_trip
    # This is assuming that our graph has been populated with nodes and edges for valid connection weights
    # whereby leftover unspecified edges are deemed unwanted at any cost
    #
    
    def applyNoMisconnect(self,qubo="constraint", LG=1):
        misconnects = self.buildMisconnectFromG()
        for (n1,n2,q1,q2) in self.nextBoardQuboNodePair(self.consecRows):   # Nodes must be consecutive
            self.ApplyPairwiseContribution( [(q1,q2)], misconnects[n1,n2] * self.params['const_bad'] * LG, qubo=qubo)

    # 
    #
    #
    
    def applyNoStartOffBase(self,qubo="constraint", LG=1):
        hb = self.buildHomeBase()
        departure = 0
        arrival = 1
        # No start on a non-base departure
        for ( s, r, n, qs1, q1 ) in self.nextBoardQuboStartPair(self.startOnNode):
            if ( not hb[n][departure]):
                #print("No start on", s, r, n, qs1, q1 )
                self.ApplyPairwiseContribution( [(qs1,q1)], self.params['const_bad'] * LG, qubo=qubo)
        # No start following a non-base arrival
        for ( s, r, n, qs1, q1 ) in self.nextBoardQuboStartPair(self.startAfterNode):
            if ( not hb[n][arrival]):
                #print("No start after", s, r, n, qs1, q1 )
                self.ApplyPairwiseContribution( [(qs1,q1)], self.params['const_bad'] * LG, qubo=qubo)
        
        
    # Apply segment initial Objectives contribution
    # 
    
    def applySegmentInitialContribution(self,qubo='objective'):
        contrib = self.buildStationWeights()
        for r in range(self.board.rows):
            for n in range(self.board.cols):
                q = list(self.board.getqb(r,n))
                self.ApplySingleInitialContribution(q, contrib[n], qubo)

    # Apply "start" (start of a trip) initial Objectives contribution
    # Note: Originally we did not have this. We found that Start were not being used to 
    #       break "in-base" connections. So we think the starts need a similar incentive
    #       as for the segments where we apply a Qii initial value.
    #
    # Update: Not working. Not sure why yet. 
    # Update: Revised method. See comments in applyStart
    #         We initialize with the 2 X negative bad trip value (we use 2 because start affects two segments)
    # Update: Correcting the loop to revisit this method now that we have solved other start issues.
    #         Also using the const_start value as is, removing the multiple
    #

    def applyStartInitialContribution(self,qubo='objective'):
        #hb = self.buildHomeBase()
        #for n in range(self.board.cols):
        #for q in self.board.flags:
        self.ApplySingleInitialContribution(self.board.flags, self.params['const_start'], qubo)

    # Block invalid gaps - Experimental
    
    def blockInvalidGaps(self,LG=1,qubo='constraint'):
        gaps = self.buildValidGaps()
        for n1 in range(self.board.cols):
            for n2 in range(self.board.cols):
                for r2 in range(1,self.board.rows):
                    r = r2 - 1
                    q1 = self.board.getqb(r,n1)[0]
                    q2 = self.board.getqb(r2,n2)[0]
                    if ( q1 < q2 ):
                        self.CancelPairwiseContribution( [(q1,q2)], LG, qubo  ) 
                
    # Apply segment gaps where valid
    #
    
    def applyValidGaps(self,qubo='objective', LG=1):
        hb = self.buildHomeBase()
        wgts = self.buildEndPointWeights() # Column 0 = depart, 1 = arrival
        gaps = self.buildValidGapsFromG(LG=LG)
        departure = 0
        arrival = 1

        for n1 in range(self.board.cols):
            for n2 in range(self.board.cols):
                for r2 in range(1,self.board.rows):
                    r = r2 - 1
                    q1 = self.board.getqb(r,n1)[0]
                    q2 = self.board.getqb(r2,n2)[0]
                    if ( q1 < q2 ):
                        # n1 to n2 gap
                        gap = gaps[n1,n2]
                        # Gaps > 0 are valid connections: We apply the true time cost 
                        if ( gap > 0 ):
                            # Cancel Positioning costs (initially place on Qii ground states)
                            # n1 arrival point
                            self.ApplyPairwiseContribution( [(q1,q2)], wgts[n1,arrival], qubo  )
                            # n2 departure point
                            self.ApplyPairwiseContribution( [(q1,q2)], wgts[n2,departure], qubo  )
                            # n1 to n2 time gap
                            self.ApplyPairwiseContribution( [(q1,q2)], gap, qubo='-gaps-') # Must use a dedicated gaps qubo to make them cancellable
                        # Zero gaps are not valid connection: We apply a "badtrip" cost. However this is a cancellable cost if 
                        # a "Start" is inserted to break the connection (thus we assign to the -gaps- qubo)
                        else:
                            # Base to Base reverse gaps should be Cancellable. Others not.
                            gap_qubo = 'invalid-gaps'
                            # Detect base to base to make the gap cancellable
                            if ( hb[n1][arrival] and hb[n2][departure]):
                                gap_qubo = '-gaps-'
                            # Making non-cancellable gap for bad connections
                            self.ApplyPairwiseContribution( [(q1,q2)], -gap, qubo=gap_qubo) # 
                            #self.ApplyPairwiseContribution( [(q1,q2)], self.params['const_bad'], qubo='invalid-gaps') 
                    else:
                        print("applyValidGaps: Warning, this pair might have been missed, consider sorting:", q1, q2)

                            
        
    # Apply Segment Starts condition:
    # 
    # 15 Oct 2020: Revamped Start method
    # 26 Oct 2020: Edges alone do not dictate how starts are applied. 
    #
    # 1) Start adds CI as a PairWise with the target segment (CI is obtained from G weights in edges)
    # 2) Start adds a CO as a PairWise with the previous to target (CO is obtained from G weights in edges)
    # 3) Start adds a 3 way weight between target,previous (and ancilla bit)
    # 4) For non existing edges, place a bad_trip penalty instead of CI on a segment
    # 5) For non existing edges, place a bad_trip penalty instead of CO on a previous segment
    # ** Respect the order such that target is not confused with the previous to target
    # ** Use the G graph
    
    def applyStart(self,qubo='objective', P=1):
        wgts = self.buildEndPointWeights() # Column 0 = depart, 1 = arrival
        departure = 0
        arrival = 1
        
        # Bad trip weight
        bad_trip = self.params['const_bad']
        # Start node id offset
        soff = self.board.cols
        
        # Obtain the gap from the "gaps" qubo
        gap_qubo = self.board.getQubo('-gaps-')

        # Traverse Qubo to apply ChkI and Cancel Gaps
        for r in range(0,self.board.rows-1): # All rows except last
            s = r + soff
            for n in range(self.board.cols):
                #print("Start Contributions for Row",r,"Node",n,".............................")
                valid_found = False
                # For valid edges, Start to Segment add the check in time
                for s1, n1, chkI in self.G.edges.data("weight"):
                    #print("Start object id", s1.obj.id, "start row item", s ,"for row",r, "(offset is",soff,")")
                    if ( s1.isStart() and n1.isSegment() and (n1.obj.task_id-1 == n) and (s1.obj.task_id-1==s)):

                        valid_found = True
                        qs1 = self.board.flags[r] 
                        #qw1 = self.board.ancil[r]   
                        q1 = self.board.getqb(r,n)[0]                    
                        # Add Check In time
                        (qn1,qn2) = sorted((qs1,q1))

                        # Handle the first row cancelling of the initial positioning cost (unsequenced segment). For other rows, this is done
                        # via pairwise between two segment nodes. However, for the first row, this needs to 
                        # be handled by the Start node.

                        if ( r == 0 ):
                            # n1 departure point weight cancellation to be replaced by ChkI
                            self.ApplyPairwiseContribution( [(qn1,qn2)], wgts[n,departure], qubo  )

                        # Apply the 
                        self.ApplyPairwiseContribution([(qn1,qn2)] , chkI, qubo=qubo)
                        #print("Applying check in time", chkI, "with Start variable",qs1, "at node variable",q1)
                        
                        # If we have a previous row, cancel gaps between this node and previous nodes
                        pr = r - 1
                        if ( pr >= 0 ):
                            for pn in range(self.board.cols):
                                q2 = self.board.getqb(pr,pn)[0]    
                                (qn1,qn2) = sorted((q1,q2))
                                gap = gap_qubo[(qn1,qn2)]
                                if ( gap > 0 ):
                                    contribution = -gap  
                                    #print("Applying cubic value", contribution,"to",qn1,qn2,qs1,qw1)
                                    #self.ApplyTripleContribution([(qn1,qn2,qs1,qw1)], contribution, qubo='cubic-gap' )
                                    #print("     >>> Cancelling gap", gap, "between",q2,"and",q1,"due to start",qs1)
                                    #print(self.Ann.tg.formatSegment(self.Ann.segments[pn],0), "<==>",self.Ann.tg.formatSegment(n1,0))
                                    self.ApplyHighOrderContribution([qn1,qn2,qs1], contribution, qubo='cubic-gap', P=P )
                                    #print("Total variables in use: ", self.board.qubits)

                # If no valid edge found between start s and segment n, then we need to apply a heavy cost
                # to starting a trip here     
                # ** This is already better handled as a constraint. Comment out.
                #if ( not valid_found ):
                #    qs1 = self.board.flags[r] 
                #    q1 = self.board.getqb(r,n)[0]                    
                #    (qn1,qn2) = sorted((qs1,q1))
                #    self.ApplyPairwiseContribution([(qn1,qn2)] , bad_trip, qubo=qubo)
                #    #print("Applying bad trip between Start variable",qs1, "and node variable",q1)
                    
                                
        # Traverse Qubo to apply ChkO
        for r in range(1,self.board.rows): # All rows except first
            for n in range(self.board.cols):
                valid_found = False
                s = r + soff
                pr = r - 1
                #print("End Contributions for Previous Row",pr,"Node",n,".............................")
                # For valid edges, Segment to Start add the check out time
                for n1, s1, chkO in self.G.edges.data("weight"):
                    if ( s1.isStart() and n1.isSegment() and (n1.obj.task_id-1 == n) and (s1.obj.task_id-1==s)):
                        valid_found = True
                        qs1 = self.board.flags[r]   
                        q1 = self.board.getqb(pr,n)[0]    # Prior row nodes                
                        # Add Check Out time
                        (qn1,qn2) = sorted((qs1,q1))
                        self.ApplyPairwiseContribution([(qn1,qn2)] , chkO, qubo=qubo)
                        #print("Applying check out time", chkO, "with Start variable",qs1, "at previous node variable",q1)

                # If no valid edge found between start s and segment n, then we need to apply a heavy cost
                # to starting a trip here               
                # ** This is already better handled as a constraint. Comment out.
                #if ( not valid_found ):
                #    qs1 = self.board.flags[r]   
                #    q1 = self.board.getqb(pr,n)[0]    # Prior row nodes                
                #    (qn1,qn2) = sorted((qs1,q1))
                #    self.ApplyPairwiseContribution([(qn1,qn2)] , bad_trip, qubo=qubo)
                #    #print("Applying bad trip between Start variable",qs1, "and previous node variable",q1)        


    # Return the sum of a Qubo diagonal
    def sumQii(self,Q):
        qii_sum = 0.0
        for e in Q:
            (i,j) = e
            if ( i == j ):
                qii_sum += Q[e]
        return qii_sum

    # Return the sum of Qubo off-diagonal items
    def sumQij(self,Q):
        qij_sum = 0.0
        for e in Q:
            (i,j) = e
            if ( i < j ):
                qij_sum += Q[e]
        return qij_sum

    # Return the sum of Qubo values for selected variables
    # Include highOrder substitutions that may occur
    
    def sumQselect(self,Q,variables, inclSubs=True):
        qij_sum = 0.0
        if ( inclSubs ):
            additional = self.collectHighOrder(variables)
            variables.extend(additional)
            #print("Additional variables included in qubo sum", additional)
            #print("Variables to be summed", variables)
        
        for i in variables:
            qij_sum += Q[(i,i)]
            for j in variables:
                if ( i < j ):
                    qij_sum += Q[(i,j)]
        return qij_sum
    
    def collectHighOrder(self,variables):
        result = []
        found_additional = True
        while( found_additional ):
            additional = []
            found_additional = False
            for i in variables:
                for j in variables:
                    if ( i < j ):
                        v = highOrderExpression.varkey(self,[i,j])
                        if ( v in self.board.highOrders ):
                            newvar = self.board.highOrders[v]
                            if (( newvar not in additional ) and (newvar not in result) and (newvar not in variables)):
                                additional.extend([newvar])
                                found_additional = True
                                #print("including", newvar, "for pair",v )
            result.extend(additional)
            variables = additional
        return(result)
        
    # ============================================================================================
    # Edge creation decision function
    # ============================================================================================
    
    def createEdge(self,n1,n2):
        hb = self.buildHomeBase()
        departure=0
        arrival=1
        # Stations connect?
        doesConnect = (n1.obj.arr == n2.obj.dep)
        # Sequential connection?
        gap = self.getGap(n1,n2)
        posGap = (gap > 0)
        # Departure on n2 is a base?
        isBase = hb[n2.obj.task_id-1,departure]
        # Minimum Connect time?
        doesMinConnect = (self.getMinGap(n1,n2) > 0 )
        badtrip = self.params['const_bad']
        cancellable_badgap = gap * (self.params['const_neg_gap']) # Only valid when gap is negative as per table below
        # Maximum connect time
        doesMaxConnect = (gap < self.params['const_max_connect']) # 
        
        # TESTING - PROTOTYPE Max Fly 2X2 code
        # When doesConnect and doesMinConnect, BUT the gap is NOT large enough for crew rest
        # we declare that the nodes do NOT have minimum connection in the situation where the 
        # sumof the n1 and n2 flight time is larger than the max 2X2 flight time
        #
        # Testing result: Problem size increases for the QC. We need to optimize the method.
        # The real solution is to properly implement the "floating wraparound days" methodology
        # For now, we will keep the original method, and process the result classically
        #if ( doesConnect and doesMinConnect and posGap and doesMaxConnect):
        #    if ( gap < self.params['const_min_prone_rest']):  #
        #        if ( n1.obj.ft + n2.obj.ft > self.params['const_max_fly_2X2']):
        #            print("Disallowing",n1.obj.lab,"from connecting to",n2.obj.lab,"because rest is insufficient and 2x2 flight time exceeds the limit")
        #            doesMinConnect = False

        #  n1.arr==n2.dep   Gap(n1,n2) > 0  n2.dep is a Base  Gap > min   |  Create an Edge   |  Weight
        # (connect,posGap,isBase,minGap,maxGap)
        #
        # Returns tuple as ( createEdge, Weight, Cancellable )
        
        dMatrix = {}
        dMatrix[(1,1,1,1,1)] = (1,gap,1)    #   "Y          |   gap,    cancellable",
        dMatrix[(1,1,0,1,1)] = (1,gap,1)    #,      "Y          |   gap,    cancellable",
        dMatrix[(1,0,1,1,1)] = (1,cancellable_badgap,1) #,      "Y          |   badgap, cancellable",
        dMatrix[(1,0,0,1,1)] = (0,0,0)      #,      "N          |   N/A",
        dMatrix[(0,1,1,1,1)] = (0,0,0)      #,      "N          |   N/A",
        dMatrix[(0,1,0,1,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(0,0,1,1,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(0,0,0,1,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(1,1,1,0,1)] = (1,cancellable_badgap,1) #,      "        Y          |   badtrip, cancellable",
        dMatrix[(1,1,0,0,1)] = (0,0,0)      #,      "        N          |   N/A",

        #dMatrix[(1,0,1,0,1)] = (1,cancellable_badgap,1) #,      "        Y          |   badgap, cancellable",
        dMatrix[(1,0,1,0,1)] = (0,0,0) #,      "        N          |   badgap, cancellable",

        dMatrix[(1,0,0,0,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(0,1,1,0,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(0,1,0,0,1)] = (0,0,0)      #,      "        N          |   N/A',
        dMatrix[(0,0,1,0,1)] = (0,0,0)      #,      "        N          |   N/A",
        dMatrix[(0,0,0,0,1)] = (0,0,0)      #,      "        N          |   N/A"

        dMatrix[(1,1,1,1,0)] = (0,0,0)   
        dMatrix[(1,1,0,1,0)] = (0,0,0)   
        dMatrix[(1,0,1,1,0)] = (0,0,0) 
        dMatrix[(1,0,0,1,0)] = (0,0,0)    
        dMatrix[(0,1,1,1,0)] = (0,0,0) 
        dMatrix[(0,1,0,1,0)] = (0,0,0) 
        dMatrix[(0,0,1,1,0)] = (0,0,0) 
        dMatrix[(0,0,0,1,0)] = (0,0,0) 
        dMatrix[(1,1,1,0,0)] = (0,0,0) 
        dMatrix[(1,1,0,0,0)] = (0,0,0) 
        dMatrix[(1,0,1,0,0)] = (0,0,0) 
        dMatrix[(1,0,0,0,0)] = (0,0,0)  
        dMatrix[(0,1,1,0,0)] = (0,0,0)    
        dMatrix[(0,1,0,0,0)] = (0,0,0)  
        dMatrix[(0,0,1,0,0)] = (0,0,0)    
        dMatrix[(0,0,0,0,0)] = (0,0,0)     

        
        return( dMatrix[(doesConnect, posGap, isBase, doesMinConnect, doesMaxConnect)])

        
    # ============================================================================================
    # Graph functionality - Some are replacing the Anneal fucntionality 
    # ============================================================================================

    # build graph from segments for processing
    # Each graph node is an object of type Node

    def buildFltGraph(self, fltonly = False, view=False):

        segments = self.Ann.segments
        states = self.Ann.states

        # TODO: Consider sorting and re-indexing segments
        
        G = nx.DiGraph()

        # Build the segments connectivity graph. Assign the time gap to the weight value
        
        for n1 in segments:
            for n2 in segments:
                if ( n1.task_id >= n2.task_id ): continue  # This may need to be optional for other models that allow re-timing a segment

                # Truth Table for edges
                #
                # Applicability: Creating an Edge in the Graph means that we allow two nodes to be sequenced consecutively, baring 
                #                additional constraints.
                # In other words: If we do not create an edge between two nodes, they will NEVER be allowed to be consecutive to each other.
                # 
                #    n1.arr==n2.dep   Gap(n1,n2) > 0  n2.dep is a Base  Gap > min   |  Create an Edge   |  Weight
                #    --------------   --------------  ----------------  ----------- |  ---------------  |  ------
                #          1                1                1               1      |        Y          |   gap,    cancellable
                #          1                1                0               1      |        Y          |   gap,    cancellable
                #          1                0                1               1      |        Y          |   badgap, cancellable
                #          1                0                0               1      |        N          |   N/A
                #          0                1                1               1      |        N          |   N/A
                #          0                1                0               1      |        N          |   N/A
                #          0                0                1               1      |        N          |   N/A
                #          0                0                0               1      |        N          |   N/A
                #          1                1                1               0      |        Y          |   badgap, cancellable
                #          1                1                0               0      |        N          |   N/A
                #          1                0                1               0      |        Y          |   badgap, cancellable
                #          1                0                0               0      |        N          |   N/A
                #          0                1                1               0      |        N          |   N/A
                #          0                1                0               0      |        N          |   N/A
                #          0                0                1               0      |        N          |   N/A
                #          0                0                0               0      |        N          |   N/A
                
                ( doEdge, gap, cancellable ) = self.createEdge(n1,n2)

                #if ( gap < 0 and doEdge ):
                #    print("Implemented negative gap between",self.Ann.FD.formatSegment(n1,0),"and",self.Ann.FD.formatSegment(n2,0))                      

                if ( doEdge ):
                    if ( view ):
                        l1 = n1.obj.lab + '/' + str(n1.obj.depday)
                        l2 = n2.obj.lab + '/' + str(n2.obj.depday)
                        G.add_weighted_edges_from([(l1,l2, abs(gap) )])
                    else:
                
                        # Cancellable gap must be negative. If not cancellable, store weight as a positive

                        if ( cancellable ): 
                            gap = -abs(gap)
                        else:
                            gap = abs(gap)
                    
                        G.add_weighted_edges_from([(n1,n2, gap )])      
                        
                        #if ( gap < 0 ):
                        #    print("Implemented negative gap between",self.Ann.FD.formatSegment(n1,0),"and",self.Ann.FD.formatSegment(n2,0))                      
                else:
                    pass
                    #print("No edge for", self.Ann.FD.formatSegment(n1,0),"<= no connect =>", self.Ann.FD.formatSegment(n2,0)) 

        if ( not fltonly ):

            for start in states:
                for seg in segments:
                    
                    # Order is important: Start->Segment represents the beginning of a cycle
                    # Build the valid Start to leading Segments and assign the Check In value
                    # Valid for homebase only
                    
                    if seg.obj.dep in self.Ann.HomeBases:
                        if ( view ):
                            G.add_weighted_edges_from([(start.task_id,seg.task_id,self.params['const_CI'])])
                        else:
                            G.add_weighted_edges_from([(start,seg,self.params['const_CI'])])
                            
                    # Order is important: Segment->Start represents the end of a cycle
                    # Build the valid ending Segments to a Start and assign the Check Out value
                    # Valid for homebase only
                    
                    if seg.obj.arr in self.Ann.HomeBases:
                        if ( view ):
                            G.add_weighted_edges_from([(seg.task_id,start.task_id,self.params['const_CO'])])
                        else:
                            G.add_weighted_edges_from([(seg,start,self.params['const_CO'])])

        return G

    # =====================================================================================================
    # Generators for traversing the connections space between nodes
    #
    # =====================================================================================================

    # =====================================================================================================
    # Any pair of two nodes from two sets (may be the same set)
    # =====================================================================================================
    
    def nextNodePair(self,nodes1,nodes2, match=None, opt=None, unique=True):
        for n1 in nodes1:
            for n2 in nodes2:
                #if ( n1 == n2 ): continue
                if ( unique and (n1.task_id >= n2.task_id )): continue
                if ( match is not None ):
                    if ( not match(n1,n2,opt)): continue
                        
                yield (n1,n2)

    # =====================================================================================================
    # Any pair of items on the board returned as node ids and variable ids (qubits)
    # =====================================================================================================
    
    def nextBoardQuboNodePair(self,match=None):
        for r in range(self.board.rows):
            for n1 in range(self.board.cols):
                q1 = self.board.getqb(r,n1)[0]   
                for r2 in range(self.board.rows):
                    for n2 in range(self.board.cols):
                        q2 = self.board.getqb(r2,n2)[0]
                        if ( q1 >= q2 ): continue
                        if (( match is not None ) and ( not match(r,r2))): continue
                            
                        yield  (n1,n2,q1,q2) 

    # =====================================================================================================
    # Any pair of (start,node) on the board returned as node ids and variable ids (qubits)
    # =====================================================================================================
    
    def nextBoardQuboStartPair(self,target=None):
        for s in range(self.board.rows):
            qs1 = self.board.flags[s]
            for r in range(self.board.rows):
                for n in range(self.board.cols):
                    if ( target is not None ):
                        if ( not target(s,r,n)): continue                    
                        q1 = self.board.getqb(r,n)[0]
                        
                        yield (s,r,n,qs1,q1)
                    

    # =====================================================================================================
    # Matching/filter conditions
    # =====================================================================================================
    
    # Has an edge in the graph
    def edgesNodePair(self,n1,n2,G):
        if ( (n1,n2) in G.edges ): return True
        return False

    # Has no edge in the graph
    def noEdgesNodePair(self,n1,n2,G):
        if ( not self.edgesNodePair(n1,n2,G) ): return True
        return False

    # Consecutive row nodes
    def consecRows(self,r1,r2):
        return( r2 == r1+1 )

    # Start is for the current item row
    def startOnNode(self,s,r,n):
        if (s==r): return True
        return False
    
    # Start is for the previous item row
    def startAfterNode(self,s,r,n):
        if (s==r+1): return True
        return False
    
                