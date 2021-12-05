# Quzzi

Quzzi is a project that aims at solving certain hard schedule planning problems found in aviation using Quadratic Unconstrained Binary Optimization (QUBO). 

The original work submitted produced a proof-of-concept, using real-world data, demonstrating that it is possible to solve airline Crew Trip (and other) problems using QUBOs thus allowing for solving them on a D-Wave Quantum Computer.

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

## Current Status (October 2021)

The initial code submission has minimal documentation. 
Documentation is added on an ongoing basis.

## Where to start (Work in progress)

	Problem Description (TBD)
	Constraints and Objectives (TBD)
	Quadratic formulations (TBD)
	Trip solver implementation (TBD)
	Code Reference (TBD)
