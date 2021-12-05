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

import time

#==============================================================================================#
# s2fsched (c) 2020 Mario Guzzi                                                         #
#                                                                                              #
# class bench: Benchmarking tool for solving multiple profiles of solvers                      #
#                                                                                              #
#                                                                                              #
#==============================================================================================#


class bench:
    
    
    def __init__(self,A,task_id=0):
        self.task_id = task_id
        self.A = A
        # [QPU,Neal,Hyb]
        self.solvers = {"tabu":[0,0,0,0], "neal":[0,1,0,0], "qpu":[1,0,0,0], "hyb":[0,0,1,0], "grb":[0,0,0,1], "def":[0,0,0,0]}
        # Profiles
        self.profiles = []
        
        # Results collection
        self.results = {}
        self.count = 0
        self.best_energy = 0.0
        self.best_result = None
        self.best_solver = None
        self.best_profile = None
        self.best_time = None
        
        # Output collection
        self.output = []

    
    def clear(self):
        self.profiles.clear()
        self.profiles = []
    
    def validSolvers(self,solvers):
        if (solvers is None): return False
        for s in solvers:
            if ( s not in self.solvers ): return False
        return(True)
    
    def add(self,name=None, solvers=["def"],reads=[100],time=[3],chain=[1]):
        if ( not self.validSolvers(solvers)): return (False)
        if (len(time)<=0): time=[0]
        if (len(reads)<=0): reads=[0]
        if (len(chain)<=0): chain=[0]
        if ( name is None ): name = "profile "+str(len(self.profiles)+1)

        profile = {}
        profile['name'] = name
        profile['solvers'] = solvers
        profile['reads'] = reads 
        profile['time'] = time
        profile['chain'] = chain 
        self.profiles.append(profile)
        return(self)
    
    def list(self):
        for i,p in enumerate(self.profiles):
            print("Profile",i+1)
            maxL = max(len(k) for k in self.profiles[i])+1
            fmt = "{:"+str(maxL)+"} :"
            for j,k in enumerate(self.profiles[i]):
                print(fmt.format(k),self.profiles[i][k])

    def next(self):
        # For each profile
        for p, prof in enumerate(self.profiles):
            #print("Profile",p,prof)
            # For each solver
            for solv in prof['solvers']:
                #print(solv)
                selection = self.solvers[solv]
                
                # For each time limit
                for time in prof['time']:
                    
                    # For each reads
                    for reads in prof['reads']:
                        
                        # For each chain 
                        for chain in prof['chain']:
                            
                            yield (prof['name'], p, solv, selection, time, reads, chain )
    
    def process(self,max_v=1,verbose=True,task_id=None, q=None):
        
        #with Capturing() as self.output:
        for (name, prof, solv, selection, rtime, reads, chain ) in self.next():

            t1 = time.time()
            #print("Time 1 = " + str(t1))
            t2 = t1
            
            if ( verbose ):
                print("Solving Profile: {:16} Solver: {:8} Time: {} -- Reads: {} -- Chain: {}".format(name, solv, rtime, int(reads),chain))

            maxtry = 3
            tries = 0
            while(tries < maxtry):

                if ( tries ): print( "Warning: Retry #",tries,"...")

                try:
                    # Solve
                    self.A.solve(useQPU=selection[0], 
                                 useNeal=selection[1], 
                                 useHyb=selection[2],
                                 useGrb=selection[3],
                          name=name,
                          time_limit = rtime,
                          num_reads = int(reads),
                          chain_strength = chain,verbose=verbose)

                    t2 = time.time()
                    #print("Time 2 = " + str(t2))
                    break
                except Exception as e:
                    tries += 1
                    print("Warning: Error reaching solver:", e)


            if ( tries >= maxtry ):
                print("Error: Could not recover from errors. Moving on...")
                # TODO: What to store for a result when no result is obtained? 
                #       Currently we record nothing.
            else:

                for res in self.A.sampleset.data():
                #print(A.sampleset.data())
                    self.energy = res[1]
                    self.results[self.count]={}
                    self.results[self.count]['name'] = name
                    self.results[self.count]['params'] = (rtime,reads,chain)
                    self.results[self.count]['energy'] = self.energy
                    self.results[self.count]['result'] = res
                    self.results[self.count]['sampleset'] = self.A.sampleset
                    #self.results[self.count]['routes'] = self.A.FD.getRoutes(self.A.sampleset)
                    self.results[self.count]['starttime'] = t1
                    self.results[self.count]['time'] = t2 - t1
                    self.results[self.count]['better'] = False
                    self.results[self.count]['best_energy'] = (self.results[self.count-1]['best_energy'] if self.count > 0 else  self.energy )
                    self.results[self.count]['atime'] = t2 - self.results[0]['starttime']
                    self.results[self.count]['nodes'] = self.A.QT.board.cols 
                    self.results[self.count]['vars'] = self.A.QT.board.qubits
                    #self.results[self.count][''] = 
                    #self.results[self.count][''] = 
                    
                    
                    
                    if ( verbose ):
                        print("Energy",self.energy)

                    if ( self.energy < self.best_energy ):
                        self.results[self.count]['better'] = True
                        self.results[self.count]['best_energy'] = self.energy
                        self.best_energy = self.energy
                        self.best_result = self.count
                        self.best_solver = solv
                        self.best_profile = name
                        self.best_time = t2-t1
                        if ( verbose ): 
                            self.A.print_all(max_v=max_v,solver=solv)

                    # Log the result
                    #self.logResult(name,solv,self.count)

                    break;

                self.count += 1
                    
        if ( q is not None ):
            q.put(task_id,self)
                    
        #return(self)

        # Logging functions

    # LogString: 
    # 
    # timestamp:benchmark:model:resultid:energy:better:best_energy:rtime:btime:nodes:vars

    def logString(self,name,model,resid,energy,better,besten,restime,benchtime,nodes,qvars):
        timestamp = time.time()
        output = "{ts},{bk},{mod},{rid},{en},{bet},{best},{rtim},{btim},{n},{v}\n" \
        .format( \
                ts = timestamp, \
                bk = name,
                mod = model, \
                rid = resid, \
                en = energy, \
                bet = ("Y" if (better == True) else "N"), \
                best = besten, \
                rtim = restime, \
                btim = benchtime, \
                n = nodes, \
                v = qvars )

        return output

    # clear log file
    
    def logClear(self,filename="log.txt"):
        with open(filename, 'w') as out_file:
            out_file.write("\n")
            out_file.close()
        
    # Log one result
    def logResult(self,name,solver,instance=None,filename="log.txt"):

        b = self
        
        if ( instance == None ):
            instance = b.count
            
        r = b.results[instance]

        out = self.logString(name, \
                             solver, \
                             instance, \
                             r['energy'], \
                             r['better'], \
                             (r['energy'] if r['better']=='Y' else b.best_energy), \
                             r['time'], \
                             r['atime'], \
                             r['nodes'], \
                             r['vars'])

        with open(filename, 'a') as out_file:
            out_file.write(out)
            out_file.close()

        return out

