# Crew Trip Solver Example - Brief Usage

## Demo solver 

### Default settings - Simulated Annealing

Under Quzzi/src you will find test_solver.py. The default configuration is to use Simulated Annealing. 

Run as:

```
  python test_solver.py
```

### Run using Quantum Annealing

Open test_solver.py and go to the end of the file to find the Benchmark loop.
Comment out the Simulated Annealing call and uncomment the Quantum Hybrid call as so:

```python
benchmarks = []
for m, model in enumerate(models):

    B = bench(model.A,len(benchmarks))

    # Default uses Simulated Annealing 

    #B.add("Simulated-BQM "+str(m+1), solvers=["neal"], reads=np.linspace(1000,1000,1))

    # To use the Hybrid Quantum Solver, uncomment the line below.
    # Note that the benchmark tool in this loop retains the best solution for any
    # solvers used. Therefore, to ensure getting details of the Hybrid solvers regardless
    # of the outcome, comment or remove other solvers from the benchmark
    
    B.add("Quantum-BQM "+str(m+1), solvers=["hyb"], time=np.linspace(10,10,1))
    
    benchmarks.append(B)
    
    #B.logClear()
```

Save the file and run as previously shown.

### Default use case - 24 Flight segments to sequence

The default use case (datasets/DS2b.csv) contains 24 flight segments per day. 

Each row is a flight segment requiring a flight crew. 

The problem is to sequence all flight segments into legal trips. 

A trip must start at the crew home base (LCA) and finish with a segment that returns home. Transiting through the home base is allowed in this example.

|row | fid | Flt | Dep | Arr | dDay | dTime | aTime | aDay | FT | GT |
|----|-----|-----|-----|-----|------|-------|-------|------|----|----|
| 0  | 001 | 210 | LCA |CWL |d01 |0325 |0835 |d01 |ft 0510 |gt 0000 |
| 1  | 002 | 102 | LCA |ATH |d01 |0405 |0550 |d01 |ft 0145 |gt 0000 |
| 2  | 003 | 602 | LCA |BEY |d01 |0410 |0455 |d01 |ft 0045 |gt 0000 |
| 3  | 004 | 603 | BEY |LCA |d01 |0540 |0630 |d01 |ft 0050 |gt 0000 |
| 4  | 005 | 103 | ATH |LCA |d01 |0635 |0810 |d01 |ft 0135 |gt 0000 |
| 5  | 006 | 122 | LCA |CHQ |d01 |0725 |0905 |d01 |ft 0140 |gt 0000 |
| 6  | 007 | 302 | LCA |CDG |d01 |0730 |1200 |d01 |ft 0430 |gt 0000 |
| 7  | 008 | 104 | LCA |ATH |d01 |0740 |0925 |d01 |ft 0145 |gt 0000 |
| 8  | 009 | 112 | LCA |SKG |d01 |0910 |1110 |d01 |ft 0200 |gt 0000 |
| 9  | 010 | 211 | CWL |LCA |d01 |0935 |1430 |d01 |ft 0455 |gt 0000 |
| 10 | 011 | 123 | CHQ |LCA |d01 |0950 |1125 |d01 |ft 0135 |gt 0000 |
| 11 | 012 | 105 | ATH |LCA |d01 |1010 |1145 |d01 |ft 0135 |gt 0000 |
| 12 | 013 | 113 | SKG |LCA |d01 |1155 |1350 |d01 |ft 0155 |gt 0000 |
| 13 | 014 | 206 | LCA |BHX |d01 |1220 |1705 |d01 |ft 0445 |gt 0000 |
| 14 | 015 | 106 | LCA |ATH |d01 |1245 |1430 |d01 |ft 0145 |gt 0000 |
| 15 | 016 | 303 | CDG |LCA |d01 |1300 |1700 |d01 |ft 0400 |gt 0000 |
| 16 | 017 | 202 | LCA |STN |d01 |1450 |1935 |d01 |ft 0445 |gt 0000 |
| 17 | 018 | 107 | ATH |LCA |d01 |1515 |1650 |d01 |ft 0135 |gt 0000 |
| 18 | 019 | 108 | LCA |ATH |d01 |1520 |1705 |d01 |ft 0145 |gt 0000 |
| 19 | 020 | 109 | ATH |LCA |d01 |1750 |1925 |d01 |ft 0135 |gt 0000 |
| 20 | 021 | 207 | BHX |LCA |d01 |1805 |2220 |d01 |ft 0415 |gt 0000 |
| 21 | 022 | 604 | LCA |BEY |d01 |1925 |2010 |d01 |ft 0045 |gt 0000 |
| 22 | 023 | 203 | STN |LCA |d01 |2035 |0050 |d02 |ft 0415 |gt 0000 |
| 23 | 024 | 605 | BEY |LCA |d01 |2055 |2145 |d01 |ft 0050 |gt 0000 |

