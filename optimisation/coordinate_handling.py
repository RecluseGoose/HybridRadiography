# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 13:37:23 2018

@author: robert.culver
"""
import numpy as np
import types
from pdb import set_trace as dbg

class NormalisedCoord(object):
    """ Class represents a coordinate, and stores methods for normalisation and unnormalisation.

    args:
            value:                  input vector [x1, x2, ...]
            bounds:                 boundaries for each component [(x1_min,x1_max), (x2_min,x2_max), .... ]
            names:                  can specify names ['x','y','z','theta_x', ...]
            edges:                  specifies what to do when value overshoots bounds ['reflect','clamp','cycle', ...]
            inputIsNormalised:      option to initialise object with a normalised vector (default is False)

    methods:
            setValue(value):        updates stored .value and .normValue parameters
            setNormValue(value):    updates stored .value and .normValue parameters (with a normalised value input)
            normalise(value):       returns normalised vector using generated normalisation methods
            unnormalise(value):     returns unnormalised vector using generated unnormalisation methods

    useful class parameters:
            value       stored vector
            normValue   normalised stored vector

    ## USAGE AND UNIT TESTS ##
    # Can normalise with initialisation, or after initialisation
    >>> value = [174.0,14.0]
    >>> bounds = [(0,180.0),(0,90.0)]
    >>> p = NormalisedCoord(value, bounds)
    >>> p.value, np.round(p.normValue,3)
    (array([ 174.,   14.]), array([ 0.967,  0.156]))

    # Can specify different modes of boundary methods
    >>> value = [-181.0,91.0,12.0]
    >>> bounds = [(-180.0,180.0),(0,90.0),(0.0,10.0)]
    >>> boundaryMethods = ['cycle','reflect','clamp']
    >>> p = NormalisedCoord(value, bounds, edges = boundaryMethods)
    >>> p.value, np.round(p.normValue,3)
    (array([ 179.,   89.,   10.]), array([ 0.997,  0.989,  1.   ]))

    # Can use this object to normalise/unnormalise values, without actually changing the held value (note our boundary methods from before)
    >>> normalised = p.normalise([181.0,1.0,-10.0])
    >>> np.round(normalised,3)
    array([ 0.003,  0.011,  0.   ])
    >>> unnormalised = p.unnormalise([0.75,-0.1,0])         ### Note that the boundary methods work in reverse as well... ###
    >>> unnormalised
    array([ 90.,   9.,   0.])
    >>> p.value, np.round(p.normValue,3)                    ### Note that we haven't changed the stored values ###
    (array([ 179.,   89.,   10.]), array([ 0.997,  0.989,  1.   ]))

    # Can also apply edge methods to normalised coordinates
    >>> mutatedNormal = [1.1, 1.1, 1.1]
    >>> p.applyEdgesToNorm(mutatedNormal)
    array([ 0.1,  0.9,  1. ])

    # Can change the stored values
    >>> p.setNormValue(normalised)
    >>> p.value, np.round(p.normValue,3)
    (array([-179.,    1.,    0.]), array([ 0.003,  0.011,  0.   ]))
    >>> p.setValue(unnormalised)
    >>> p.value, np.round(p.normValue,3)
    (array([ 90.,   9.,   0.]), array([ 0.75,  0.1 ,  0.  ]))

    # Can find distance between two normalised vectors:
    >>> v0 = [0.2,0.9,0.1]
    >>> v1 = [0.8,0.7,0.2]
    >>> dists = p.getNormDists(v0,v1)
    >>> print(np.round(dists,3))                            # (first element is in cycling mode... so 0.4 dist is correct for first el)
    [ 0.4  0.2  0.1]

    # Can specify parameter names to create an object absent of the value parameters
    >>> p = NormalisedCoord(names = ['Alvin', 'Simon', 'Theodore'],bounds = bounds)
    >>> p.nDim
    3
    
    # Test pickling
    >>> import pickle
    >>> pkl = pickle.dumps(p)
    >>> p2 = pickle.loads(pkl)
    >>> p2.normalise([0.2,0.1,-0.4]) == p.normalise([0.2,0.1,-0.4])
    array([ True,  True,  True], dtype=bool)
    """
    def __init__(self, value = None, bounds = None, nDim = None, names = None, edges = None, inputIsNormalised = False):
        '''Create instance of ParameterCoordinate'''
        # Error checking: number of dimensions
        self.nDim = max([len(arg) if arg is not None else 0 for arg in [value,bounds,names]]) if nDim is None else int(nDim)
        # Error checking: names
        if names is not None: assert (isinstance(names,(tuple,list)) and all([isinstance(s,str) for s in names])), 'Invalid names argument. Must be list/tuple of strings.'
        # Error checking: edge modes
        validEdgeModes = ['clamp','reflect','cycle']
        if edges is not None:
            edgesArgIsString = isinstance(edges,str) and (edges in validEdgeModes)
            edgesArgIsTupList = isinstance(edges,(tuple,list)) and (len(edges) == self.nDim) and all([isinstance(e,str) and (e.lower() in validEdgeModes) for e in edges])
            assert (edgesArgIsString or edgesArgIsTupList), 'Invalid names argument. Must be list/tuple of strings in: '+''.join([e+', ' for e in validEdgeModes[:-1]]) +validEdgeModes[-1]+'. Also, check arg lengths.'
        # Error checking: bounds
        if bounds is not None:
            assert (isinstance(bounds,(tuple,list,np.ndarray)) and (len(bounds) == self.nDim)
                    and all([isinstance(b,(tuple,list,np.ndarray)) and (len(b)==2) for b in bounds])
                    and all([b[0]<b[1] for b in bounds])), 'Invalid boundaries.'
        # Initialise class instance parameters...
        self.bounds = bounds if (bounds is not None) else [(0.0,1.0)]*self.nDim
        self.names = names if (names is not None) else ["P{}".format(i) for i in range(self.nDim)]
        self.edges = edges if ((edges is not None) and edgesArgIsTupList) else [edges]*self.nDim if ((edges is not None) and edgesArgIsString) else ['clamp']*self.nDim
        self._initNormalisation(self.bounds)
        # Initialise value, if specified
        if value is not None:
            if inputIsNormalised:
                self.setNormValue(value)
            else:
                self.setValue(value)

    def __len__(self):
        return self.nDim

    def _initNormalisation(self,bounds):
        '''Helper func, sets up _normScales and _edgeMethods'''
        self._normScales = np.array([1.0/(upper-lower) for lower, upper in bounds])
        edgeMethods = [self._edgesClamp if (method == 'clamp') else
                       self._edgesReflect if (method == 'reflect') else self._edgesCycle #if (method == 'cycle')
                       for method in self.edges]
        self._edgeMethod = lambda vector: np.array([m(v,b) for m,v,b in zip(edgeMethods,vector,bounds)])
        
    def __getstate__(self):
        '''Custom pickling for handling of of lambda'''
        copyDict = dict(self.__dict__)
        del copyDict['_edgeMethod']
        return copyDict
            
    def __setstate__(self,d):
        '''Custom pickling for handling of of lambda'''
        self.__dict__ = (d)
        self._initNormalisation(self.bounds)

    def _edgesClamp(self,x,bound):
        '''Boundary handling. Clamps values to edge of bounds.'''
        if x < bound[0]:
            return bound[0]
        elif x > bound[1]:
            return bound[1]
        else:
            return x

    def _edgesReflect(self,x,bound):
        '''Boundary handling: reflection. for example, in spherical coordinates the elevation angle reflects. Resorts to clamping if overshoot is greater than half the range'''
        range_ = bound[1]-bound[0]
        centre = 0.5*(bound[0] + bound[1])
        diff = bound[0]-x
        if np.abs(centre - x) > range_:
            return self._edgesClamp(x,bound)
        if x < bound[0]:
            return (bound[0] + diff)%(range_) + bound[0]
        elif x > bound[1]:
            return (bound[1] + diff)%(range_) + bound[0]
        else:
            return x

    def _edgesCycle(self,x,bound):
        '''Boundary handling: cycling. for example, in spherical coordinates the azimuthal angle cycles'''
        if (x < bound[0]) or (x >= bound[1]):
            return (x - bound[0])%(bound[1]-bound[0]) + bound[0]
        else:
            return x

    def normalise(self,v0):
        '''Normalise an unnormalised coordinate'''
        assert(np.shape(v0) == (self.nDim,)),'Invalid input. Input must be vector equal to length self.nDim'
        edgecorrected = self._edgeMethod(v0)
        return (edgecorrected - np.array(self.bounds).T[0])*self._normScales

    def unnormalise(self,v0):
        '''Unnormalise a normalised coordinate'''
        assert(np.shape(v0) == (self.nDim,)),'Invalid input. Input must be vector equal to length self.nDim'
        return self._edgeMethod(v0/self._normScales + np.array(self.bounds).T[0])

    def applyEdgesToNorm(self,v0):
        '''Takes in a previously normalised coordinate and applies edge conditions.'''
        unnorm = self.unnormalise(v0)
        renorm = self.normalise(unnorm)
        return renorm

    def setValue(self,v0):
        '''Set normalised (and unnormalised) value by supplying an unnormalised value'''
        self.normValue = self.normalise(v0)
        self.value = self.unnormalise(self.normValue)

    def setNormValue(self,v0):
        '''Set unnormalised (and normalised) value by supplying a normalised value'''
        self.value = self.unnormalise(v0)
        self.normValue = self.normalise(self.value)

    def getNormDists(self,v0,v1):
        '''Finds difference between two normalised vectors'''
        mincs = np.min([v0,v1],axis=0)
        maxcs = np.max([v0,v1],axis=0)
        assert (maxcs.max() <= 1.0) and (mincs.min() >= 0.0), "Input vector coordinates must be within [0,1]"
        dists = np.array([x1-x0 if (edge != 'cycle') else np.minimum(x1-x0,x0-x1+1.0) for x0,x1,edge in zip(mincs,maxcs,self.edges)])
        return dists


class ParameterCoord(NormalisedCoord):
    '''Class represents an optimisation parameter coordinate, and stores methods for normalisation and unnormalisation. This is a NormalisedCoord class
    with an added vary argument.

    Note that the vary list is attached to the class to prevent these parameters from being changed. It only affects things in the normalisation, and so

    args:
            value:                  input vector [x1, x2, ...]
            bounds:                 boundaries for each component [(x1_min,x1_max), (x2_min,x2_max), .... ]
            vary:                   specifies whether to vary component or not [True, False, True, ... ]
            names:                  can specify names ['x','y','z','theta_x', ...]
            edges:                  specifies what to do when value overshoots bounds ['reflect','clamp','cycle', ...]
            inputIsNormalised:      option to initialise object with a normalised vector (default is False)

    methods:
            setValue(value):        updates stored .value and .normValue parameters, can specify dict input
            setNormValue(value):    updates stored .value and .normValue parameters (with a normalised value input), can specify dict input
            normalise(value):       returns normalised vector using generated normalisation methods
            unnormalise(value):     returns unnormalised vector using generated unnormalisation methods

    useful class parameters:
            value       stored vector
            normValue   normalised stored vector
            vary        specifies which values should be changed

    ## USAGE AND UNIT TESTS ##
    >>> value = [181.0,-10.0,12.0]
    >>> bounds = [(-180.0,180.0),(0,90.0),(0.0,10.0)]
    >>> names = ['az','alt','rad']
    >>> boundaryMethods = ['cycle','reflect','clamp']
    >>> vary = [True, True, False]
    >>> p = ParameterCoord(value, bounds, edges = boundaryMethods, vary = vary, names = names)
    >>> p.value, np.round(p.normValue,3)
    (array([-179.,   10.,   10.]), array([ 0.003,  0.111,  1.   ]))

    # Now if we try and set the third value (which isn't varying), the input is ignored.
    >>> p.setValue([-18.0, 0.0, 1.0])
    >>> p.value, np.round(p.normValue,3)
    (array([-18.,   0.,  10.]), array([ 0.45,  0.  ,  1.  ]))

    # Also, if you set the values using dicts, you will get errors if you try to change a fixed parameter.
    >>> p.setValue({'alt':9.0, 'az':-36.0})
    >>> p.value, np.round(p.normValue,3)
    (array([-36.,   9.,  10.]), array([ 0.4,  0.1,  1. ]))
    >>> p.setNormValue({'alt':0.1, 'az':0.4})
    >>> p.value, np.round(p.normValue,3)
    (array([-36.,   9.,  10.]), array([ 0.4,  0.1,  1. ]))
    '''
    def __init__(self, value = None, bounds = None, vary = None, *args,**kwargs):
        self._valNotSet = True
        super(ParameterCoord,self).__init__(value, bounds, *args,**kwargs)
        self.vary = np.array(vary if (vary is not None) else [True]*self.nDim)

    def setValue(self,v0):
        '''Set normalised (and unnormalised) value by supplying an unnormalised value'''
        if self._valNotSet:
            super(ParameterCoord,self).setValue(v0)
            self._valNotSet = False
        else:
            super(ParameterCoord,self).setValue(self._applyVary(v0))

    def setNormValue(self,v0):
        '''Set unnormalised (and normalised) value by supplying a normalised value'''
        if self._valNotSet:
            super(ParameterCoord,self).setNormValue(v0)
            self._valNotSet = False
        else:
            super(ParameterCoord,self).setNormValue(self._applyVary(v0))

    def _applyVary(self,v0):
        '''Prevents overwrite of protected components (specified by vary)'''
        v0 = self._dealWithInput(v0)
        v1 = self.value
        v1[self.vary] = np.array(v0)[self.vary]
        return v1

    def _dealWithInput(self,input_):
        '''Allows list, tuple, ndarray, or dict input'''
        if isinstance(input_,(tuple, list, np.ndarray)):
            return np.array(input_)
        elif isinstance(input_,dict):
            vals = input_.values()
            keys = input_.keys()
            out = self.value if hasattr(self,'values') else np.zeros(self.nDim, dtype = np.array(vals).dtype)
            assert all([(key in self.names) and self.vary[self.names.index(key)] for key in keys]),'Inaccessible parameter name.'
            for val,key in zip(vals,keys):
                out[self.names.index(key)] = val
            return out
        else:
            raise (TypeError,'Invalid input')