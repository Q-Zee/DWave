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

from enum import Enum    # for routeGroup
import itertools         # for routeGroupings
import copy              # for routeComposite

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch # for drawGroupings
import matplotlib.patches as mpatches         # for drawGroupings

import numpy as np

from quzzi.qzfsched import Node
from quzzi.qzfsched import Segment

#==============================================================================================#
# s2fsched (c) 2020 Mario Guzzi                                                         #
#                                                                                              #
# Route Groupings for manipulating and displaying route sequences                              #
#                                                                                              #
# routeGroup                                                                                   #
# routeGrouping                                                                                #
# segmentComposite                                                                             #
# routeComposite                                                                               #
# levelSegments                                                                                #
# drawGroupings                                                                                #
#                                                                                              #
#                                                                                              #
#                                                                                              #
#                                                                                              #
#==============================================================================================#    

class routeGroup(Enum):
    SEG = 1
    DUTY = 2
    TRIP = 3
    REST = 4
    POS = 5
    CREW = 6
    EQUIP = 7
    LINE = 8
    SHIFT = 9
    OFF = 10
    GRP = 11

class routeGrouping:
    id_iter = itertools.count()
    def __init__(self, items=[], grp=routeGroup.SEG, lab="",lev=1, fn=None, autocomp=True): 
        
        self.task_id = next(self.id_iter)
        self.build_composite = fn
        self.composite = None      
        self.items = []
        self.label = lab
        self.auto = autocomp
        self.grp = grp
        self.lev = lev

        # For Segments sequence, auto-create composites (since there are no children in SEG groups)
        if (( grp == routeGroup.SEG) and (self.auto)):
            self.add(items)
            self.composite = self.makeComposite(fn)
    
    def add(self,items):
        if ( not isinstance(items, list)): items = [items]
        self.items.extend(items)
        self.composite = self.makeComposite()
        return(self)
    
    # Create a composite of the items list
    def makeComposite(self,fn=None):
        if ( fn is not None ): self.build_composite = fn
        if ( self.build_composite is not None):
            self.composite = self.build_composite(self,self.items)
        return(self.composite)

    # Recursively calculate the composite of a grouping
    def getComposite(self):
        if ( self.items is not None ):
            for i in self.items:
                if ( isinstance(i,routeGrouping)):
                    i.composite = i.getComposite()
        return(self.makeComposite())
    
    def dump(self,lev=0):
        print('>'*lev,type(self),self.label,self.grp, self.composite)
        for s in self.items:
            if ( isinstance(s,routeGrouping)):
                s.dump(lev+1)
            elif (isinstance(s,Node)):
                print('*'*lev, "Node Segment Id", s.obj.task_id)
            elif (isinstance(s,Segment)):
                print('*'*lev, "Segment Id", s.task_id)
                
class segmentComposite:
    id_iter = itertools.count()
    def __init__(self,seg):
        self.seg = None
        self.dur = 0
        self.gaps = 0
        if ( seg is not None):
            if ( isinstance(seg,Segment)):
                self.seg= copy.deepcopy(seg)
                self.dur = self.seg.UT2 + self.seg.co - (self.seg.UT1 - self.seg.ci)
                self.gaps = 0
            if ( isinstance(seg,routeGrouping) ):
                if ( seg.composite is not None):
                    self.seg= copy.deepcopy(seg.composite.seg)
                    if ( self.seg is not None):
                        self.dur = self.seg.UT2 + self.seg.co - (self.seg.UT1 - self.seg.ci)
                    self.gaps = 0
        self.task_id = next(self.id_iter)