### Output - Trip sequences

Segments will be sequenced into "trips", each originating and terminating at the crew base (LCA in this use case). 

The output will look like this:

```
Allocated 3746 qubo variables 0 to 575
          24 start flags 576 to 599
          3146 additional variables 600 to 3745
1 models
1 benchmarks
Solving Profile: Quantum-BQM 1    Solver: hyb      Time: 10.0 -- Reads: 100 -- Chain: 1
Solving using the LeapHybridSolver...(time limit is 10.0 )
Energy : -480006.99227539264
Trip
0 007 302  LCA CDG d01 0730 1200 d01 ft 0430 gt 0000 0.0
1 016 303  CDG LCA d01 1300 1700 d01 ft 0400 gt 0100 0.0
Trip
2 002 102  LCA ATH d01 0405 0550 d01 ft 0145 gt (1255) 0.0
3 005 103  ATH LCA d01 0635 0810 d01 ft 0135 gt 0045 0.0
4 009 112  LCA SKG d01 0910 1110 d01 ft 0200 gt 0100 0.0
5 013 113  SKG LCA d01 1155 1350 d01 ft 0155 gt 0045 0.0
6 017 202  LCA STN d01 1450 1935 d01 ft 0445 gt 0100 0.0
7 023 203  STN LCA d01 2035 0050 d02 ft 0415 gt 0100 0.0
Trip
8 001 210  LCA CWL d01 0325 0835 d01 ft 0510 gt (2125) 0.0
9 010 211  CWL LCA d01 0935 1430 d01 ft 0455 gt 0100 0.0
10 019 108  LCA ATH d01 1520 1705 d01 ft 0145 gt 0050 0.0
11 020 109  ATH LCA d01 1750 1925 d01 ft 0135 gt 0045 0.0
Trip
12 003 602  LCA BEY d01 0410 0455 d01 ft 0045 gt (1515) 0.0
13 004 603  BEY LCA d01 0540 0630 d01 ft 0050 gt 0045 0.0
Trip
14 015 106  LCA ATH d01 1245 1430 d01 ft 0145 gt 0615 0.0
15 018 107  ATH LCA d01 1515 1650 d01 ft 0135 gt 0045 0.0
Trip
16 006 122  LCA CHQ d01 0725 0905 d01 ft 0140 gt (0925) 0.0
17 011 123  CHQ LCA d01 0950 1125 d01 ft 0135 gt 0045 0.0
18 014 206  LCA BHX d01 1220 1705 d01 ft 0445 gt 0055 0.0
19 021 207  BHX LCA d01 1805 2220 d01 ft 0415 gt 0100 0.0
Trip
20 008 104  LCA ATH d01 0740 0925 d01 ft 0145 gt (1440) 0.0
21 012 105  ATH LCA d01 1010 1145 d01 ft 0135 gt 0045 0.0
Trip
22 022 604  LCA BEY d01 1925 2010 d01 ft 0045 gt 0740 0.0
23 024 605  BEY LCA d01 2055 2145 d01 ft 0050 gt 0045 0.0
----------------------------------
```

### Objective - Minimize non-flight time spent by crew members

The objective (above and beyond basic constraint compliance for the structure of trips) is to minimize the crew duty time spent that is not directly for performing a flight. In other words 

```
Minimize Sum (Duty Time minus Flight Time) for all trips.
```

More precisely: 
  Report time of 60 minutes and Release time of 30 minutes for each trip
  Connection time (ground time) between flight segments within each trip

The number of resulting trips is not set ahead of time. 

Note that flight time limitations per trip are not applied in this model.

