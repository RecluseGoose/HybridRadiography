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

import engine.material_path2
import engine.rays
from simulation.mapping import MatpathGreyscaleMapping
from simulation import transformations
from simulation import poisson
from _utilities.tools import portionOutList
from _utilities.img_manip import imread,getAllFiles


DEFAULT_BG_THRESH = 0.0001 # material path value that defaults to bg

def _reshapeDefaults1D(arg, N, name = None):
    '''helper function for formatting inputs'''
    assert name in ['flipnorms', 'densities'], 'name "{}" not in compatible arg list'.format(name)
    out = np.repeat(np.atleast_1d(arg), N, axis=0) if (not np.iterable(arg) or (len(arg) != N)) else np.array(arg)
    assert (out.shape[0] == N), 'Shape of reformatted {} is {}, shape ({}, X) expected.'.format(name, out.shape, N)
    return out.astype(np.bool if name == 'flipnorms' else np.double)

def _reshapeDefaults2D(arg, N, name='arg'):
    '''helper function for formatting inputs'''
    assert name in ['angles', 'offsets', 'scales'], 'name "{}" not in compatible arg list'.format(name)
    out = np.repeat(np.atleast_2d(arg), N, axis=0) if (np.ndim(arg) == 1) else np.array(arg)
    assert (out.shape[0] == N), 'Shape of reformatted {} is {}, shape ({}, X) expected.'.format(name, out.shape, N)
    return out.astype(np.double)

class _SetupObj(object):
    def __str__(self):
        className = [str(self.__class__)]
        keyVals = [str(k) + ': ' + str(v) for k,v in self.__dict__.items()]
        return '\n'.join(className + keyVals)
    
    def _reshapeDefaults1D(self, vals, N, name):
        return _reshapeDefaults1D(vals, N, name) ## TODO! refactor properly
    
    def _reshapeDefaults2D(self, vals, N, name):
        return _reshapeDefaults2D(vals, N, name) ## TODO! refactor properly

class GeomSetup(_SetupObj):
    '''
    '''
    def __init__(
            self,
            angles = np.zeros(3),
            offsets = np.zeros(3),
            sod = None,
            sdd = None,
            axisOffs = 0.0
        ):
        self.nMesh = len(angles) if np.ndim(angles)==2 else 1
        self.angles = self._reshapeDefaults2D(angles, self.nMesh, 'angles')
        self.offsets = self._reshapeDefaults2D(offsets, self.nMesh, 'offsets')
        self.sod = sod
        self.sdd = sdd
        self.axisOffs = axisOffs
        
    def getSingleSetup(self, i=0):
        out = GeomSetup(
            angles = self.angles[i],
            offsets = self.offsets[i],
            sod = self.sod,
            sdd = self.sdd,
            axisOffs = self.axisOffs
        )
        return out
        
        
class SimSetup(_SetupObj):
    '''
    '''
    def __init__(
            self,
            cadpaths = None,            # <-- list of cads, first defines reference point for coordinate system
            detSize = (200.0, 200.0),   # beware, this is detector half-size...
            detShape=(1000,1000),       # Detector image resolution
            scales = np.ones(3),        # 
            densities = np.array([1]),  # 
            flipnorms = np.array([0]),  # 
        ):
        cadpathsIsIterable = (not isinstance(cadpaths,str)) and np.iterable(cadpaths)
        self.nMesh = len(cadpaths) if cadpathsIsIterable else 1
        self.cadpaths = cadpaths if cadpathsIsIterable else [cadpaths]
        self.detSize = detSize
        self.detShape = detShape
        self.scales = self._reshapeDefaults2D(scales, self.nMesh, 'scales')
        self.densities = self._reshapeDefaults1D(densities, self.nMesh, 'densities')
        self.flipnorms = self._reshapeDefaults1D(flipnorms, self.nMesh, 'flipnorms')
        
        
    def getSingleSetup(self,i=0):
        assert (not isinstance(self.cadpaths,str)) and (len(self.cadpaths) >= 1), 'cadpaths must be list of cads'
        out = SimSetup(
            cadpaths = self.cadpaths[i],
            detSize = self.detSize,
            detShape = self.detShape,
            scales = self.scales[i],
            densities = self.densities[i],
            flipnorms = self.flipnorms[i]
        )
        return out


