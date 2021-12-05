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


'''
    Flight network classes
'''

class Node:

    def isStart(self):
        return isinstance(self.obj,Start)
    
    def isSegment(self):
        return isinstance(self.obj,Segment)
    
    def isDayItem(self):
        return isinstance(self.obj,DayItem)
    
    def __init__(self, obj ):
        if ( isinstance(obj,Segment)):
            self.task_id = obj.task_id
            self.lab = obj.lab
            self.obj = obj
        elif ( isinstance(obj,Start)):
            self.task_id = obj.task_id
            self.lab = obj.lab
            self.obj = obj
        elif ( isinstance(obj,DayItem)):
            self.task_id = obj.task_id
            self.lab = obj.lab
            self.obj = obj
        else:
            raise Exception("Error on type. Got %s" % (type(obj)))

'''
    Trip Start 
'''
                   
class Start:

    def __init__(self, task_id, lab):
        self.task_id = task_id
        self.lab = lab

'''
    Flight Segment 
'''
        
class Segment:

    def getUarrtime(self):
        return ((self.getUdeptime() + self.ft))
                
    def getUdeptime(self):
        return ((self.depday - 1) * 1440 + self.deptime)
    
    def setT(self, T):
        self.T = T
        self.UT1 = self.getUdeptime()
        self.UT2 = T - ( self.getUdeptime() + self.ft)
        
    def getUT(self):
        return( self.T - self.ft)

    def getUT1(self):
        return( self.UT1)

    def getUT2(self):
        return( self.UT2)
    
    def setCI(self,ci):
        self.ci = ci
        
    def setCO(self,co):
        self.co = co
        
    def getCI(self):
        return self.ci
        
    def getCO(self):
        return self.co
        
    def __init__(self, task_id, lab, dep, arr, deptime, arrtime, depday, arrday, HomeBases):
        self.task_id = task_id
        self.lab = lab
        self.dep = dep
        self.arr = arr
        self.deptime = deptime
        self.arrtime = arrtime
        self.depday = depday
        self.arrday = arrday
        self.ft = (arrday-1) * 1440 + arrtime - ( (depday-1) * 1440 + deptime )
        self.UT1 = 0
        self.UT2 = 0
        self.T = 0
        self.ci = 0
        self.co = 0

        # NOTE: Base handling is being reworked. In the latest design 
        #       we are not implementing this in each segment. Work in progress.
        # NOTE2: The concept of Base Weight is also being revised
        
        self.DepBaseWgt = 0 
        self.ArrBaseWgt = 0 
        
        if ( self.dep in HomeBases):
            self.DepBaseWgt = HomeBases[dep]
            
        if ( self.arr in HomeBases):
            self.ArrBaseWgt = HomeBases[arr]
    
'''
    Day Activity Item - (for solving assignment problems - TBD)
'''
            
class DayItem:
    def __init__(self, task_id, day):
        self.task_id = task_id            # 
        self.lab = "DO-" + str(day)  #
        self.t1 = 0             # Start of day
        self.t2 = 1439          # End of day
        self.date = day
        return

