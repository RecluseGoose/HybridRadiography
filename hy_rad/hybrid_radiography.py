# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 07:40:25 2019

@author: robert.culver
"""
import os
import numpy as np
import pickle
from time import time as time
from scipy.ndimage import gaussian_filter

#from reconstruction.recon import NikonRecon
from _utilities.img_manip import imread, imwrite, getAllFiles
from _utilities.tools import portionOutList
from sampling.samplers import DefectVoxSampler, DefectRadSampler
from simulation.engine_interface import SimSetup, GeomSetup

class DefectSimulation(object):
    def __init__(self,
                 simSetup,
                 geomSetup,
                 cleanProjs,    # a filename or numpy array to an array containing clean, simulated projections. Generated if not exist
                 mpgsObjKwargs, # mapping object keyword args from registration
                 blur,          # blur from registration
                 nProj,         # number of total (unique) projections in set
                 vox,            # vox used for sampling, should usually be an eroded version of the original vox
                 ):
        self.nProj = nProj
#        self.detShape = detShape
        self.simSetup = simSetup
        self.geomSetup = geomSetup
        self.thetas = np.linspace(0,-360,nProj + 1)[:-1]
        self.blur = blur
        # DefectVoxSampler handles the sampling of the vox (index based sampling) and converts ijk in vox to xyz in cad
        stlfile = simSetup.cadpaths[0]
        self.dvs = DefectVoxSampler(stlfile=stlfile, vox=vox)
        # DefectRadSampler handles the generation of RadiographSim scene setups for a given defect xyz (cad) coordinate
        self.drs = DefectRadSampler( self.simSetup.getSingleSetup(), mpgsObjKwargs, geomSetup )
        self.cleanProjs = self._getCleanProjs(cleanProjs) # defect free simulated projections
    
    def _getCleanProjs(self, cleanProjs):
        if isinstance(cleanProjs, np.ndarray):
            arr = cleanProjs
        if isinstance(cleanProjs, str):
            if os.path.exists(cleanProjs):
                print('Loading clean projections from file')
                arr = np.load(cleanProjs)
        else:
            print('Generating clean projections')
            arr = self.generateCleanSims(cleanProjs)
        return arr
    
    def generateCleanSims(self, cleanfile, nThreads = 10, noisy = False):
        '''Generates a clean set of simulated projections'''
        coordXYZ = self.dvs.ijk2xyz([0,0,0])    # Will be ignored; defect density set for ignore
        defectSize = np.ones(3).astype(np.float)# Will be ignored; defect density set for ignore
        rs1 = self.drs.makeRadSim(coordXYZ, defectSize, densities=[1.0,0.0], defectcad=self.simSetup.cadpaths[-1])
        cleanProjs = np.zeros((self.nProj,self.simSetup.detShape[0],self.simSetup.detShape[1]))
        chunks = np.linspace(0,self.nProj,10).astype(int)
        for i0,i1 in zip(chunks[:-1],chunks[1:]):
            cleanProjs[i0:i1,:,:] = rs1.get(self.thetas[i0:i1], geomSetup = GeomSetup(axisOffs=self.geomSetup.axisOffs), nThreads=nThreads, blur = self.blur, noisy = noisy)
#            cleanProjs[i0:i1,:,:] = rs1.get(self.thetas[i0:i1], geomSetup=self.geomSetup, blur = self.blur)
        if cleanfile:
            np.save(cleanfile, cleanProjs)
        return cleanProjs
    
    def sampleEveryViable(self, period):
        '''Samples periodically and generates viable sample indices for vox'''
        allInds = self.dvs.sampleEvery(period)
        return self.keepViableInds(allInds)
        
    def keepViableInds(self, allInds):
        allCoordsXYZ = self.dvs.ijk2xyz(allInds)
        viableInds = allInds[self.drs.checkCoordInView(allCoordsXYZ, thetas = self.thetas)]
        return viableInds
    
    def sampleIndBatch(
        self,
        viableInds,              # list of vox indices for sampling
        defectSize,
        defectDensity = 0.0,     # density of defects. Should be from 0-1. For 0.6 packing ratio, use 0.6 here.
        nThreads = 20,
        dumpdir = "d:/resize/",
        roiBoundary = 20,
        ):
        '''Chugs through viable inds and saves 2D projection results to temporary location'''
        if not os.path.isdir(dumpdir): os.mkdir(dumpdir)
        for i,ind in enumerate(viableInds):
            t0 = time()
            dataToWrite = self.sampleInd(ind, defectSize, defectDensity, nThreads, roiBoundary)
            fn = "_".join(["{}".format(i) for i in ind]) + '.pkl'
            with open(os.path.join(dumpdir,fn),'wb') as f:
                f.write(pickle.dumps(dataToWrite))
            t1 = time()
            print("Finished ind {},  {}/{} in {}s".format(ind, i+1, len(viableInds),t1-t0))
            
    def sampleInd(
        self,
        ind,
        defectSize,
        defectDensity = 0.0,     # density of defects. Should be from 0-1. For 0.6 packing ratio, use 0.6 here.
        nThreads = 20,
        roiBoundary = 20,
        ):
        '''processes an ind and returns 2D projection diffs, 2D rois and ind'''
        coordXYZ = self.dvs.ijk2xyz(ind)
        print('attempt1: ',coordXYZ)
        coordXYZ = self.dvs.ijk2xyz(ind)
        print('attempt2: ',coordXYZ)
        rois = self.drs.defectRois(coordXYZ, self.thetas, roiBoundary) 
        rs0 = self.drs.makeRadSim(coordXYZ, defectSize, densities=[1.0, -1.0 + defectDensity], defectcad = self.simSetup.cadpaths[-1])
        pc = np.array([img[r] for r, img in zip(rois, self.cleanProjs)])
        pd = rs0.get(self.thetas, geomSetup = GeomSetup(axisOffs=self.geomSetup.axisOffs), nThreads=nThreads, rois = rois, blur = self.blur)
#        pd = rs0.get(self.thetas, geomSetup = self.geomSetup, nThreads = nThreads, rois = rois, blur = self.blur)
        diffs = pd-pc # diffs should be positive    
        print('writing defect')        
        return dict( diffs = diffs, rois = rois, ind = ind)#, pc = pc, pd = pd)
    
    def testInd(
        self,
        ind,
        defectSize,
        defectDensity = 0.0,     # density of defects. Should be from 0-1. For 0.6 packing ratio, use 0.6 here.
        nThreads = 5,
        roiBoundary = 20,
        skipSampling = 100,     # interval with which to skip samples
        ):
        '''produces 2D image stack for testing'''
        skipSamps = slice(None, None, skipSampling)
        coordXYZ = self.dvs.ijk2xyz(ind)
        rois = self.drs.defectRois(coordXYZ, self.thetas[skipSamps], roiBoundary)
        rs0 = self.drs.makeRadSim(coordXYZ, defectSize, densities=[1.0, -1.0 + defectDensity], defectcad = self.simSetup.cadpaths[-1])
        cleans = self.cleanProjs[skipSamps]
        pc = np.array([img[r] for r, img in zip(rois, cleans)])
        pd = rs0.get(self.thetas[skipSamps], geomSetup = GeomSetup(axisOffs=self.geomSetup.axisOffs), nThreads=nThreads, rois = rois, blur = self.blur)
#        pd = rs0.get(self.thetas, geomSetup = self.geomSetup, nThreads = nThreads, rois = rois, blur = self.blur)
        return pc, pd, rois, cleans
    