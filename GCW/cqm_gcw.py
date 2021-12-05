#
# Copyright 2021 Mario Guzzi
#
# Licensed under the Apache License, Version 2.0 (the "License"); 
# you may not use this file except in compliance with the License. 
#
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under 
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
# See the License for the specific language governing permissions and limitations under the License.
#
# -*- coding: utf-8 -*-
"""CQM-GCW.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1hrxeTN0B6_XN3zMxhDN3k89D-vAqKdVI

Copyright 2021 Mario Guzzi

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

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
 W  C       | W        F |         G  |            |
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

# Usage 

Ensure you assign your DWave API token below unless already configured on the server.
"""

token=None # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

!pip install dwave-ocean-sdk

import dimod
from dimod import BinaryQuadraticModel, Binary
from dwave.system import LeapHybridCQMSampler

#
# Goat Cabbage Wolf Problem - Solving using CQM 
#
# Model definitions
#

# We have 4 items that each can be in two states: on left bank (0) or right bank (1)
# Items are: W, G, C and F

Wolf = 0
Cabbage = 1
Goat = 2
Farmer = 3

avail_W = 4
avail_C = 5
avail_G = 6

move_W = 7
move_C = 8
move_G = 9

items = { Wolf : "W", Cabbage : "C", Goat: "G" , Farmer: "F"  }
names = { Wolf : "wolf", Cabbage : "cabbage", Goat: "goat" , Farmer: "farmer"  }

# Column labels for each trip (row)

row_labels = {
            Wolf:    "W", 
            Goat:    "G",
            Cabbage: "C",
            Farmer:  "F",
            avail_W: "aW",
            avail_G: "aG",
            avail_C: "aC",
            move_W:  "mW",
            move_G:  "mG",
            move_C:  "mC"    
}

# Conflicts when farmer not present on the same river bank

Danger = { (Wolf,Goat): 1, (Goat,Cabbage): 1 }

# States for each item

LeftBank = 0
RightBank = 1

# Create a Variable name : Item on a bank at each step

def varname( st=0, item=0):
  name = row_labels[item]+"_step_"+str(st)
  return name

MS = 10  # Maximum Steps
IT = 4   # Items
BK = 2   # Banks
L = 8    # Items on either bank

O_IT = 0           # Item_state start offset
O_AV = IT          # Availability state start offset
O_CH = IT + IT - 1 # Choices state start offset

#print(O_IT,O_AV,O_CH)

COL = len(row_labels) # Columns

board = { 
    (s,i) : dimod.Binary(varname(s,i)) for i in range(COL) for s in range(MS)}

#print(items)
#print(board)

#
# cqm preparation
#

time_limit = 5
cqm = dimod.CQM()

# 1 - Initial Condition: All items including farmer on the left bank (=0)

cqm.add_constraint( sum( board[0,i] for i in range(O_IT,IT) ) == 0, label=f"init_items" )

# 2- Farmer goes back and forth between banks at each step: 
for s1 in range(MS-1):
  s2 = s1 + 1
  cqm.add_constraint( board[s1,Farmer] + board[s2,Farmer] == 1, label=f"farmer_{s1}_to_{s2}_diff" )

# 3 - There can only be 0 or 1 choice made in the choices columns

for s1 in range(MS):
  cqm.add_constraint( sum( board[s1,c] for c in range(O_CH,O_CH+IT-1)) <= 1, label=f"choice_count_step_{s1}" )

# 4 - Assign avail_item variable: (item_state + farmer_state - 1) **2 - avail_state == 0

for s1 in range(MS):
  for i in range(IT-1):
    cqm.add_constraint(  ( board[s1,i] + board[s1,Farmer] - 1)**2 - board[s1,i+O_AV] == 0, label=f"item_{i-IT}_avail_step_{s1}" )

# 5 - Ensure that the item states change according to the chosen item to move
#
# item_state_s1 + choice_state_s1 - (2 * farmer_state_s1 * choice_state_s1) - item_state_s2 == 0 

for s1 in range(MS-1):
  s2 = s1 + 1
  for i in range(IT-1):
    cqm.add_constraint(  board[s1,i] + board[s1,i+O_CH] - ( 2 * board[s1,Farmer] * board[s1,i+O_CH]) - board[s2,i]  == 0  , label=f"move_chosen_item_{i}_{s1}_to_{s2}")

