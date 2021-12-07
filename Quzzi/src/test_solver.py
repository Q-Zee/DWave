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


import matplotlib.pyplot as plt
import numpy as np

from quzzi.qzanneal import routeAnneal
from quzzi.tripModel import tripModel
from quzzi.qzbench import bench

# Change dir to correct location

import os
os.chdir('Quzzi/src')

# Close plots

plt.close('all')

# Initializes models

models = []

for days in [[1]]: 
    # Initialize a model
    #ra =  routeAnneal(dataset="..\datasets\FCMar4-1.csv",homebases={"LCA":1},atypes=[],depday=days)
    #ra =  routeAnneal(dataset="..\datasets\DS2b.csv",homebases={"LCA":1},atypes=[],depday=days)
    ra =  routeAnneal(dataset="../datasets/DS2b.csv",homebases={"LCA":1},atypes=[],depday=days)
    model = tripModel().annealer(ra)

    model.A.FD.list_segments()
    model.drawGraph()

    model.A.QT.params['const_neg_gap'] = 0 # Testing. Questionning the pertinence of reducing negative gaps this way.

    model.printParams()
    #model.inspectTables()

    model.setConstraints()  # This is where we need methods to alter contents of the setConstraints to perform benchmarks
    #model.printParams()
    model.inspectQubos()
    model.inspectTables()
    model.A.QT.board.info()
    models.append(model)

print(len(models),"models")

benchmarks = []
for m, model in enumerate(models):
    #B = bench(model.A,len(benchmarks))
    #B.add("Model "+str(m+1), solvers=["hyb"], time=np.linspace(1,1,1))
    #B.add("Model "+str(m+1), solvers=["qpu"], reads=np.linspace(1000,5000,2), chain=np.linspace(1,5,5))
    #B.add("Model "+str(m+1), solvers=["neal"], reads=np.linspace(10,1000,25))
    #B.add("Model "+str(m+1), solvers=["neal"], reads=np.linspace(10,2000,10))
    #benchmarks.append(B)

    #B = bench(model.A,len(benchmarks))
    #B.add("Classical "+str(m+1), solvers=["neal"], reads=np.linspace(5000,20000,5))
    #benchmarks.append(B)
    
    B = bench(model.A,len(benchmarks))
    B.add("Simulated "+str(m+1), solvers=["neal"], reads=np.linspace(1000,1000,1))
    #B.add("Simulated "+str(m+1), solvers=["neal"], time=np.linspace(10,15,1))
    benchmarks.append(B)
    
    #B.logClear()
    
print( len(benchmarks), "benchmarks")

for b in benchmarks:
    b.process(verbose=True)
    
print("Completed")