class MPEngObject(object):
    def __init__(self, engKwargs):
        '''engKwargs is expected to contain everything required for the scene setup...
        filenames, xres, yres, angles, offsets, scales, densities, flipnorms'''
        self.engKwargs = engKwargs
        self._initiate()
        
    def _initiate(self):
        '''helper func: initiation must happen on init and picklng'''
        for file in self.engKwargs['filenames']:
            assert os.path.exists(file),'file not found: '.format(file)
        self.eng = engine.material_path2.MatPath(**self.engKwargs)
        
    def __call__(self, hfov, engAngs, engOffs, bltrs, slices):
        nShots = len(engAngs)
        roiToPass = self._parseRois(bltrs, nShots)
        for arr in [engAngs, engOffs, roiToPass]:
            assert ((len(arr)==nShots) and np.ndim(arr)==2),'engine inputs unequal lengths, {}'.format(arr)
        out = self.eng.calculate(hfov, np.array(engAngs), np.array(engOffs), roiToPass)
        return out if (slices is None) else np.array([o[s] for o,s in zip(out, slices)])
    
    def _parseRois(self,bltrs,nShots):
        if (bltrs is not None):
            roiToPass = np.zeros_like(bltrs).astype(np.double)
            for i,roi in enumerate(bltrs):
                b,l,t,r = roi
                # need to do LR flip..
                l2 = self.engKwargs['xres'] - r
                r2 = self.engKwargs['xres'] - l
                roiToPass[i] = np.array([b,l2,t,r2])
        else:
            b,l = 0.0, 0.0
            t,r = self.engKwargs['xres']-1.0, self.engKwargs['yres']-1.0
            roiToPass = np.repeat([[b,l,t,r]], nShots , axis = 0)
        return roiToPass
    
    def __getstate__(self):
        if hasattr(self,'eng'):
            del self.eng
        return self.__dict__
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._initiate()

    @staticmethod
    def _para(engKwargs, hfov, engAngs, engOffs, rois, slices):
        '''Joblib insists there are serialisation difficulties...'''
        eng = MPEngObject(engKwargs)
        out = eng(hfov, np.array(engAngs), np.array(engOffs), rois, slices)
        del eng      # some weird behaviour when running in parallel
        gc.collect() # some weird behaviour when running in parallel
        return out


class _EngineInteractor(object):
    '''Base class for classes interacting with the engine.'''
    def __init__(self):
        raise NotImplementedError('Abstract class; only use as parent class')
        # Compulsory properties
        self._padding = 1 # padding the engine output is a good idea, as sometimes the edge values can be erratic
        # Should be overwritten after inheritance
        self.geomSetup = None # geomSetup object
        self.eng = None
        self.detSize = None
        self.xres, self.yres = [s + 2*self._padding for s in self.detShape]
        self.cadPartCentre = np.zeros(3, dtype = np.float) #TODO! This probably needs changing
        
    def _getEngAngOffsFov(self, thetas, N, geomSetup):
        # Deal with arguments
        assert (N is None) ^ (thetas is None),'Must specify thetas or N, not both'
        sod = geomSetup.sod
        sdd = geomSetup.sdd
        assert (sod is not None) or (self.geomSetup.sod is not None), 'No value found for sod'
        sod = sod if (sod is not None) else self.geomSetup.sod
        assert (sdd is not None) or (self.geomSetup.sdd is not None), 'No value found for sdd'
        sdd = sdd if (sdd is not None) else self.geomSetup.sdd
        hfov = self._calcFov(sdd)
        # Run with/without parallelisation
        transGen = transformations.TT_Transformations()
        i = 0 # This has to be wrong
        transGenKwargs = dict( 
            part_orientation = geomSetup.angles[i],
            part_offset = geomSetup.offsets[i],
            part_centre = self.cadPartCentre, #TODO! This probably needs changing
            srcToObjDist = sod,
            camera_elevation=0.0,
            camera_yaw=0.0,
            camera_roll=-90.0,
            vert_offset= geomSetup.axisOffs
        ) # vert offset because we've rotated camera 90 degrees
        thsSupplied = (thetas is not None)
        transGenKwargs['thetas' if thsSupplied else 'N'] = thetas if thsSupplied else N
        ## If thetas are given, use turntableAnglesOffsetsPositions, if N is supplied, do a 'Sweep' and figure out where thetas should be
        engArgOffsFun = transGen.turntableAnglesOffsetsPositions if thsSupplied else transGen.turntableAnglesOffsetsSweep
        engAngs, engOffs = engArgOffsFun(**transGenKwargs)
        return engAngs, engOffs, hfov

    def _calcFov(self, sdd):
        # padFactor increases effective det size from actual physical size
        padFactor = self.xres * 1.0 / ( self.xres - 2*self._padding ) # will be ever so slightly bigger than 1
        hfov_half = np.arctan(self.detSize[0] * padFactor /sdd)
        return np.rad2deg(hfov_half*2.0)

    def _trimPadding(self, arr):
        p = self._padding
        return arr[p:-p,p:-p] if (arr.ndim == 2) else arr[:,p:-p,p:-p]


