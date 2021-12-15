# Quzzi

Quzzi is a project that aims at solving certain hard schedule planning problems found in aviation using Quadratic Unconstrained Binary Optimization (QUBO). 

The original work submitted produced a proof-of-concept, using real-world data, demonstrating that it is possible to solve airline Crew Trip (and other) problems using QUBOs thus allowing for solving them on a D-Wave Quantum Computer.

## Run the demo on Leap

You can run the demo by loading the code in Leap [here](https://ide.dwavesys.io/#https://github.com/q-zee/DWave) and follow the instructions [here](https://q-zee.github.io/DWave/Quzzi/docs/usage).

## Code Documentation

The code is written in Python. Documentation start [here](https://q-zee.github.io/DWave/Quzzi/docs/).

## Origins

Quzzi started in late 2018 as an exercise to prove that the D-Wave Quantum Computer could be used to solve the Crew Trip problem, thus pioneering using Quantum Computers for real-life problems today.

In 2021, a prototype solver was deployed in the [VYouPointAero startup](https://www.vyoupoint.com) Java based cloud application MVP demonstrating its usefulness in automating its flight duty period grouping capability. But most of all, it demonstrated the worlds first quantum computing powered aviation crew planning application.


## Airline crew planning problems

The authors chose to target airline crew planning problems for a few reasons:

	- Their experience with creating and classical solvers for airlines
	- The advent of new Quantum computers dedicated to solving combinatorial problems accessible today
	- The desire to breakthrough the limitations of classical systems for solving these problems.
	- Airlines offers a wealth of some of the hardest problems to solve in transportation

## Goals

The source code is made available for collaboration by interested contributors. New components are planned to be released demonstrating solutions to problems such optimal trip assignment with compliance of minimum days off patterns and activities. 

A Contributors Guide is forthcoming.

## Current Status (December 2021)

### Open Source Published

Open source published on Q-Zee. 

### In progress

#### New CQM model
Creating a new model using the DWave CQM (Constrained Quadratic Model) to compare to the BQM. CQM allows for simpler expression of constraints, creating the quadratic equations conversions under the hood. This has the potential to reduce the number of variables (by extension, qubits) required by streamlining variable interaction formulations that implement constraints.

#### Documentation
The initial code submission has minimal documentation and is added on an ongoing basis. 

### Please Donate!
Consider donating to support this effort and be added to the mailing list to receive progress updates and other benefits

[![Github Sponsorship](https://q-zee.github.io/img/sponsorqzee2.png)](https://github.com/sponsors/Q-Zee)

