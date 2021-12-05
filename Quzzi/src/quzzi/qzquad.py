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


from collections import defaultdict


class quadCoeff:
    def __init__(self):
        return

    # For constraint to achieve an exact value
    def getEqual(self,v):
        q = 2.0
        l = 1.0 - 2.0*v
        c = v ** 2.0
        return list([q,l,c])
    
    # For constraint to achieve at least one 
    # Todo: Solve an equation to create an AtLeastX
    def getAtLeastOne(self):
        q = 2.0 
        l = -3.0 
        c = 0.0
        return list([q,l,c])
    
    # For Cubic to Qubo constraints where an Ancillary must match a target
    def getBothOrNothing(self):
        q = -2.0 
        l = +1.0 
        c =  1.0
        return list([q,l,c])

    def getXOR(self):
        q =  2.0 
        l = -1.0 
        c = +1.0
        return list([q,l,c])

#======================================================================================================================================
# highOrderExpression class : 
# Given a weight, an array of variable ids representing a product of these variables and the next available variable id 
# to choose from for creating additional variables, return a Qubo representing the reduced product to a quadratic model.
#
# Usage: 
#
# W = 10000          # Intended weight
# P = 1              # Penalty weight for substituted pairs
# Vars = [1,2,3,4,5] # List of binary variable ids
#
# e = highOrderExpression(W,Vars)
#
# e.print()                      : Print the current state of the expression
# e.elaborate()                  : Elaborate the expression as a sum of terms with variable names
# e.reduceExpression(P=P,Y=6)    : Reduce a high order expression to a Quadratic order apply y1=x1x2 and adding the constraint terms
#    P : Penalty to apply for the substitution constraint
#    Y : The next variable id to use when adding new variables (Note: No high value variables to Y must be currently in use)
# e.qubo()                       : Return a Qubo (upper triangle) for the current expression if the order is < 3
# e.newvars                      : List of new variables needing to be created in a model using this expression
#
# Example using above parameters:
#
# e.print(): 
# Expression terms ========================
# 0: {'vars': [1, 2, 3, 4, 5], 'W': 10000}
#
# e.elaborate():
# ( 10000 )x1x2x3x4x5
#
# e.reduceExpression(P=1,Y=6) 
# e.elaborate():
# ( 1 )x1x2 + ( -2 )x1x6 + ( -2 )x2x6 + ( 3 )x6 + 
#             ( 1 )x3x4 + ( -2 )x3x7 + ( -2 )x4x7 + ( 3 )x7 + 
#             ( 1 )x5x6 + ( -2 )x5x8 + ( -2 )x6x8 + ( 3 )x8 + ( 10000 )x7x8
#
# e.newvars : 
# New variables [6, 7, 8]
#
# e.qubo() :
# defaultdict(<class 'float'>, {(0, 1): 1.0, (0, 5): -2.0, (1, 5): -2.0, (5, 5): 3.0, (2, 3): 1.0, (2, 6): -2.0, (3, 6): -2.0, (6, 6): 3.0, (4, 5): 1.0, (4, 7): -2.0, (5, 7): -2.0, (7, 7): 3.0, (6, 7): 10000.0})
#
#====================================================================================================================================