class CoordPixelHitCalc(_EngineInteractor):
    '''
    Gets hit points for coords of interest
    '''
    def __init__(
            self,
            simSetup,
            geomSetup
        ):
        stlfile = simSetup.getSingleSetup(0).cadpaths[0]
        self._padding = 1 # padding the engine output is a good idea, as sometimes the edge values can be erratic
        self.detSize = simSetup.detSize
        self.detShape = simSetup.detShape
        self.xres, self.yres = [s + 2*self._padding for s in self.detShape]
        self.defaultArgs = {'sod':254.0, 'sdd':1145.0}
        self.cadPartCentre = transformations.Transformations.getCentreOfSTL(stlfile)
        self.geomSetup = geomSetup.getSingleSetup(0)
    
    def getHits(
            self,
            coords, 
            thetas = None,
            N = None
        ):
        engAngs, engOffs, hfov = self._getEngAngOffsFov(thetas, N, self.geomSetup)
        outs = engine.rays.coordsToPixelHit(
            "",
            self.xres,
            self.yres,
            hfov,
            np.array(engAngs),
            np.array(engOffs),
            np.atleast_2d(coords)
        )
        ##TODO! investigate potential mem leak?
        outCopy = outs.copy()
        del outs
        return outCopy
    
        
class TurntableMatpath(_EngineInteractor):
    '''
    Calculates material paths 
    '''
    def __init__(
            self,
            simSetup,                   # SimSetup object
            geomSetup = GeomSetup(),
        ):
        ''''''
        self.cadpaths = [simSetup.cadpaths] if isinstance(simSetup.cadpaths,str) else simSetup.cadpaths
        self.nMesh = len(self.cadpaths)
        self.cadPartCentre = transformations.Transformations.getCentreOfSTL(self.cadpaths[0]) # .. reference system to first cad
        self._padding = 1 # padding the engine output is a good idea, as sometimes the edge values can be erratic
        self.xres, self.yres = [s + 2*self._padding for s in simSetup.detShape]
        self.geomSetup = geomSetup
        self.engKwargs = dict( 
            filenames = self.cadpaths,
            xres = self.xres,
            yres = self.yres, 
            angles = self._reshapeDefaults2D(geomSetup.angles, self.nMesh, 'angles'),
            offsets = self._reshapeDefaults2D(geomSetup.offsets, self.nMesh, 'offsets'),
            scales = self._reshapeDefaults2D(simSetup.scales, self.nMesh, 'scales'),
            densities = self._reshapeDefaults1D(simSetup.densities, self.nMesh, 'densities'),
            flipnorms = self._reshapeDefaults1D(simSetup.flipnorms, self.nMesh, 'flipnorms') 
        )
        self.eng = MPEngObject(self.engKwargs)
        self.detSize = simSetup.detSize
        self.simSetup = simSetup

    def getMatPathImgs(
            self,
            thetas = None,
            N = None,
            geomSetup = GeomSetup(),
            firstLastDuplication = False,
            nThreads = 1,
            rois = None,
        ):
        '''generates configurations for args for calc... a configuration is any combination of geometrical param'''
        engAngs, engOffs, hfov = self._getEngAngOffsFov(thetas, N, geomSetup)
        bltrs = None if (rois is None) else self._rois2bltrs(rois)
        if (nThreads == 1):
            slices = None if (rois is None) else self._paddedSlices(rois)
            imgs = self.eng(hfov, engAngs, engOffs, bltrs, slices)
        else:
            # portion out lists... indices must be [threadNum][cadNum][...]
            portAngs = portionOutList(engAngs,nThreads)
            portOffs = portionOutList(engOffs,nThreads)
            portROIs = [None]*nThreads if (rois is None) else portionOutList(bltrs,nThreads)
            portSlices = [None]*nThreads if (rois is None) else portionOutList(self._paddedSlices(rois),nThreads)           
            portImgs = joblib.Parallel(n_jobs =nThreads)(
                       joblib.delayed(MPEngObject._para)(self.engKwargs,hfov,pAngs,pOffs,pRois,pSlices)
                       for pAngs,pOffs,pRois,pSlices in zip(portAngs,portOffs,portROIs,portSlices))
            imgs = np.concatenate(portImgs, axis = 0)
            del portImgs
            gc.collect()
        # Duplicated first as last if requred
        if firstLastDuplication:
            imgs = np.concatenate((imgs,imgs[0,None]),axis=0)            
        outs = self._trimPadding(imgs)
        return outs
    
    def _reshapeDefaults1D(self, arg, N, name):
        '''helper function for formatting inputs'''
        return _reshapeDefaults1D(arg, N, name) ## TODO! Refactor properly

    def _reshapeDefaults2D(self, arg, N, name='arg'):
        '''helper function for formatting inputs'''
        return _reshapeDefaults2D(arg, N, name) ## TODO! Refactor properly
    
    def _rois2bltrs(self, rois):
        '''Converts stack of pythonic roi slices to c-esque (top,left, bottom, right) arrays'''
        bltrs = np.zeros((len(rois), 4))
        for iShot, roi in enumerate(rois):
            yslice, xslice = roi
            b = np.maximum(yslice.start - 2*self._padding, 0)
            l = np.maximum(xslice.start - 2*self._padding, 0)
            t = np.minimum(yslice.stop + 2*self._padding, self.yres)
            r = np.minimum(xslice.stop + 2*self._padding, self.xres)
            bltrs[iShot] = np.array([b,l,t,r])
        return bltrs           

    def _paddedSlices(self, rois):
        return [tuple([slice(sl.start, sl.stop + 2*self._padding) for sl in roi]) for roi in rois]            
        

