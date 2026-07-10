# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 10:16:26 2019

@author: Robert.Culver
"""
import numpy as np
import os
import matplotlib.pyplot as plt

from simulation.engine_interface import RadiographSim, DEFAULT_BG_THRESH, GeomSetup
from metrics.registration_metrics import histSimilarity, homogSimilarity, greySimilarity
from metrics.blur_matching import matchBlur
from _utilities.img_manip import imread, imresize,getAllFiles

DEFAULT_FKW = [ # [function, kwargs, weight]
                [histSimilarity, dict(bins = 500, vmax = 50000), 1.0],
                [homogSimilarity, dict(patchSize = 100, evalFeatures = 100), 1.0],
                [greySimilarity, dict(), 0.5]
]

class _RegBase(object):
    '''Provides the bits required to compare experimental radiographs and simulation'''
    def __init__(
            self,
            projdir,                        # Directory to projections
            simSetup,                       # Kwargs for ttmp obj
            mpgsObjKwargs=None,             # Kwargs for mpgs
            N=3,                            # number of projections to fit
            blur=0,                         # sigma param for scipy.ndimage.gaussian_filter
            fkw = DEFAULT_FKW,              # list of sub objectives [[fun,kwarg,weights], ...] to run
            geomSetup = None,
            nThreads = 1,
        ):
        assert os.path.isdir(projdir), 'projdir not found: {}'.format(projdir)
        duplicatedLast = True
        allFiles = getAllFiles(projdir, False)
        self.inds = inds = np.arange(0,len(allFiles),len(allFiles)/N).astype(np.int)
        self.thetas = np.linspace(0.0,-360.0,len(allFiles) + (not duplicatedLast))[inds]%360.0
        w, h = simSetup.detShape
        self.refs = np.array([imresize(imread(allFiles[i]),w,h) for i in self.inds], dtype = np.float32)
        self.radsim = RadiographSim(simSetup, mpgsObjKwargs=mpgsObjKwargs, projdir=projdir)
        self.blur = blur
        self.objFuns,self.objKwargs,self.weights = tuple(zip(*fkw))
        self.nThreads = nThreads

    def getSims(self, args):
        '''Returns sim for given args. arg format is set by child class _toKwargs'''
        geomSetup, mappingKwargs = self._toKwargs(args)
        sims = self.radsim.get(self.thetas, geomSetup=geomSetup, mappingKwargs=mappingKwargs, blur=self.blur, nThreads=self.nThreads)
        return sims

    def objective(self, args):
        '''Calculates objectives for given args. Args is an array which varies in length, and must match arg length required for child class'''
        sims = self.getSims(args)
        projObjs = [self._objective(r, s) for r, s in zip(self.refs, sims)]
        return (np.mean(projObjs),)

    def _objective(self, ref, sim):
        '''Weighted average objective for a single pair of ref and sim'''
        oVals = [fun(ref.astype(np.float32), sim.astype(np.float32), **kwargs) for fun, kwargs in zip(self.objFuns, self.objKwargs)]
#        weightedAv = np.multiply(self.weights,oVals).sum()/np.sum(self.weights)
        weightedAv = np.sum([w*v for w, v in zip(self.weights, oVals) if v])
        weightedAv /= np.sum([w for w,v in zip(self.weights, oVals) if v])
        return weightedAv    

    def _toKwargs(self, args):
        '''generates geom and mapping kwars: child class specifies this'''
        raise NotImplementedError('_RegBase only to be used through inheritance.')


class OffsetsRegistration(_RegBase):
    '''Provides objective for rough registration of part position on plate'''

    argOrder = ['ox', 'oy', 'oz', 'sod', 'sdd']
    
    def _toKwargs(self, args):
        '''ox, oy, oz, sod, sdd = args'''
        ox, oy, oz, sod, sdd = args
        geomSetup = GeomSetup(
                angles = np.zeros(3),
                offsets = np.array([ox, oy, oz]),
                sod = sod,
                sdd = sdd,
                axisOffs = 0.0)
        mappingKwargs = self.radsim.mpgs.getMappingKwargs() # Will default to mapping kwargs set during mpgs __init__
        return geomSetup, mappingKwargs
    
    
class GeomRegistration(_RegBase):
    '''Provides objective for rough registration of part position and angle on plate'''

    argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd']
    
    def _toKwargs(self, args):
        '''ax, ay, az, ox, oy, oz, sod, sdd = args'''
        ax, ay, az, ox, oy, oz, sod, sdd = args
        geomSetup = GeomSetup(
                angles = np.array([ax, ay, az]),
                offsets = np.array([ox, oy, oz]),
                sod = sod,
                sdd = sdd,
                axisOffs = 0.0)
        mappingKwargs = self.radsim.mpgs.getMappingKwargs() # Will default to mapping kwargs set during mpgs __init__
        return geomSetup, mappingKwargs
    
        
class FullRegistration(_RegBase):
    '''Provides objective for full registration'''

    argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'lam', 'offs', 'ampl', 'bgVal']
    
    def _toKwargs(self, args):
        '''ax, ay, az, ox, oy, oz, sod, sdd, axisOffs, lam, offs, ampl, bgVal = args'''
        ax, ay, az, ox, oy, oz, sod, sdd, axisOffs, lam, offs, ampl, bgVal = args
        geomSetup = GeomSetup(
                angles = np.array([ax, ay, az]),
                offsets = np.array([ox, oy, oz]),
                sod = sod,
                sdd = sdd,
                axisOffs = axisOffs)
        mappingKwargs = { 'bgVal': bgVal, 'bgThreshVal': DEFAULT_BG_THRESH, 'lam': lam, 'offs': offs, 'ampl': ampl }
        return geomSetup, mappingKwargs
        

class FullReg2(_RegBase):
    '''Provides full registration using Akima spectrum'''
    
    argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'akimaArgs']
    
    def _toKwargs(self, args):
        ax, ay, az, ox, oy, oz, sod, sdd, axisOffs = args[:9]
        akimaArgs = args[9:]
        geomSetup = GeomSetup(
                angles = np.array([ax, ay, az]),
                offsets = np.array([ox, oy, oz]),
                sod = sod,
                sdd = sdd,
                axisOffs = axisOffs)
        mappingKwargs = {'akimaArgs':akimaArgs}
        return geomSetup, mappingKwargs
    