class highOrderExpression:
    # Hold one expression term : W x [ v1 x v2 x v3 x ... x vn ]
    class oneterm:
        def __init__(self,W,variables):
            self.vars = variables
            self.W = W
        def getOrder(self):
            return(len(self.vars))

    # Initialize an binary weighed expression
    # variables = list of variable ids
    # W = weight to apply to the product of these variables
    #
    def __init__(self, W=1, variables=None, subs={}):
        '''
        Create a sum of binary variable product expression with an optional first term
        
        :param W: Variable weight
        :param variables: Variable ids
        :param subs: Substituted variables when converting k-local to 2-local
        '''
        
        self.order = 0
        self.terms = []
        self.newvars = []
        #print("received these substitutions:", subs )
        self.substitutions = subs
        
        if ( variables is not None):
            term=self.oneterm(W,variables)
            if ( term is not None ):
                self.terms.append(term)
                self.order = max(self.order,term.getOrder()) # Adjust the order of the expression
            
    # Calculate expression order
    # Find the highest order expression and memorize the order
    def getExpressionOrder(self):
        self.order = 0
        for t in self.terms:
            if ( t is not None):
                self.order = max(self.order,t.getOrder())
        return(self.order)

    # Add a term with penalty P and coefficient C to the expression
    # P is the penalty weight to place on the variable reduction constraint
    # C is the coefficient intended for the original expression
    def add(self,x,P,C):
        #print("Adding this term:",x,P*C)
        self.terms.append(self.oneterm(P*C,x))
        return(self)
    
    def trim(self):
        self.terms = [t for t in self.terms if t is not None]

    # Invert binary variable: (x) -> (1-x)
    
    def inv_var(self,w,array,target):
        res = []
        ext = [a for a in array if a != target]
        res.append((1*w,ext))
        res.append((-1*w,array))
        return res
    
    # Invert terms for a target variable:  
    # ex: targ = y,  xyzt => x(1-y)zt => xzt - xyzt
    
    def inv_terms(self,terms,target):
        res = []
        
        for (w,v) in [t for t in terms]:
            # if the term has a target, process inversion
            # otherwise, keep term as is
            #print("Looking for",target,"in",v)
            if ( target in v):
                res.extend(self.inv_var(w,v,target))
            else:
                res.extend((w,v))
                
            #print("New list is", res)
            
        return res
    
    # Invert an entire expression: 
    # x1x2x3x4 => (1-x1)(1-x2)(1-x3)(1-x4) => (1-x2)(1-x3)(1-x4) - (1-x2)(1-x3)(1-x4)x1 => ... until only sum of product terms remain
    def inv_exp(self,wgt,variables):
        terms = [(wgt,variables)]
        for v in variables:
            terms = self.inv_terms(terms,v)
        return terms    

    # Print the list of expressions.
    # Note: Zero expressions come from substituting one expression to another 
    def print(self):
        print("Expression terms ========================")
        for i,t in enumerate(self.terms):
            print(i,end=': ')
            if ( t is None):
                print("Zero Term")
            else:
                print(t.__dict__)
    
    def elaborate(self):
        result = ""
        first=True
        for t in self.terms:
            if ( t is not None):
                if ( first ):
                    first = False
                else:
                    result = result + ' + '
                    #print(' + ',end='')
                result = result + "(" + str(t.W)+")"    
                #print("(",t.W,")", end='')
                for v in t.vars:
                    result = result + "x{}".format(v)
                    #print("x%s" %(v),end='')
        return result
        #print("")
                
    # Reduction to Quadratic
    # Applying variable substitution method introducing ancilla variables
    #
    # x0x1x2 ==> y0=x0x1 ==> P(x0x1 -2x0y0 -2x1y0 +3y0) + y0x2
    # Thus Wx0x1x2 = P(x0x1 -2x0y0 -2x1y0 +3y0) + Wy0x2
    #
    # Note: Remember to (consider to) add an ancilla constraint to make y0=x0x1
    #

    def reduceCubicTerm(self, P, x, y, W):
        
        # Generate the following terms from x and y
        # P(x0x1 -2x0y0 -2x1y0 +3y0) + Wy0x2     Note: x2 may be an array of n remaining terms requiring further reduction
        self.add([x[0],x[1]], P,  1)
        self.add([x[0],y[0]], P, -2)
        self.add([x[1],y[0]], P, -2)
        self.add([y[0]],      P, +3)
        #self.add(x[2:]+[y[0]], W, 1) # Add the remaining term with the substituted variable
        self.add([y[0]]+x[2:], W, 1) # Add the remaining term with the substituted variable
        #return(exp)

    def varkey(self,variables):
        key = ""
        for v in variables:
            key = key + "x" + str(v)
        return(key)

    # Invert binary variables in all terms
    # Note: Most useful when inverting the one initial term.
    
    def invertBinary(self, P=1, Y=100):
        newterms = []
        #print("Reducing expression order", self.order)
        for i,t in enumerate(self.terms):
            # Invert the term, add returned new terms
            newterms.extend(self.inv_exp(P*t.W, t.vars))
            self.terms[i]=None
            
        # Move new terms into expression
        for (w,a) in newterms:
            self.add(a, 1, w) 
        self.trim()
        return(Y)
    
    # Reduce HighOrder term.
    # If order > 3, perform y0=x0x1 substitution and recur to reduce the rest further
    # if order == 3, 
    
    def reduceHighOrder(self,term,Y,P=1):
        # Terms within quadratic order remain as is
        if ( term.getOrder() <= 2 ):
            self.add(term.vars, 1, term.W)
            return(Y)

        # Find out if we have reduced this term
        # before. If we have, obtain the substitution
        # variables. If not, create a new one
        
        key = self.varkey(term.vars[0:2])
        
        if ( key in self.substitutions ):
            y = [self.substitutions[key]]
            #print("Reusing reduction: ", key + " =>" + str(y[0]) )
        else:
            # Higher order term needs to be reduced
            # Add a new variable 
            y = [Y,] # new Y variable added
            Y += 1   # position for next variable
            self.newvars.extend(y)
            self.substitutions[key] = y[0]
            #print("added new variable to the list: ", self.newvars)
            #print("next var will be: ", Y )
            
            # NOTE: Impose this penalty only once at creation of the substitution.
            #       Do not repeat each time it is used so this must be in the 
            #       "else" portion of the subs lookup
            # Impose a penalty term P(x0x1 -2x0y0 -2x1y0 +3y0)
            self.reduceCubicTerm(P, term.vars, y, term.W)

        # Return the next variable position
        return(Y)
        
        
    # Working our way from the start of the terms array 
    # down to the end, replace each term having N >= 3 variables
    # with a reduced equivalent series, bring the expression down to a Quadratic version 
    
    def reduceExpression(self, P=1, Y=100):
        while ( self.getExpressionOrder() >= 3):
            #print("Reducing expression order", self.order)
            for i,t in enumerate(self.terms):
                if ( t is not None):
                    if ( t.getOrder() > 2 ):
                        #print("Reducing:",t.__dict__)
                        #exp = self.reduceCubicTerm(P,t.vars,[Y],t.W)
                        Y = self.reduceHighOrder(t,Y,P=P)
                        self.terms[i]=None
                        #self.print()
        self.trim()
        return(Y)

    # create a Qubo / Upper triangle method for the current expression
    # Will only return a Qubo for order 2 or less expressions
    # Variable ids are assumed as 1 origin and placed in Qubo using 0 origin
    
    def qubo(self):
        if ( self.getExpressionOrder()>2): return None
        Q = defaultdict(float)
        for t in self.terms:
            if ( t is not None ):

                # Linear Qii terms
                if ( len(t.vars) == 1 ):
                    i = t.vars[0]
                    if ( not (i,i) in Q ):
                        Q[(i,i)] = 0.0
                    Q[(i,i)] += t.W
                    #print("Q%d%d=%d" % (i,i,Q[(i,i)]))

                # Quadratic Qij terms
                if ( len(t.vars) == 2 ):
                    (i,j) = tuple(sorted([t.vars[0], t.vars[1]]))
                    if ( not (i,j) in Q ):
                        Q[(i,j)] = 0.0
                    Q[(i,j)] += t.W
                    #print("Q%d%d=%d" % (i,j,Q[(i,j)]))
        return (Q)
        
    def applyQubo(self,Q):
        if ( self.getExpressionOrder()<3 ):
            for t in self.terms:
                if ( t is not None ):

                    # Linear Qii terms
                    if ( len(t.vars) == 1 ):
                        i = t.vars[0]
                        if ( not (i,i) in Q ):
                            Q[(i,i)] = 0.0
                        Q[(i,i)] += t.W
                        #print("Q%d%d=%d" % (i,i,Q[(i,i)]))

                    # Quadratic Qij terms
                    if ( len(t.vars) == 2 ):
                        (i,j) = tuple(sorted([t.vars[0], t.vars[1]]))
                        if ( not (i,j) in Q ):
                            Q[(i,j)] = 0.0
                        Q[(i,j)] += t.W
                        #print("Q%d%d=%d" % (i,j,Q[(i,j)]))        
        else:
            print("Warning: Attempting to apply unreduced higher order expression to a Qubo")
        
