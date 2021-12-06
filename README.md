# Solvers using the DWave Quantum Annealing Computer

## Example 1 - Solving the Goat-Cabbage-Wolf problem using CQM

This is a nice little problem for the Quantum Annealer to solve using CQM.

It demonstrates how one can solve a problem by expressing the valid possible moves without giving any hints as to how to actually solver the problem.

There are two version files:
1) Jupyter Notebook. Ensure that you setup your API token where indicated before executing.
2) Python file you can run on DWave leap directly using : https://ide.dwavesys.io/#https://github.com/q-zee/DWave under the GCW folder.

## Example 2 - Solving the 8 Queens problem

Here are two versions of a solver to the 8 Queens problem using DWave. 

The [first](https://github.com/Q-Zee/DWave/blob/main/8Queens/8Queens.py) uses QUBO and I wrote this solution in 2020 during CDL Toronto Quantum Stream 

The [second](https://github.com/Q-Zee/DWave/blob/main/8Queens/8queens_cqm.py), uses the newly released CQM solver and certainly made the implementation easier over the QUBO method.

## Example 3 - Solving Airline Crew Trip problems

The airline crew trip problem is a recurring crew planning process (usually each month or 28 day period) most scheduled airline must solve to create Fatigue Management Regulation and Policy compliant flight duty periods for pilots and flight attendants.


