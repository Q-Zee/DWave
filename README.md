# Solvers using the DWave Quantum Annealing Computer

## Introduction

Here you will find a prototype solver for the airline Crew Trip problem and other demonstration solvers. Before diving into the more complex solver for aviation, consider examples 2 and 3 below solving small toy problems and which gives a perspective on the Quantum Annealing approach to solving optimization problems. 

You can load the code directly in your DWave Leap account [here](https://ide.dwavesys.io/#https://github.com/q-zee/DWave)
If running the code on your python unstallation, some of the examples require you to set the API token in the notebook or python code. 

## Example 1 - ✈ Solving Airline Crew Trip problem ✈

The airline crew trip problem is a recurring crew planning process (usually each month or 28 day period) most scheduled airline must solve to create Fatigue Management Regulation and Policy compliant flight duty periods for pilots and flight attendants.

The [prototype](https://q-zee.github.io/DWave/Quzzi/) proposes a QUBO solver using a Binary Quadratic Model (BQM). 

With the release of the new DWave Constrained Quadratic Model (CQM) solver in October 2021, there is an intent to write a new version as a CQM model. As other examples below demonstrate, implementing constraints using CQM has shown to be far easier than with BQM.

## Example 2 - 🐺 🐐 🥗 Solving the Wolf-Goat-Cabbage riddle using CQM

This is a nice little problem for the Quantum Annealer to solve using CQM.

It demonstrates how one can solve a problem by expressing the valid possible moves without giving any hints as to how to actually solver the problem.

There are two version files:
1) Jupyter Notebook. Ensure that you setup your API token where indicated before executing.
2) Python file you can run under the GCW folder.

## Example 3 - ♟ Solving the 8 Queens problem ♟

Here are two versions of a solver to the 8 Queens problem using DWave. 

The [first](https://github.com/Q-Zee/DWave/blob/main/8Queens/8Queens.py) uses QUBO and I wrote this solution in 2020 during CDL Toronto Quantum Stream 

The [second](https://github.com/Q-Zee/DWave/blob/main/8Queens/8queens_cqm.py), uses the newly released CQM solver and certainly made the implementation easier over the QUBO method.