class RadiographSim(object):
    def __init__(self, simSetup, geomSetup = GeomSetup(), mpgsObjKwargs={}, projdir=None, noisy = False):
        self.ttmp = TurntableMatpath(simSetup, geomSetup)              # supplies material paths
        # Check mpgsObjKwargs to see if we have everything we need to map greyscales...
        mpgsObjKwargs = {} if (mpgsObjKwargs is None) else mpgsObjKwargs ##TODO! fix, probably
        _mustGenerate = ('mappingKwargs' not in mpgsObjKwargs.keys()) or (mpgsObjKwargs['mappingKwargs'] is None)
        _mustLoadToGenerate = (('mp' not in mpgsObjKwargs.keys()) and ('gs_target' not in mpgsObjKwargs.keys()))
        if (_mustGenerate and _mustLoadToGenerate):
            # If we have to fit mapping but don't have mp and gs_target... we get sim and ref.
            assert (projdir is not None),'To fit greyscale mapping, projdir is required'
            sim0 = self.ttmp.getMatPathImgs(thetas = [0.0])[0]
            ref0 = imread(getAllFiles(projdir)[0])
            mpgsObjKwargs.update({'mp':sim0, 'gs_target':ref0})
        self.mpgs = MatpathGreyscaleMapping(**mpgsObjKwargs)    # supplies mapping function
        self._nanDetections = []
        self.noisy = noisy
        
    def get(
            self,
            thetas,
            geomSetup = GeomSetup(),
            nThreads = 1,
            firstLastDuplication = False,
            mappingKwargs = None,
            blur = 0,
            rois = None,
            normalise = True,
            bitDepthReduction = np.float16,     # rounding errors due to bitDepth reduction is intentional
            noggin = True,
            noisy = 0,
        ):
        '''Generate radiograph'''
        mps = self.ttmp.getMatPathImgs(thetas, rois = rois, geomSetup = geomSetup, nThreads=nThreads)
        if np.isnan(mps.sum()): mps = self._fixNans(mps, geomSetup, thetas)
                    
        try:
            mapped = self.mpgs.map(mps, mappingKwargs)
            mpRange = (0.0,np.inf)*np.ones(2)
            brightVal, darkVal = self.mpgs.map(mpRange, mappingKwargs)
                
            if noggin:
                
        

                detShape = self.ttmp.simSetup.detShape
                pixSize = np.mean(np.array(self.ttmp.detSize)/detShape)*2.0
                sdd = self.ttmp.geomSetup.sdd
                N_avg_max = 1
                brightImg = poisson.getPhotonMap(detShape, pixSize, sdd, N_avg_max)/N_avg_max ##TODO: optimise
                
                if not (rois is None):
                    brightImg = np.array([brightImg[r] for r in rois])
                
                if noisy:
                    photonCounts = noisy*(mapped - darkVal)/(brightVal-darkVal)*brightImg
                    print("printing",photonCounts.max(), photonCounts.min(),photonCounts.shape)
                    from time import time as time
                    print("Starting rando")
                    t0 = time()
                    photonCounts = np.random.poisson(photonCounts)
                    print("End rando", time()-t0)