# Composites builder class
class routeComposite:
    def __init__(self):
        pass
    
    # For testing. Creates a string list of the sequence int items
    def Str(self,items):
        if ( not isinstance(items, list)): items = [items]
        s = ""
        for i in items:
            s = s+'-'+str(i)
        s = s[1:]
        return(s)
    
    # Node.Segment sequence composite
    def Seg(self,items):
        
        compseg = None
        if (len(items)>0):
            # First and Last items are used for constructing the composite
            first = items[0].obj
            last = items[-1].obj

            # Create an initial composite object using the first segment
            compseg = segmentComposite(first)

            # Create composite item using first and last
            # Flight time is the sum of the items ft
            compseg.seg.ft = sum(s.obj.ft for s in items)
            compseg.seg.task_id = first.task_id # FIXME: Used to be id, but this was wrong, revealed bug after correcting.
            compseg.seg.lab = "" #routeComposite.Str(self,items)
            compseg.seg.dep = first.dep
            compseg.seg.arr = last.arr
            compseg.seg.deptime = first.deptime
            compseg.seg.arrtime = last.arrtime
            compseg.seg.depday = first.depday
            compseg.seg.arrday = last.arrday
            compseg.seg.UT1 = first.UT1
            compseg.seg.UT2 = last.UT2
            compseg.seg.T   = 0 # N/A for composites
            compseg.seg.ci = first.ci # + postime[0]
            compseg.seg.co = last.co # + postime[1]
            # Duration is total span from first co to last ci
            compseg.dur = compseg.seg.arrtime + compseg.seg.co - (compseg.seg.deptime - compseg.seg.ci)
            compseg.gaps = 0  # TODO: Future use for encorporating work vs wait times in a composite
        return(compseg)
    
    # route Grouping group composite
    def Grp(self,items):
        compseg = None
        if(len(items)>0):
            for i in items:
                # Create the composites
                i.makeComposite()
                
            first = items[0].composite
            last = items[-1].composite

            compseg = segmentComposite(first)

            if (compseg.seg is not None):
                #compseg.seg.ft = sum(s.composite.seg.ft for s in items)
                compseg.seg.task_id = first.task_id # FIXME: Used to be id, but this was wrong, revealed bug after correcting.
                #compseg.seg.lab = "" #routeComposite.Str(self,items)
                compseg.seg.dep = first.dep
                compseg.seg.arr = last.arr
                compseg.seg.deptime = first.deptime
                compseg.seg.arrtime = last.arrtime
                compseg.seg.depday = first.depday
                compseg.seg.arrday = last.arrday
                compseg.seg.UT1 = first.UT1
                compseg.seg.UT2 = last.UT2
                compseg.seg.T   = 0 # N/A for composites
                compseg.seg.ci = first.ci # + postime[0]
                compseg.seg.co = last.co # + postime[1]
                # Duration is total span from first co to last ci
                compseg.dur = compseg.seg.arrtime + compseg.seg.co - (compseg.seg.deptime - compseg.seg.ci)
                compseg.gaps = 0  # TODO: Future use for encorporating work vs wait times in a composite
            
        return(compseg)
    
# Create non-overlapping sequences

class levelSegments:
    
    def __init__(self, items,pfx="GRP"):

        self.groupings = routeGrouping(routeGroup.GRP,pfx,lev=2)
        
        if ( isinstance(items,list)):
            self.items = items
#        elif (isinstance(grp,routeGrouping)): # TODO: Fix the grp variable: Needed ? Fix it. Not needed? remove.
#            self.items = items.items
        else:
            raise ValueError("items parameter not understood")

    
    def level(self, pfx):
        # Assign segment ids to sequences
        for i,s in enumerate(self.items):
            sq = 0
            group = self.findSlot(pfx,s.obj)
            if ( group is not None):
                group.add([s])

    def getGrpByName(self,name):
        for s in self.groupings.items:
            if ( s.label==name): return(s)
        return(None)

    def findSlot(self,pfx, targ):

        notFound = True
        seq = 0
        while( notFound ):
            p = pfx+str(seq)
            group = self.getGrpByName(p)
            if ( group is None ):
                group = routeGrouping([],lab=p, fn=routeComposite.Seg)
                self.groupings.add(group)
                return(group)
            
            # Sequence exists, lets find a fit
            conflict = False
            for s in group.items:
                if ( self.overlap(targ,s.obj)):
                    conflict = True
                    break;
            if ( not conflict ): return(group)
            seq += 1
    
    def overlap(self,a,b):
        (at1,at2) = self.gettime(a)
        (bt1,bt2) = self.gettime(b)
        # Full overlap
        if ( at1 < bt1 and at2 > bt2 ): return True
        if ( bt1 < at1 and bt2 > at2 ): return True
        # partial overlap
        if ( at1 >= bt1 and at1 < bt2): return True
        if ( at2 >= bt1 and at2 < bt2): return True
        if ( bt1 >= at1 and bt1 < at2): return True
        if ( bt2 >= at1 and bt2 < at2): return True
        return(False)
    
    def gettime(self,s):
        t1 = (s.depday-1) * 1440 + s.deptime
        t2 = t1 + s.ft
        return(t1,t2)

