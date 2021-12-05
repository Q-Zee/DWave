# 🐺 🐐 🥗

# Solving the Wolf, Goat and Cabbage riddle with DWave CQM Hybrid Quantum Solver
#### by Mario Guzzi - QuzziCode@gmail.com

## The Riddle [from Wikipedia](https://en.wikipedia.org/wiki/Wolf,_goat_and_cabbage_problem)

Once upon a time a farmer went to a market and purchased a wolf, a goat, and a cabbage. On his way home, the farmer came to the bank of a river and rented a boat. But crossing the river by boat, the farmer could carry only himself and a single one of his purchases: the wolf, the goat, or the cabbage.

If left unattended together, the wolf would eat the goat, or the goat would eat the cabbage.

The farmer's challenge was to carry himself and his purchases to the far bank of the river, leaving each purchase intact. How did he do it? 

## Solving with the Quantum Computer

We want to let the Quantum Computer figure out how to solve this puzzle without giving any hints in our coding as to how to solve it: Just provide a construct describing the possible moves the farmer can physically make, the dangers (undesirable) situations to avoid and a way to know that the problem is solved efficiently (objective).

## Method: We use DWave Constraint Quadratic Model Hybrid (CQM) Quantum Annealer

### Variables

We are using CQM to solve this problem. We define 4 binary variables representing each object and the river bank they are on:

>Wolf, Goat, Cabbage and the Farmer

>0 = Left bank, 1 = Right bank

As well each of these variables are assigned a step (boat trip). This forms a grid of 4 variables in N steps.

Furthermore we add 2 sets of binary variables, each indicating the "available" items to move to the opposite bank and the "choice" made out of these available items. 

### Visualization

The table below details the model. Each row represents a current state and a trip decision: Which of the cargo items can be moved and which one has been selected for the trip.

F is the farmer and while the farmer is on a bank the cargo is safe. Where the farmer is absent, the cargo needs to be safe from the dangers.

The first row in the table below shows that the Goat was selected to be moved from the left bank to the right bank (row 2) leaving the wolf and cabbage behind (a valid condition).

The last row shows the final goal everyone is on the other side.

```
----------------------------------------------------
 Left bank  | Right Bank | Available  | Choice     | 
----------------------------------------------------
 W  C  G  F |            | W   C   G  |         G  | 
 W  C       |       G  F |         G  |            |
    ...            ...        ...          ...
            | W  C  G  F | W   C   G  |            |
====================================================
```

Example of a valid outcome: 

```
----------------------------------------------------
 Left bank  | Right Bank | Available  | Choice     | 
----------------------------------------------------
 W  C  G  F |            | W   C   G  |         G  |
 W  C       |       G  F |         G  |            |
 W  C     F |       G    | W   C      | W          |
    C       | W     G  F | W       G  |         G  |
    C  G  F | W          |     C   G  |     C      |
       G    | W  C     F | W   C      |            |
       G  F | W  C       |         G  |         G  |
            | W  C  G  F | W   C   G  |         G  |
====================================================
```

### Constraints

The constraints describe the physical rules to follow.

```
1) The initial step is set to all 4 items on bank 0.
2) The farmer alternates between each bank each trip
3) Available items are those on the bank where the Farmer is located
4) A choice must have 0 or 1 items matching the available items
Note: The farmer is allowed to travel with no cargo.
5) The state of each consecutive rows must transition respecting the choice item to move: Source bank item removed, Destination bank item added
6) Do not leave the Goat and the Wolf or, the Goat and the Cabbage unattended (bank where the farmer is absent)
```

### Objective function

The objective incentivises the solver to get to the goal in the least steps possible. Without it, the farmer could take infinite trips, with or without items, all the while respecting the conflict rules.

**This is an important point about the model**: The constraints describe the physical _possibilities_ to choose from _without_ any indicator as to _how_ to solve the puzzle.  

It demonstrates the power of quantum annealing's ability to find solutions to problems without any algorithmic logic on how to solve it.

So the objective simply to have the least number of items on the left bank as possible over all the steps.