# 6 - Prevent conflicts where farmer is absent
# Note: Determining where the Farmer is absent is based on the alternating constraint #2.
# Therefore even number rows have the farmer on the left bank and odd number rows have the farmer on the right bank

for s1 in range(MS):
  for i1 in range(IT-1):
    for i2 in range( i1+1,IT-1):
      if (i1,i2) in Danger or (i2,i1) in Danger:
        if ( s1 % 2 == 1 ):
          # Left Bank
          cqm.add_constraint( 1 - board[s1,i1] + 1 - board[s1,i2]  <= 1, label=f"conflict_left_{i1}_{i2}_step_{s1}"  ) 
        else:
          # Right Bank
          cqm.add_constraint(  board[s1,i1] + board[s1,i2]  <= 1, label=f"conflict_right_{i1}_{i2}_step_{s1}"  ) 

# Objective: Move all items from the left bank. We maximize the number of items on the right bank across all steps

objective = cqm.set_objective( -sum(board[s,i] for i in range(IT-1) for s in range(MS)) )

# Call the Quantum Computer
sampler = LeapHybridCQMSampler(token=token)
raw_sampleset = sampler.sample_cqm(cqm, time_limit=time_limit,label="CQM-GWC")

# Obtain the results and determine how many feasible results we have.

feasible_sampleset = raw_sampleset.filter(lambda d: d.is_feasible)
num_feasible = len(feasible_sampleset)

print(str(num_feasible)+" Feasible samples")
if num_feasible > 0:
    best_samples = \
        feasible_sampleset.truncate(min(10, num_feasible))
else:
    print("Warning: Did not find feasible solution")
    best_samples = raw_sampleset.truncate(10)

print(" \n" + "=" * 30 + "BEST SAMPLE SET" + "=" * 30)
print(best_samples)

# Verbose description of the trips and items moved for one solution
def printSolution(solution):
  for st in range(MS):
    res = [solution[varname(st,i)] for i in range(IT)]
    if ( sum(res) == 4 ):
      print("Solved")
      break;
    
    bank = int(solution[varname(st,Farmer)])
    choice = [int(solution[varname(st,i+O_CH)]) for i in range(IT-1)]
    destination = ["right", "left"][bank]

    if ( sum(choice) == 0):
      print(["Go to other side empty","Return empty"][bank])
    else:
      i = sum(a*b for a,b in zip(choice,[0,1,2,3]))
      print( ["Bring the","Return with the"][bank],names[i],["to the other side",""][bank])

# Print the state of all solutions in the sample
def printState(samples, detailed=False, verbose=True):
  extra = 0
  if ( detailed ): extra = 2

  for i,s in enumerate(samples):
    print("Result "+str(i+1))

    if ( verbose ):
      printSolution(s)

    # Title row
    count = 0

    header = " Left bank  | Right Bank |"
    extraHeader = " Available  | Choice "

    print( '\n'+header, end='' )
    if detailed: print( extraHeader, end='')
    print('')

    for b in range(BK):
      for i in range(IT):
        label = ' ' + items[i]+' ' 
        count = count + len(label)
        print( label , end='')
      count = count + 1
      print( '|', end='')

    if ( detailed ):
      for i in range(IT,COL):
        label = ' ' + row_labels[i]+' ' 
        count = count + len(label)
        if (i == O_CH-1 ) : 
          count = count + 1
          label = label + '|'

        print( label, end='')
        
    print('\n'+"-"*(count+1))

    goalReached = False
    for st in range(MS):

      total = 0
      for b in range(BK+extra):
        for i in range(IT):
          v = 0.0
          # Item locations
          if ( b < BK ):
            if ( varname(st,i) in s ):
              v = s[varname(st,i)]
            q = ' '
            if ( int(v) == b ): 
              q = items[i]
              if ( b == 1 ): total = total+1
            print( ' '+ q + ' ', end='' )
          else:
            # Movement choice
            if ( i < IT-1):
              if ( varname(st,i+IT) in s ):
                v = s[varname(st,i+IT+(b-2)*(IT-1))]
              q = ' '
              if ( int(v) > 0.0 ): q = items[i]
              print( ' '+ q + '  ', end='' )

        print( '|', end='')
      print('')

      if ( total == IT ):
        goalReached = True
        break;

    print("=" * (count+1))
    #break

# Output the results

printState(best_samples, detailed=True)
