# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 14:49:14 2019

@author: robert.culver
"""
import numpy as  np
import joblib
import scipy.interpolate as interp
import matplotlib.pyplot as plt

from optimisation.spuci_optimiser import SP_UCI
from metrics.registration_metrics import histSimilarity
from _utilities.img_manip import imresize
from _utilities.tools import portionOutList

class MatpathGreyscaleMapping(object):
    '''
    Class encapsulates:
        - Conversion of material path values to greyscales.
        - Greyscale offsets.
        - Greyscale scaling.
        - Inherent flatfielding
        
    For full tracability, mapping functions separated into:
        - _kwargsMethod(mp, gsTarget, **methodKwargs) method, which gets a set of kwargs for a given mapping method
        - _evalMethod(mp, **mappingKwargs) method, which executes mapping with kwargs
    
    Usage:
    
    # Setup
    >>> shape = (30,30)
    >>> np.random.seed(174)
    >>> mp = np.random.random(shape)
    >>> gs_target = np.random.random(shape)
    
    # Generate mpgs
    >>> mpgs = MatpathGreyscaleMapping(mp, gs_target, method = 'polyfit')
    
    # Use mpgs to map onto greyscale
    >>> gs = mpgs.map(mp)
    >>> gs.shape == mp.shape
    True
    >>> np.abs(gs - gs_target).sum() # should be small if fit is good
    219.2892058602539
    
    # Use mpgs to map new things
    >>> mp2 = np.random.random(shape)
    >>> gs2 = mpgs.map(mp2)
     
    # Can get mapping kwargs for tracability
    >>> mk = mpgs.getMappingKwargs()
    >>> mk.keys()
    ['pfit']
    >>> print(', '.join(map(lambda x: '{:.5f}'.format(x), mk['pfit'])))
    2.55766, -7.19605, 7.13239, -2.88585, 0.37066, 0.50300
    
    >>> mpgs2 = MatpathGreyscaleMapping(mp, gs_target, mappingKwargs = mk, method = 'polyfit')
    >>> gs3 = mpgs.map(mp)
    >>> np.all(gs == gs3) # should replicate original fit
    True
    '''
    def __init__(self, mp = None, gs_target = None, method = 'expfit', methodKwargs = {}, mappingKwargs = None):
        self.method = method
        self._map = self._getEvalFun(method)
        assert (mappingKwargs is not None) ^ (gs_target is not None), 'Must specify either mappingKwargs or gs_target'
        self._mappingKwargs = mappingKwargs if mappingKwargs else self._getKwargs(mp, gs_target, method, methodKwargs)
        
    def map(self, mp, mappingKwargs = None):
        '''Placeholder for mapping function. This is overwritten during __init__'''
        mappingKwargs = mappingKwargs if (mappingKwargs is not None) else self._mappingKwargs
        nThreads = 1 # Hard coded to 1 for now... parallelising this makes no improvement from what I can tell.
        if (nThreads == 1):
            imgs = self._map(mp, **mappingKwargs)
        else:
            # portion out lists... indices must be [threadNum][cadNum][...]
            portMP = portionOutList(mp,nThreads)
            portImgs = joblib.Parallel(n_jobs = nThreads)(
                       joblib.delayed(self._map)(mp_ , **mappingKwargs)
                       for mp_ in portMP)
            imgs = np.concatenate(portImgs, axis = 0)
        return imgs
        
    
    def plot(self, mp, gs_target, method = 'polyfit', methodKwargs = {}, mappingKwargs = None):
        _map = self._getEvalFun(method)
        _mappingKwargs = mappingKwargs if mappingKwargs else self._getKwargs(mp, gs_target, method, methodKwargs)
        f = plt.figure()
        x1 = np.linspace(mp.min(),mp.max(), 200)
        y1 = _map(x1,**_mappingKwargs)
        x2 = mp.flatten()
        y2 = gs_target.flatten()
        nPts = np.min((40000,len(x2))) # points used for plotting
        inds = (len(x2)*np.random.random(nPts)).astype(np.int64)
        plt.plot(x2[inds],y2[inds],'.k')
        plt.plot(x1,y1)
        f.show()
        return f
    
    def getMappingKwargs(self):
        '''Returns the mappingKwargs being used in map'''
        return self._mappingKwargs
    
    def _getEvalFun(self, method):
        '''Used to set mapping function based on method'''
        mappingMethods = {'polyfit' : self._evalPolyfit, 'expfit' : self._evalExpfit, 'akima' : self._evalAkima}
        keys = mappingMethods.keys()
        assert (method in keys),'Specified method \'{}\' not recognised, {}'.format(method, keys)
        return mappingMethods[method]
            
    def _getKwargs(self, mp, gs_target, method, methodKwargs):
        '''Used to set mapping kwargs based on method and inputs'''
        kwargMethods = {'polyfit' : self._kwargsPolyfit, 'expfit' : self._kwargsExpfit, 'akima' : self._kwargsAkima}
        keys = kwargMethods.keys()
        assert (method in keys),'Specified method \'{}\' not recognised, {}'.format(method, keys)
        return kwargMethods[method](mp, gs_target,**methodKwargs)
    
    def _evalPolyfit(self, mp, pfit):
        '''Evaluates a polyfit'''
        return np.polyval(pfit, mp.flatten()).reshape(mp.shape)
    
    def _kwargsPolyfit(self, mp, gs_target, order = 10):
        '''Generates kwargs compatible with _evalPolyfit'''
        return dict(pfit = np.polyfit(mp.flatten(), gs_target.flatten(), order))
    
    def _evalExpfit(self, mp, bgVal, bgThreshVal, lam,offs, ampl):
        '''Evaluates an exponential fit'''
        return ((ampl-offs)*(np.exp(-lam*mp)) + offs)*(mp>bgThreshVal) + bgVal*(mp<=bgThreshVal)
    
    def _kwargsExpfit(self, mp, gs_target, expBounds = [[0.0,5.0],[0.0,3e4],[4e4,1e5]], verbose = True, spuciKwargs={}):
        '''Fits exponential fit to match histograms'''
        counts,bins = np.histogram(gs_target, bins =1000)
        imax = np.argmax(counts)
        bgVal = np.mean(bins[imax:imax+1])
        bgThreshVal= 1e-3
        expObj = lambda args: (histSimilarity(self._evalExpfit(mp, bgVal, bgThreshVal,*args), gs_target.astype(np.float32)), )
        expOpt = SP_UCI(expObj, expBounds)
        if verbose: print("Optimising greyscale mapping...")
        if ('maxEvals' not in spuciKwargs.keys()): spuciKwargs['maxEvals'] = 3000
        expOpt.optimise(verbose = verbose, **spuciKwargs)
        lam,offs, ampl = expOpt.getBest()
        return dict(bgVal = bgVal, bgThreshVal=bgThreshVal, lam=lam ,offs=offs, ampl=ampl)       
    
    def _evalAkima(self, mp, akimaArgs):
        '''Evaluates based on an akima interpolation'''
        # Heavy use of overloading here...
        hasSavedArgs = hasattr(self, "_akimaArgsPrevious")
        argsMatchSaved = hasSavedArgs and (len(self._akimaArgsPrevious) == len(akimaArgs)) and np.all(self._akimaArgsPrevious == akimaArgs)
        needsInterpUpdate = (not hasSavedArgs) or (not argsMatchSaved)
        # Update interp and args if required by checks
        if needsInterpUpdate:
            self._akimaArgsPrevious = akimaArgs
            self._akimaInterpFun = self._buildAkima(akimaArgs)
        # perform interpolation
        outs = self._akimaInterpFun(mp)
        outs[np.isnan(outs)] = np.nanmin(outs)
        return outs
    
    def _buildAkima(self, akimaArgs):
        '''Converts akima args into an akima interpolator'''
        # reshape 1D input into x and y values
        x,y = akimaArgs.reshape(-1,2).T
        # take unique values only
        _, iunique = np.unique(x, return_index = True)
        x = x[iunique]
        y = y[iunique]
        # sort for ascending x and descending y
        x = x[x.argsort()]
        y = y[y.argsort()[::-1]]
        # build interpolator
        interpolator = interp.Akima1DInterpolator(x,y)
        return interpolator
    
    def _kwargsAkima(self, mp, gs_target, nPoints = 20, verbose = True, spuciKwargs={}):
        '''Generates kwargs for akima interpolation'''
        assert nPoints > 2, 'Must have more than two points for interpolation'
        mpMax = mp.max()
        # get a first guess by fitting to an exp fit...
        xbins = np.linspace(0.0, mpMax, (nPoints-1) + 1)
        xguess = [(x0 + x1)*0.5 for x0, x1 in zip(xbins[:-1],xbins[1:])]
        gsflat = (gs_target if (gs_target.shape == mp.shape) else imresize(gs_target, mp.shape[0], mp.shape[1])).flatten()
        mpflat = mp.flatten()
        yguess = [np.hstack((gsflat[(x0<mpflat)*(mpflat<x1)],[0.0])).mean() for x0, x1 in zip(xbins[:-1],xbins[1:])]
        # add on zero point
        xguess = [0.0] + xguess
        yguess = [np.hstack((gsflat[(mpflat<0.01*mpMax)],[0.0])).mean()] + yguess
        firstGuess = np.vstack((xguess, yguess)).T.flatten()
        argsToBuild = firstGuess
        return dict(akimaArgs = argsToBuild)
