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

from dimod.binary_quadratic_model import BinaryQuadraticModel
from tabu import TabuSampler        
from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler
import neal

from quzzi.qznodes import Node, Segment, Start
from quzzi.qzfsched import schedData
from quzzi.qubotrips import QuboTrips

class routeAnneal:

    # Default Test Case
    def buildSet1(self):
        segments=[]
        segments.append( Node(Segment(1, "X01", "LCA", "ATH", 600, 695, 1, 1,self.HomeBases)))
        segments.append( Node(Segment(2, "X02", "ATH", "LCA", 755, 845, 1, 1,self.HomeBases)))
        segments.append( Node(Segment(3, "X03", "LCA", "ATH", 875, 970, 1, 1,self.HomeBases)))
        segments.append( Node(Segment(4, "X04", "ATH", "LCA", 1035, 1125, 1, 1,self.HomeBases)))
        return(segments)

    def getN(self):
        return (self.FD.N)

    def getG(self):
        return (self.QT.G)
    
    def getT(self):
        return (self.T)
    
    def getHomeBases(self):
        return self.HomeBases

    # TODO: Base handling work in progress 
    def getHomeBaseWeightOffset(self):
        return self.HomeBaseWeightOffset
    
    def __init__(self,dataset="",homebases={},atypes=[],depday=None):
        
        self.states = []
        self.segments = []
        self.HomeBases = homebases
        self.NotHomeBaseWeight = 0 # self.makeBaseWeight(len(self.HomeBases)+1) 
        self.FD = schedData()                         # Flight Data Object
        # Load the data

        if ( type(dataset) == type(self.segments)):
            self.FD.set(dataset)
        else:
            if ( dataset != "" ):
                self.FD = schedData(dataset, Atypes=atypes, depDay = depday, HomeBases=self.HomeBases )
            else:
                self.FD.set(self.buildSet1())
            
        self.QT = QuboTrips(self,self.FD.N,norm=1000) # quboTrips object. TODO: Resolve the reference back to routeAnneal
        
        self.segments = self.FD.segments
        self.N = self.getN()

        # Create the trip Start state objects. 
        state_origin = self.N+1;
        self.states = []
        for s in range(self.N):
            self.states.append(Node(Start(state_origin+s,"start")))
        
        # TODO: Decide on applicability of this including self.T
        #print ("Minimum Dep", min(node.obj.deptime + ((node.obj.depday-1)) * 1440 for node in self.segments))
        #print ("Maximum Arr", max(node.obj.arrtime + ((node.obj.arrday-1)) * 1440 for node in self.segments))
        # Set T as the range of time fully enclosing all segments, plus buffer
        self.T = max(node.obj.getUarrtime() for node in self.FD.segments) + (2 * 1440) # We add buffer of 1 day prior and 1 day after

        # TODO: This needs to use the QuboTrips parameters or be in line with them
        # We are not currently using this information from segments in quboTrips
        for seg in self.segments:
            seg.obj.setT(self.T)
            seg.obj.setCI(60) # Checkin Time TODO: Parameterize this
            seg.obj.setCO(30) # Check out time. TODO: Parameterize this
            #print( seg.obj.id, seg.obj.getUT1(), seg.obj.getUT2(), seg.obj.getUT(), seg.obj.ft,seg.obj.getUT()+seg.obj.ft )

    # Solver for Q 
    # Gets Q from the final Qubo prepared in QT
    def solve(self, 
              useQPU=False, 
              useNeal=False, 
              useHyb=True,
              useGrb = False,
              name = "",
              time_limit = 10,
              num_reads = 100,
              chain_strength = 10000,
              verbose=True):
        
        Q = self.QT.finalQubo()
        
        BQM_offset = 0 # TODO: Use the accumulated quadratic constants from the constraints

        bqm = BinaryQuadraticModel.from_qubo(Q, offset=BQM_offset)

        self.sampleset = None
        
        # Call the requested solver
        
        if ( useQPU ):
            if ( verbose ): print("Solving using the DWaveSampler on the QPU...")
            sampler = EmbeddingComposite(DWaveSampler(solver={'qpu': True}))
            sampleset = sampler.sample_qubo(Q, num_reads=num_reads, chain_strength = chain_strength, label=name)
        elif ( useHyb ): 
            if ( verbose ): print("Solving using the LeapHybridSolver...", end='')
            sampler = LeapHybridSampler()
            time_limit = max(time_limit,sampler.min_time_limit(bqm))
            if ( verbose ): print( "(time limit is",time_limit,")")
            sampleset = sampler.sample(bqm, time_limit = time_limit, label=name)
        elif ( useNeal ): 
            if ( verbose ): print("Solving using the SimulatedAnnealing...")
            sampler = neal.SimulatedAnnealingSampler()
            sampleset = sampler.sample(bqm, num_reads = num_reads)
        elif ( useGrb ): 
            if ( verbose ): print("Solving using the Gurobi Quadratic...")
            #sampler = neal.SimulatedAnnealingSampler()
            sampleset = self.solveQGrb(Q,nreads=num_reads)
        else:
            if ( verbose ): print("Solving using the TabuSampler...")
            sampler = TabuSampler()
            sampleset = sampler.sample(bqm, num_reads = num_reads)

        self.sampleset = sampleset
        
        count = 0
        for res in self.sampleset.data(): count += 1
        
        return (count)

    '''
    # Experimental Quadratic solver using Gurobi
    
    # Gurobi support
    import gurobipy as gp
    from gurobipy import GRB
    
    def solveQGrb(self,Q,nreads=1):
        
        with gp.Env(empty=True) as env:
            
            with Capturing() as discardOutput:
                env.setParam('LogToConsole', 1)
            env.start()

            try:

                # Create a new model
                with gp.Model("Qubo1", env=env) as m:

                    # Initialize our Hamiltonian (objective to minimize)
                    obj = gp.QuadExpr();
        
                    # Initialize our variables dictionary
                    x={}
                        
                    # Create the variables enumerated as x0,x1,x2,...
                    # from the Qubo diagonal
        
                    for (i,j) in Q.keys():
                        if ( i == j ):
                            if i not in x:
                                x[i] = m.addVar(vtype=GRB.BINARY, name=str(i))
                            obj += Q[(i,i)] * x[i]
        
                    # Add the pairwise coefficients from the Qubo to our Hamiltonian
        
                    for (i,j) in Q.keys():
                        if ( j > i ):
                            if i not in x:
                                x[i] = m.addVar(vtype=GRB.BINARY, name=str(i))
                            if j not in x:
                                x[j] = m.addVar(vtype=GRB.BINARY, name=str(i))
                            obj += Q[(i,j)] * x[i] * x[j];

                    # Add constraints : 
                    # 1 - Exactly N variables within the range N * N must be set to 1
                    EN = self.QT.board.cols
                    #model.addConstrs((quicksum(smatr[i,j] * v[j] for i in met) == 0) for j in reactions
                    #m.addConstrs([x[i] <= 1 for i in range(EN * EN)], name='coverage')
                    print("Constraint: Sum of", EN*EN, "variables must less or equal to",EN)
                    m.addConstr(gp.quicksum(x[i] for i in range(EN*EN))==EN, name="coverage")
                    #m.addConstr(gp.quicksum(x[i] for i in range(EN*EN))>=EN-1, name="coverage")
                    print("Constraint: No more than", EN/2, "start flags")
                    m.addConstr(gp.quicksum(x[i] for i in range(EN*EN,EN*EN+EN)) <= EN/2, name="coverage")

                    print("Constraint: Sum of each", EN, "row variables must be equal to 1")
                    for r in range(EN):
                        m.addConstr(gp.quicksum(x[c+r*EN] for c in range(EN)) == 1.0, name="row=1")

                    print("Constraint: Sum of each", EN, "column variables must be equal to 1")
                    for c in range(EN):
                        m.addConstr(gp.quicksum(x[c+r*EN] for r in range(EN)) == 1.0, name="col=1")


                    # Set our complete objective
                    m.setObjective(obj, GRB.MINIMIZE);
                    
                    # Optimize model
                    m._maxreads = nreads
                    m._numreads = 0
                    m._solveQGrb_results = []

                    m.write("GOutput.MPS")
                                    
                    m.optimize(solveQGrb_callback)
                    
                    # Create a dimod compatible sampleset
        
                    arr = np.zeros(len(m.getVars()))   
                    for v in m.getVars():
                        arr[int(v.varName)] = 1.0 if v.x > 0.5 else 0.0
                    m._solveQGrb_results.append(list(arr))
        
                    sampleset = None
                    for r in m._solveQGrb_results:
                        variables = [i for i,v in enumerate(r) if v > 0.5]
                        energy = 0.0
                        if ( len(variables) ):
                            energy = self.QT.sumQselect(Q,variables)
                        
                        s = SampleSet.from_samples(r, 'BINARY', energy)
                        if sampleset is None:
                            sampleset = s
                        else:
                            sampleset = dimod.concatenate((sampleset,s))
                    
                    return sampleset
        
            except gp.GurobiError as e:
                print('Error code ' + str(e.errno) + ': ' + str(e))
            
            except AttributeError:
                print('Encountered an attribute error')
'''
        
    def print_all(self,max_v=3,solver="unknown"):
        self.FD.print_all(self.sampleset,max_v,QT=self.QT)
        self.FD.print_sequences(self.sampleset, max_v, solver=solver)

# Utilities and add-ons

from io import StringIO 
import sys

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
        
'''
#=============================================#
# Special Gurobi callback since there appears #
# to be no method for such a callback within  #
# a class at this time                        #
#=============================================#

def solveQGrb_callback(model,where):  # Callback to capture intermediate new results
    if where == GRB.Callback.MIPSOL:
        #print(model.__dict__)
        arr = [1.0 if a > 0.5 else 0.0 for a in model.cbGetSolution(model.getVars()) ]   
        model._solveQGrb_results.append(arr)
        model._numreads += 1
        if ( model._numreads >= model._maxreads):
            model.terminate()

'''