#                    sims = poisson.getNoisy2(photonCounts)*((brightVal-darkVal)/noisy) + darkVal
                    sims = photonCounts*((brightVal-darkVal)/noisy) + darkVal
                    nLevels = int(noisy + 0.5) # integer photon numbers
                    sims = self._nLevels(sims, darkVal, brightVal, nLevels)
                else:
                    sims = (mapped - darkVal)*brightImg + darkVal

            else:
                sims = mapped
            
            if normalise:
                sims = darkVal + (self._clampToDtype(sims-darkVal, bitDepthReduction) / self._clampToDtype(brightImg, bitDepthReduction)).astype(np.float64)
            else:
                sims = self._clampToDtype(sims, bitDepthReduction).astype(np.float64)
                
            
        except Exception as e:
            print("\nERROR IN MAP")
            import pickle
            data = pickle.dumps(dict(
                    mappingKwargs = mappingKwargs,
                    mps = mps,
                    defaultMappingKwargs = self.mpgs._mappingKwargs,
                    rois = rois
                    ))
            with open("error.pkl",'wb') as f:
                f.write(data)
            raise(e)
        sims = np.array([scipy.ndimage.gaussian_filter(s,blur) for s in sims])
        print("nancount:",np.isnan(sims).sum())
        return sims
    
    def _fixNans(self, mps, geomSetup, thetas): #TODO! ideally, I wouldn't have to fix this here...
        '''Very, very rarely a pixel or two glitches out, this fills in the holes.'''
        nans = np.isnan(mps)
        self._nanDetections.append([geomSetup, nans.sum(),thetas])
        for i in range(mps.shape[0]):
            # Fix ith mp img with median_filter
            while (nans[i].sum()):
                mask = nans[i]
                mps[i][mask] = scipy.ndimage.median_filter(mps[i],3)[mask]
                nans[i] = np.isnan(mps[i])
        return mps
    
    def _nLevels(self, img, imin, imax, n):
        '''Restricts dataset to n levels... useful if digitisation limited by photon count'''
        ispan = imax - imin
        img_nLevels = np.round((img-imin)*(n/ispan))*(ispan/n) + imin
        return img_nLevels
    
    def _clampToDtype(self, arr, dtype):
        info = np.finfo(dtype)
        return np.minimum(np.maximum(arr, info.min), info.max).astype(dtype)
        