class drawGroupings:
    
    class BoxDisplay:
        def __init__(self):
            self.box_height = 0.8
            self.box_pad = 0.00
            self.box_voff = (1.0 - (self.box_height-(2*self.box_pad)))/2
            self.box_v1 = False
            self.box_v2 = False
            self.box_v3 = True
        
    # Create a drawing object to display the groupings provided
    # Option 1: If grps is a routeGrouping, groupings = grps.items
    # Option 2: If grps is a list, groupings = grps
    
    def __init__(self,grps,fromLev=0):
        self.groupings = [grps]
        if ( isinstance(grps,list)): self.groupings = grps
        if ( isinstance(grps,routeGrouping)): self.groupings = grps.items
        self.boxparam = self.BoxDisplay()
    
    def gettime(self,s):
        t1 = (s.depday-1) * 1440 + s.deptime
        t2 = t1 + s.ft
        return(t1,t2)
    
    def nextSEG(self,items):
        for i in items:
            if ( not isinstance(i,routeGrouping)):
                yield i
            else:
                yield from self.nextSEG(i.items)

    def draw2(self,pfx=None,grp=None,lev=0):
        
        # Given a group, select the items in the group
        # otherwise select the group given at initialization
        
        if ( grp is not None ):
            if ( isinstance(grp,list)):
                source = grp
            elif (isinstance(grp,routeGrouping)):
                source = grp.items
        else:
            source = self.groupings
        
        # If given a pfx, create a reduced list 
        items = []
        if ( pfx is not None ):
            for i in source:
                if ( i.label.find(pfx) == 0):
                    items.append(i)
        else:
            items = source
            
        print("Items list", items)

        # Construct the labels stack
        labels = [s.label for s in items]
        NRows = len(labels)
        
        #print(NRows, "rows", labels)

        # Initialize our plot
        fig, ax = plt.subplots(figsize=(18.4, NRows))
        # Save in class for other methods to access
        self.fig = fig
        self.ax = ax
        ax.invert_yaxis()
        ax.xaxis.set_visible(True)
        
        # Calculate dimensions and set x axis
        # TODO: Needs to collect the leaves of the tree: routeGroup.SEG
        
        minT = 10**10
        maxT = 0
        for s in self.nextSEG(items):
            #print("nextSEG yielded",s.obj.id)
            (t1,t2) = self.gettime(s.obj)
            maxT = max(maxT,t2)
            minT = min(minT,t1)
        #maxT = ((maxT // 1440)+1) * 1440
        maxT = ((maxT // 60)+1) * 60
        minT = ((minT // 60)) * 60
        ax.set_xlim(minT, maxT) 
        
        # Calculate and fit the x-axis tick labels
        # xticks
        div = 60
        rate = 2
        rightSized = False
        while( not rightSized ):
            ticks = np.array(range(int(maxT/div)+1))*div
            if(len(ticks)>36):
                div *= rate
                continue
            rightSized = True
            
        ticks = ticks[ticks>=minT]
                        
        xlabels = []
        for t in ticks:
            xlabels.append("{:02d}:{:02d}".format((t%1440)//60,(t%1440)%60))
        plt.xticks(ticks, xlabels)
        
        # For each items in out list (primary list)
        # set the display row and proceed to draw the 
        # grouping
        
        for row,item in enumerate(items):       
            #print("Printing", row,item)
            
            self.drawGroupItem(label=labels[row],row=row,item=item,lev=lev)
            
        # Patching - Not really doing what we want: Can't get the rounded corners working like the examples
        # Applies to all items drawn
        
        new_patches = []
        for i, patch in enumerate(reversed(ax.patches)):
            bb = patch.get_bbox()
            color=patch.get_facecolor()
            p_bbox = FancyBboxPatch((bb.xmin, bb.ymin),
                                abs(bb.width), abs(bb.height),
                                #boxstyle="round,pad=-0.0040,rounding_size=0.015",
                                #boxstyle="round,pad=-0.001, rounding_size=0.015",
                                #mpatches.BoxStyle("Round", pad=-0.001, rounding_size=0.1),
                                mpatches.BoxStyle("Round", pad=self.boxparam.box_pad),
                                #boxstyle="round, rounding_size=1.5",
                                ec="k", fc=color,
                                mutation_aspect=1
                                )
            patch.remove()
            new_patches.append(p_bbox)
        for patch in new_patches:
            ax.add_patch(patch)
        
        plt.grid(True,axis='x')
        ax.set_axisbelow(True)
                
        return fig, ax            
        
    # Draw one group: 
    # if grp is a segment, draw the segment
    # if grp is not a segment, draw its composite and recur on each item
    
    def drawGroupItem(self,label=None, item=None,row=0,lev=0):
        
        if ( label is None ): label = "Sequence " + str(row+1)
            
        #print("GroupItem Type is", type(item))

        # Option 1: item is a routeGrouping: Draw the composite and the children items
        # Option 2: item is a routeComposite: Draw the composite segment
        # Option 3: item is a Node(Segment): Draw the node segment
        
        if ( isinstance(item,routeGrouping)):
            # draw the composite
            self.drawSegmentItem(label=label,item=item.composite,row=row,lev=lev)
            # recur for each item
            for i in item.items:
                self.drawGroupItem(label=label,item=i,row=row,lev=lev)
        
        if ( isinstance(item,segmentComposite)):
            # draw the composite
            self.drawSegmentItem(label=label,item=item.seg,row=row,lev=lev)
            
        if   ( isinstance(item,Node)):
            # draw the segment at the given row
            self.drawSegmentItem(label=label,item=item.obj,row=row,lev=lev)


    # Main item draw method. 
    # TODO: Parameterize the boxstyle for each level from the class level
    
    def drawSegmentItem(self,label=None, item=None,row=0,lev=0):
        if ( label is None ): label = "Sequence " + str(row+1)
        if ( item is None ): return

        ax = self.ax
        
        #print("SegmentItem Type is", type(item))

        # Select the box style depending on the item type
        # given. TODO: Use a paramater stack to make selection

        i = row

        box_v1 = self.boxparam.box_v1
        box_v2 = self.boxparam.box_v2
        box_v3 = self.boxparam.box_v3
        box_height = self.boxparam.box_height
        box_pad = self.boxparam.box_pad
        box_voff = self.boxparam.box_voff
        
        # get the segment object
        s = item
        if ( isinstance(item, segmentComposite)):
            s = item.seg
            #
            #  TODO: Implement boxstyles. For now we skip drawing anything else than segments
            #
            return
            #
            
            
            
        if ( isinstance(item, Node)):
            s = item.obj
        
        if ( s is None ): return

        # Get segment details
        (t1,t2) = self.gettime(s)
        width = t2 - t1 + 1
        height = box_height - (box_pad * 2)
        left = t1

        # TODO: This should be done once in the main draw loop (?) seems row label is repeated for each box drawn
        ax.barh(label, width, height=height, left=left,color='lightseagreen')

        
        text_color = 'black'
        if ( box_v1 ):
            text = s.dep +" "+s.lab+" "+s.arr
            x = left + width / 2
            ax.text(x, i, text, ha='center', va='center',color=text_color)
        if (box_v2):
            text1 = s.lab
            ax.text(left, i, text1, ha='left', va='bottom',color=text_color)
            text2 = s.dep
            ax.text(left, i, text2, ha='left', va='top',color=text_color)
            text3 = s.arr
            ax.text(left+width, i, text3, ha='right', va='top',color=text_color)
        if (box_v3):
            x = left + width / 2
            text1 = s.lab
            ax.text(x, i-box_voff*2+0.04, text1, ha='center', va='bottom',color=text_color)
            text2 = s.dep
            ax.text(x, i, text2, ha='center', va='top',color=text_color)
            text3 = s.arr
            ax.text(x, i+box_voff*2, text3, ha='center', va='top',color=text_color)
     

    def buildComposites(self,items=None):
        if ( items is None ): items = self.groupings
        if ( not isinstance(items,list)): items = [items]
        for i in items:
            i.getComposite()
    
    # TODO: Upgrade to handle multi level routeGroupings 
    
    def draw(self,pfx=None):
    
        
        if ( pfx is None ):
            sequences = self.groupings.items
        else:
            sequences = []
            for g in self.groupings.items:
                if ( g.label.find(pfx) == 0):
                    sequences.append(g)
        
        #labels = list(sequences.keys())
        labels = [s.label for s in self.groupings.items]
        NTrips = len(labels)

        fig, ax = plt.subplots(figsize=(18.4, NTrips))
        ax.invert_yaxis()
        ax.xaxis.set_visible(True)
        
        minT = 10**10
        maxT = 0
        for c in self.groupings.items:
            for s in c.items:
                (t1,t2) = self.gettime(s.obj)
                maxT = max(maxT,t2)
                minT = min(minT,t1)
        #maxT = ((maxT // 1440)+1) * 1440
        maxT = ((maxT // 60)+1) * 60
        minT = ((minT // 60)) * 60
        
        ax.set_xlim(minT, maxT) #np.sum(data, axis=1).max()) 

        # xticks
        div = 60
        rate = 2
        rightSized = False
        while( not rightSized ):
            ticks = np.array(range(int(maxT/div)+1))*div
            if(len(ticks)>36):
                div *= rate
                continue
            rightSized = True
            
        ticks = ticks[ticks>=minT]
                        
        xlabels = []
        for t in ticks:
            xlabels.append("{:02d}:{:02d}".format((t%1440)//60,(t%1440)%60))
        plt.xticks(ticks, xlabels)
        

        box_height = 0.8
        box_pad = 0.00
        box_voff = (1.0 - (box_height-(2*box_pad)))/2

        box_v1 = False
        box_v2 = False
        box_v3 = True
        
        for i, r in enumerate(sequences):
            #i = ii-1
            label = r.label
            for s in r.items:
                # Get segment details
                (t1,t2) = self.gettime(s.obj)
                width = t2 - t1 + 1
                height = box_height - (box_pad * 2)
                left = t1
                ax.barh(label, width, height=height, left=left,color='lightseagreen')
                #print( i,s.obj.id,t1,t2 )
                #ax.barh(label, width, left=left, height=0.5,color='lightseagreen')
                text_color = 'black'
                if ( box_v1 ):
                    text = s.obj.dep +" "+s.obj.lab+" "+s.obj.arr
                    x = left + width / 2
                    ax.text(x, i, text, ha='center', va='center',color=text_color)
                if (box_v2):
                    text1 = s.obj.lab
                    ax.text(left, i, text1, ha='left', va='bottom',color=text_color)
                    text2 = s.obj.dep
                    ax.text(left, i, text2, ha='left', va='top',color=text_color)
                    text3 = s.obj.arr
                    ax.text(left+width, i, text3, ha='right', va='top',color=text_color)
                if (box_v3):
                    x = left + width / 2
                    text1 = s.obj.lab
                    ax.text(x, i-box_voff*2+0.04, text1, ha='center', va='bottom',color=text_color)
                    text2 = s.obj.dep
                    ax.text(x, i, text2, ha='center', va='top',color=text_color)
                    text3 = s.obj.arr
                    ax.text(x, i+box_voff*2, text3, ha='center', va='top',color=text_color)


        # Patching - Not really doing what we want: Can't get the rounded corners working like the examples
        new_patches = []
        for i, patch in enumerate(reversed(ax.patches)):
            bb = patch.get_bbox()
            color=patch.get_facecolor()
            p_bbox = FancyBboxPatch((bb.xmin, bb.ymin),
                                abs(bb.width), abs(bb.height),
                                #boxstyle="round,pad=-0.0040,rounding_size=0.015",
                                #boxstyle="round,pad=-0.001, rounding_size=0.015",
                                #mpatches.BoxStyle("Round", pad=-0.001, rounding_size=0.1),
                                mpatches.BoxStyle("Round", pad=box_pad),
                                #boxstyle="round, rounding_size=1.5",
                                ec="k", fc=color,
                                mutation_aspect=1
                                )
            patch.remove()
            new_patches.append(p_bbox)
        for patch in new_patches:
            ax.add_patch(patch)
                
        plt.grid(True,axis='x')
        ax.set_axisbelow(True)
                
        return fig, ax
        
