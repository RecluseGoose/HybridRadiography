# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 16:34:36 2019

@author: robert.culver
"""
import os
import scipy.ndimage
import numpy as np
import joblib
import gc
import matplotlib.pyplot as plt

import engine.material_path
import engine.rays
from simulation import transformations
from _utilities._defaults import USER_DOCS
from _utilities._tools import portionOutList

cadpath = os.path.join(USER_DOCS,'artist_placation2.stl')
detShape=(1200, 1000)
detSize=(400.0,400.0)
N = 4
angs = np.zeros((N,3))
offs = np.zeros((N,3))
sod = np.ones(N)*1150.0
ssd = np.ones(N)*3000.0

class MPEngObject(object):
    def __init__(self, cadpath, xres, yres):    
        self.cadpath = cadpath
        self.xres = xres
        self.yres = yres
        self._initiate()
        
    def _initiate(self):
        '''helper func: initiation must happen on init and picklng'''
        self.eng = engine.material_path.MatPath(self.cadpath, self.xres, self.yres)
    
    def __call__(self, *args, **kwargs):
        out = self.eng.calculate(*args, **kwargs)
        return out
    
    def __getstate__(self):
        if hasattr(self,'eng'):
            del self.eng
        return self.__dict__
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._initiate()

    @staticmethod
    def _para(cadpath, xres, yres, hfov, engAngs, engOffs):
        '''Joblib insists there are serialisation difficulties...'''
        eng = MPEngObject(cadpath, xres, yres)
        output = eng(hfov, np.array(engAngs), np.array(engOffs))
        del eng      # some weird behaviour when running in parallel
        gc.collect() # some weird behaviour when running in parallel
        return output
        
class TurntableMatpath(object):
    '''
    Calculates material paths 
    '''
    def __init__(
            self,
            cadpath,
            detShape=(1000,1000),       # Detector image resln
            detSize=(200.0,200.0),      # Physical detector size
            defaultArgs={'sod':254.0, 'sdd':1145.0}
        ):
        ''''''
        self.cadpath = cadpath
        self.cadPartCentre = transformations.Transformations.getCentreOfSTL(cadpath)
        self._padding = 1 # padding the engine output is a good idea, as sometimes the edge values can be erratic
        self.eng = MPEngObject(cadpath, detShape[0]+2*self._padding, detShape[1]+2*self._padding)
        self.defaultArgs = defaultArgs
        self.detSize = detSize
        self.detShape = (self.eng.xres, self.eng.yres)

    def _trimPadding(self, arr):
        p = self._padding
        return arr[p:-p,p:-p] if (arr.ndim == 2) else arr[:,p:-p,p:-p]

    def getMatPathImgs(
         self,
         N = None,
         thetas = None,
         angs = np.zeros(3),
         offs = np.zeros(3),
         sod = None,
         sdd = None,
         axisOffs = 0.0,
         firstLastDuplication = False,
         nThreads = 1,
        ):
        '''generates configurations for args for calc... a configuration is any combination of geometrical param'''
        # Deal with arguments
        assert (N is None) ^ (thetas is None),'Must specify thetas or N, not both'
        assert (sod is not None) ^ ('sod' in self.defaultArgs.keys()), 'No value found for sod'
        sod = sod if (sod is not None) else self.defaultArgs['sod']
        assert (sdd is not None) ^ ('sdd' in self.defaultArgs.keys()), 'No value found for sdd'
        sdd = sdd if (sdd is not None) else self.defaultArgs['sdd']
        hfov = self._calcFov(sdd)
        # Run with/without parallelisation
        transGen = transformations.TT_Transformations()
        transGenKwargs = dict( part_orientation = angs,
                              part_offset = offs,
                              part_centre = self.cadPartCentre,
                              srcToObjDist = sod,
                              camera_elevation=0.0,
                              camera_yaw=0.0,
                              camera_roll=-90.0,
                              lateral_offset= axisOffs )
        thsSupplied = (thetas is not None)
        transGenKwargs['thetas' if thsSupplied else 'N'] = thetas if thsSupplied else N
        engArgOffsFun = transGen.turntableAnglesOffsetsPositions if thsSupplied else transGen.turntableAnglesOffsetsSweep
        engAngs, engOffs = engArgOffsFun(**transGenKwargs)
        if (nThreads == 1):
            imgs = self.eng(hfov, engAngs, engOffs)
        else:
            portAngs = portionOutList(engAngs,nThreads)
            portOffs = portionOutList(engOffs,nThreads)
            portImgs = joblib.Parallel(n_jobs =nThreads)(
                       joblib.delayed(MPEngObject._para)(self.cadpath,self.detShape[0],self.detShape[1],hfov,pAngs,pOffs)
                       for pAngs,pOffs in zip(portAngs,portOffs))
            imgs = np.concatenate(portImgs, axis = 0)
            del portImgs
            gc.collect()
        # Duplicated first as last if requred
        if firstLastDuplication:
            imgs = np.concatenate((imgs,imgs[0,None]),axis=0)
        return self._trimPadding(imgs)
    
    def _calcFov(self, sdd):
        # padFactor increases effective det size from actual physical size
        padFactor = self.eng.xres * 1.0 / ( self.eng.xres - 2*self._padding )
        hfov_half = np.arctan(self.detSize[0] * padFactor /sdd)
        return np.rad2deg(hfov_half*2.0)

    
#class TurntableRadiograph(TurntableMatpath):
#    def __init__(self, cadpath, detShape, detSize, defaultParams):
#        super(TurntableRadiograph,self).__init__(cadpath, detShape, detSize, defaultParams)
#    
#    def specifyRelation_poly(self, pfit):
#        pass

plt.close('all')

def play(imgs):
    transformations.playStack(imgs, vmin = 0, vmax = 20, loops  =2)

def jibs(imgs):
    n = int(np.sqrt(len(imgs)))
    xres,yres = imgs.shape[1:]
    outs = np.zeros((n*xres,n*yres))
    for i in range(n):
        for j in range(n):
            outs[i*xres:(i+1)*xres,j*yres:(j+1)*yres] = imgs[i*n + j]
    plt.matshow(outs, vmin = 0, vmax = 25, cmap = 'gray_r')        
    plt.show()

mp =TurntableMatpath(cadpath,(300,300))
N  = 49
imgs = [mp.getMatPathImgs(N,nThreads=5, offs = [0,0,.0], angs = [0,0,a]) for a in np.linspace(0,45.0,5)] 
[jibs(img) for img in imgs]