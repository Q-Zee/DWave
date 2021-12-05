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

import csv

from quzzi.qznodes import Node, Segment
from quzzi.groupings import routeGroup, routeGrouping, routeComposite

#from quzzi.groupings import routeGroup
#from quzzi.groupings import routeGrouping
#from quzzi.groupings import routeComposite

class schedData:
    
    def __init__(self,dataSet=None, Atypes=[], depDay=None, HomeBases=[]):
        self.N = 0
        self.segments = []
        if (dataSet is not None):
            self.load(dataSet, Atypes=Atypes, depDay=depDay, HomeBases=HomeBases)
        
    def load(self,dataSet, Atypes=[], depDay=None, HomeBases=[]):
        self.segments = self.loadFlts(dataSet, Atypes, depDay, HomeBases)
        self.segments.sort(key=lambda x: (x.obj.depday*1440)+x.obj.deptime) # Sort by departure date/time
        for i,seg in enumerate(self.segments): # Reindex to match the sort
            seg.obj.task_id = i+1
            seg.task_id = i+1
        self.N =len(self.segments)
        return( self.N )
    
    def set(self,flightSegments):
        self.segments = flightSegments
        self.N = len(self.segments)

    # ================================================================
    # TODO: Take the below method and implement in new model
    # ================================================================
    # Return to base : penalizing on start and depenalizing on return
    # 
    # const_location_start : Will add the base weight of the airport
    # const_location_return: Will subtract base weight of the airport
    # 
    # a Net Zero means we have a cycle returning to the start airport
    #
    # ================================================================

    # Utility functions for formatting flight segments and time
    # TODO: Implement with are standard rigor regarding date and time handling
    
    # Hours and minutes from a number of minutes in a day (0-1439)
    def formatHHMM(self,m):
        if ( m < 0 ): return('({:s})'.format(self.formatHHMM(-m)))
        return ("{:02d}{:02d}".format(int((m%1440)/60),(m%1440)%60))
    
    def formatSegment(self,seg,gap):
        # Id  FNum Dep Arr dd DepT ArrT d2 FTim Grnd
        # 001 0000 AAA BBB dd HHMM-HHMM d2 HHMM HHMM
        task_id = seg.obj.task_id
        fnum = seg.obj.lab
        dep = seg.obj.dep
        arr = seg.obj.arr
        ddy = seg.obj.depday
        depT = self.formatHHMM(seg.obj.deptime)
        arrT = self.formatHHMM(seg.obj.arrtime)
        ft = self.formatHHMM((seg.obj.arrtime+1440*seg.obj.arrday) - (seg.obj.deptime+1440*seg.obj.depday))
        ady = seg.obj.arrday
        gnd = self.formatHHMM(gap)
        
        output = "{:03d} {:4s} {:3s} {:3s} d{:02d} {:4s} {:4s} d{:02d} ft {:4s} gt {:4s}".format(task_id,fnum,dep,arr,ddy,depT,arrT,ady,ft,gnd)
        return(output)
     
    def print_trip(self,result, implicit=True, QT=None):
        variables = result[0]
        ids = []
        energy = result[1]
        N = self.N
        segments = self.segments
        
        print("Energy :", (energy))
        sndx = N*N
        prev_node = None
        leg_count = 0
        for row in range(N):
            origin = row * N
            state = 0
            #ancil = 0
            implicit_break = False
        
            if ( sndx+row < len(variables)):
                state = variables[sndx+row]
                stateStr = ["","Trip"][int(state)]

            for node in range(N):
                n = origin + node

                if ( variables[n] == 1):
                    
                    ids.extend([n])
                    
                    if ( state == 1):
                        ids.extend([sndx+row])
                        print(stateStr)
                        #leg_count = 0      DURING TESTING WE WANT TO SEE ALL THE GAP VALUES
                        #prev_node = None
                    leg_count += 1
                    leg_gap = 0

                    if ( leg_count > 1 ):
                        t1 = segments[prev_node].obj.deptime + (1440*segments[prev_node].obj.depday) + segments[prev_node].obj.ft
                        t2 = segments[node].obj.deptime + (1440*segments[node].obj.depday)
                        leg_gap = t2 - t1
                        a1 = segments[prev_node].obj.arr;
                        a2 = segments[node].obj.dep;
                        #
                        # Detect implicit break (NOTE: This is to assist with tuning the QUBO)
                        if ( implicit ):
                            if ( state != 1 ):
                                if ( a1 != a2 ): implicit_break = True
                                if ( leg_gap < 0 ): implicit_break = True
                                #if ( leg_gap > 4*60 ): implicit_break = True
                                if ( implicit_break ):
                                    print("Break")
                    #print(row, segments[node].obj.id, segments[node].obj.lab, segments[node].obj.dep, segments[node].obj.arr, leg_gap)

                    # Calculate the energy contribution for a segment
                    # TODO: Unable to properly use sumQSelect here. Look for other code from Notebooks
                    ESegment = 0.0
                    if ( QT is not None ):
                        ESegment = QT.sumQselect(QT.finalQubo(),list([n]))

                    print(row, self.formatSegment(segments[node],leg_gap),ESegment)
                    prev_node = node
        print("----------------------------------")
        print("Variables: ", sorted(ids))            

    # print(len(sampleset._record), sampleset._record[0])

    def print_all(self, sampleset, max_v = 3, QT=None):
        for res in sampleset.data():
            #self.print_trip(res,QT=QT)  
            self.print_trip(res)
            max_v = max_v - 1
            if ( max_v <= 0 ): break

    def get_sequences(self,A,result):
        # Imply sequence breaks when not marked as a Trip start, but is not continuous
        implicit = True
        
        # Build a dictionary of sequences
        sequences = {}
        
        # Get the variables from the solver result
        variables = result[0]
        
        # Get the segments 
        segments = A.segments
        
        # Get variables geometry          
        N = A.N
        sndx = N*N
        
        prev_node = None
        leg_count = 0
        seq_count = 0
        
        # Initialize the working sequence
        sequence = []
        
        # Row by row correlate variables to segment ids
        # and detect sequence starts
        for row in range(N):
            origin = row * N
            state = 0
            #ancil = 0
            implicit_break = False
        
            if ( sndx+row < len(variables)):
                state = variables[sndx+row]
        
            for node in range(N):
                n = origin + node
        
                if ( variables[n] == 1):
                    
                    #if ( state == 1):
                    #    ids.extend([sndx+row])
        
                    leg_count += 1
                    leg_gap = 0
        
                    if ( leg_count > 1 ):
                        t1 = segments[prev_node].obj.deptime + (1440*segments[prev_node].obj.depday) + segments[prev_node].obj.ft
                        t2 = segments[node].obj.deptime + (1440*segments[node].obj.depday)
                        leg_gap = t2 - t1
                        a1 = segments[prev_node].obj.arr;
                        a2 = segments[node].obj.dep;
                        #
                        # Detect implicit break 
                        if ( implicit ):
                            if ( state != 1 ):
                                if ( a1 != a2 ): implicit_break = True
                                if ( leg_gap < 0 ): implicit_break = True
        
                    # Is this segment starting a new sequence?
                    # - Is it the very first segment? 
                    # - Do we have a Start flag?
                    # - Do we have an implicit break?
                    # If so, put the current sequence (if not empty) into the result and start a new sequence
        
                    if ( leg_count > 1):
                        if ( state == 1 or implicit_break ):
                            sequences[seq_count] = sequence;
                            sequence=[]
                            seq_count += 1
        
                    # Add to the current sequence
                    sequence.append(segments[node].obj.task_id)
        
                    prev_node = node
        
        # Save the last sequence in progress
        if ( len(sequence)>0):
            sequences[seq_count] = sequence;
            sequence=[]
            seq_count += 1          
        
        return sequences
    
    def print_sequences(self,sampleset, max_v=3,solver="unknown"):
        print("{",end='') # Object
        print("\"solutions\":[",end='')     # single array for all solutions
        for tid,res in enumerate(sampleset.data()):
            seqs = self.get_sequences(self, res)
            print("{",end='') # Object
            print("\"solution\":", id, ",", sep='', end='')
            print("\"energy\":", res[1], ",", sep='', end='')
            print("\"solver\":", "\"", solver, "\"", ",", sep='', end='')
            print("\"sequence\": {",end='')
            
            
            for i,k in enumerate(seqs):
                if ( i>0): print(",",end='')
                print("\"",i,"\":[",sep='', end='') # grouping array start
                
                for j,v in enumerate(seqs[k]):
                    if ( j>0): print(",",end='')
                    print(v, sep='', end='')  # Values comma separated
                    
                print("]",end='') # Close the array
                
            print("}", end='') # end of sequence 
            print("}]",end='') # End of solutions array
            max_v = max_v - 1
            if ( max_v <= 0 ): break
        print("}") # end of single json object
        
    #==================================================================#
    # Segment listing
    #==================================================================#

    def list_segments(self):
        for i,seg in enumerate(self.segments):
            print(i, self.formatSegment(seg,0))
    
    #==================================================================#
    # Flight segment data set loader. Move into the flightsData module #
    #==================================================================#

    # Load flight data files                
    def loadFlts(self,targetDataSet, Atypes=[], depDay=None, HomeBases=[]):
        fseg = []
        firstRow=True
        flt_id = 0
        with open(targetDataSet, newline='') as csvfile:
            fltreader = csv.reader(csvfile, delimiter=',')
            for row in fltreader:
                if ( firstRow ):
                    firstRow = False
                else:
                    #  0    1    2    3      4      5      6      7      8      9      10     11    12    13    14
                    # FID, FN, FDep, FArr, FDepD, FDepT, FArrT, FArrD, UDepD, UDepT, UArrT, UArrD, FFT, FTZD, Atype
                    atype = row[14]
                    if ((len(Atypes)==0) or (atype in Atypes)):
                        if ((depDay is None) or (int(row[8]) in depDay)):
                            flt_id += 1
                            fseg.append(Node(Segment(flt_id, row[1], row[2], row[3], int(row[9]), int(row[10]), int(row[8]), int(row[11]),HomeBases)))
                    #print(', '.join(row))
        return(fseg)

    # =====================================================================
    # Get a generated sequence and save in a "sequences" object
    # =====================================================================
    
    def getRoutes(self,result):
        #routes = routeSequences(self)
        #self, items=[], grp=routeGroup.SEG, lab="",lev=1, fn=None, autocomp=True): 
        
        routes = routeGrouping(grp=routeGroup.GRP, lab="Trips",lev=4)
        lab = "unassigned"
        #routes.addRes(lab)
        tripRoute = routeGrouping(grp=routeGroup.TRIP, lab=lab,lev=3)
        routes.add(tripRoute)
        FDPRoute = routeGrouping(grp=routeGroup.DUTY, lab=lab,lev=2)
        tripRoute.add(FDPRoute)
        
        trip = 1
        
        variables = result[0]
        ids = []
        energy = result[1]
        N = self.N
        segments = self.segments
        
        sndx = N*N
        prev_node = None
        leg_count = 0
        for row in range(N):
            origin = row * N
            state = 0
            #ancil = 0
        
            if ( sndx+row < len(variables)):
                state = variables[sndx+row]
                stateStr = ["","Trip"][int(state)]
                if ( state ):
                    lab = stateStr+str(trip)
                    #routes.addRes(lab)
                    tripRoute = routeGrouping(grp=routeGroup.TRIP, lab=lab,lev=3,fn=routeComposite.Grp)
                    routes.add(tripRoute)
                    FDPRoute = routeGrouping(grp=routeGroup.DUTY, lab=lab+'FDP1',lev=2,fn=routeComposite.Seg)
                    tripRoute.add(FDPRoute)
                    trip += 1

            for node in range(N):
                n = origin + node

                if ( variables[n] == 1):
                    FDPRoute.add([segments[node]])
                    #FDPRoute.add(routeGrouping(grp=segments[node], lab=segments[node].lab,fn=routeComposite.Seg))
                    #routes.addSeq([node],lab)
        return(routes)
