# DWave Quantum Annealer Experimentations

Initially created during CDL Toronto Quantum Stream 2020 as a private repo, it is being made public for sharing experimentation work on the DWave Quantum Computer.

# Example code : Comparing BQM and CQM

## 8 Queens QUBO solver

Original working prototype solving the 8 Queens problem as a QUBO. The challenge to create any solver as a QUBO is to create and solve the Quadratic equations for implementing the constraints of some problems.

## 8 Queens CQM solver

This version of the solver uses the LeapHybridCQM solver. CQM allows expressing constraints directly as mathematical expression, without requiring to create and solve quadratic equations. All the heavy lifting is done under the hood. 

The CQM version of the solver is also superior to the BQM version in that the equations created originally were somehow only solving the 8 queens original problem but failed at solving a arbitrary NxN version. This was due to errors in the quadratic equations implementation by the author. The CQM based solver does not have this shortcoming and can solve boards of arbitratry size (always as a square board) for any number of queens.





