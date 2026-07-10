# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 10:48:56 2019

@author: robert.culver
"""
import numpy as np
from scipy import ndimage

from simulation.engine_interface import RadiographSim, CoordPixelHitCalc, SimSetup, GeomSetup
from simulation.transformations import Transformations
from _utilities.voxelisation import stlToVox, polyDatToVox

class DefectVoxSampler(object):
    '''Handles samplng of geometry'''
    def __init__(self, stlfile, voxfile=None, vox = None, spacing=None, refToCentre=True, erodeIter = 5):
        assert (voxfile is not None) ^ (spacing is not None) ^ (vox is not None), 'Must specify either voxfile or spacing'
        if isinstance(stlfile, SimSetup): stlfile = stlfile.cadpaths[0]
        self.vox = vox if (vox is not None) else np.load(voxfile) if (voxfile is not None) else self._stlToVox(stlfile, vox_spacing=spacing, erodeIter=erodeIter)
        reader = Transformations.loadSTL(stlfile)
        self.bounds = Transformations.getBoundsOfSTL(reader=reader) # [x0,x1,y0,y1,z0,z1]
        self.centre = Transformations.getCentreOfSTL(reader=reader) if refToCentre else np.zeros(3)
        self.spacings = np.array([self.bounds[2*i+1] - self.bounds[2*i] for i in range(3)])*1.0/self.vox.shape
        self.origin = np.array([self.bounds[2*i] for i in range(3)])

    def _stlToVox(self, stlfile, vox_spacing, erodeIter):
        '''Generates vox from stl'''
        vox = stlToVox(stlfile, vox_spacing=vox_spacing)
        eroded = ndimage.morphology.binary_erosion(vox, iterations = erodeIter)
        return eroded

    def sampleEvery(self, samplingPeriod):
        '''Periodically samples the vox grid'''
        return periodicSamping(self.vox, samplingPeriod)
    
    def ijk2xyz(self, ijk):
        '''Converts index to cad coordinates relative to bounding box centre'''
        coords = (np.array(ijk) + 0.5*np.ones(3))*self.spacings + self.origin - self.centre
        return coords
    
    def xyz2ijk(self, xyz):
        coords = (xyz + self.centre - self.origin)/self.spacings - 0.5
        return coords

class DefectRadSampler(object):
    '''Generates RadiographSim object with defects seeded at appropriate positions'''
    def __init__( self,
                  simSetup,
                  mpgsObjKwargs,
                  geomSetup,
                  boundary = 20
                  ):
        self.cphc = CoordPixelHitCalc(simSetup = simSetup, geomSetup = geomSetup )  
        self.geomSetup = geomSetup
        self.simSetup = simSetup
        self.mpgsObjKwargs = mpgsObjKwargs
        self.boundary = boundary
    
    def checkCoordInView(self, coordsXYZ, thetas = None, N = None): 
        out = self.cphc.getHits(coordsXYZ, thetas = thetas, N = N)
        ##TODO!!! 
        # There's padding on the cphc.xres (actual used in calc), but not on the cphc.detShape (not sure what this is used for)
        # is padding treated appropriately on the output of cphc? do we need to subtract / add the padding afterwards?
        # does padding need to be treated, or are coords only used in the padded system?
#        inView = ((out >= 0)*(out < self.cphc.detShape)).all((0,2))
        inView = ((out >= self.cphc._padding)*(out < (np.array(self.cphc.detShape) + 2*self.cphc._padding))).all((0,2))
        return inView
    
    def _xyzToScene(self, coordXYZ):
        transf = Transformations()
        i = 0
        mat = transf.transl(self.geomSetup.offsets)@transf.rotabout(self.geomSetup.angles[i],np.zeros(3))
        coord = (mat@np.hstack((coordXYZ,1)))[:-1]
        return coord
    
    def defectRois(self, coordXYZ, thetas, boundary):
        #TODO! Pretty sure something here is bugged
        out = self.cphc.getHits(np.array([coordXYZ]), thetas = thetas) 
        hits = np.abs(out- np.array([0,self.cphc.detShape[0]])).astype(int)
        xstarts = np.array([hit[0][0]-boundary for hit in hits])
        ystarts = np.array([hit[0][1]-boundary for hit in hits])
        xstops = np.array([hit[0][0]+boundary for hit in hits])
        ystops = np.array([hit[0][1]+boundary for hit in hits])
        assert (xstarts > -boundary).all(), 'defect offscreen, case 0'
        assert (ystarts > -boundary).all(), 'defect offscreen, case 1'
#        assert (xstops <= (self.cphc.detShape[0] - 1 + boundary)).all(), 'defect offscreen, case 2'
        assert (ystops <= (self.cphc.detShape[1] - 1 + boundary)).all(), 'defect offscreen, case 3'
        # shift anything that needs shifting
        for i in range(len(hits)):
            if xstarts[i] < 0:
                xshift = -xstarts[i]
                xstops[i] += xshift
                xstarts[i] += xshift
            if ystarts[i] < 0:
                yshift = -ystarts[i]
                ystops[i] += yshift
                ystarts[i] += yshift
            if xstops[i] >= self.cphc.detShape[0]:
                xshift = (xstops[i] - self.cphc.detShape[0] + 1)
                xstarts[i] -= xshift
                xstops[i] -= xshift
                assert(xstarts[i] >=0),'boundary too broad'
            if ystops[i] >= self.cphc.detShape[1]:
                yshift = (ystops[i] - self.cphc.detShape[1] + 1)
                ystarts[i] -= yshift
                ystops[i] -= yshift
                assert(ystarts[i] >=0),'boundary too broad'
        # xstarts, xstops, ystarts, and ystops are index numbers... need to add 1 to stop to make slice ranges work (eg. slice(0,i) will exclude ith element).
        rois = [tuple([slice(x0,x1+1),slice(y0,y1+1)]) for x0,x1,y0,y1 in zip(xstarts,xstops,ystarts, ystops)]
        return rois
    
    def makeRadSim(self, coordXYZ, defectSize, densities = [1.0,-1.0], flipnorms = [0, 0], defectcad = None):
        assert (defectcad is not None) ^ (len(self.simSetup.cadpaths) == 2), 'Not enough cads, must have base cad and defect cad'
        # The source of all misery....
        cads = self.simSetup.cadpaths if (len(self.simSetup.cadpaths) == 2) else self.simSetup.cadpaths + [defectcad]
        simSetup = SimSetup(
            cads,
            self.simSetup.detSize,
            self.simSetup.detShape,
            densities = densities,
            scales = np.vstack((np.ones(3), defectSize)),
            flipnorms = flipnorms
        )
        newGeom = GeomSetup(
            angles = np.repeat(self.geomSetup.angles, 2, axis =0),
            offsets = np.vstack((self.geomSetup.offsets, self._xyzToScene(coordXYZ))),
            sod = self.geomSetup.sod,
            sdd = self.geomSetup.sdd,
            axisOffs = self.geomSetup.axisOffs
        )
        return RadiographSim(simSetup, newGeom, self.mpgsObjKwargs)  
    

class DefectReconSampler(object):
    '''For a given setup, converts indices to reconstructed volume ROIs'''
    def __init__(self, voxelSize, geomSetup, simSetup, vox=None, voxfile=None):
        assert np.shape(geomSetup.angles) == (1,3), 'angles input must be 1D'
        assert np.shape(geomSetup.offsets) == (1,3), 'offset input must be 1D'
        angs = geomSetup.angles[0]
        offs = geomSetup.offsets[0]
        stlfile =simSetup.cadpaths[0]        
        self.detShape = simSetup.detShape
        self.voxelSize = voxelSize
        self.invPixSize = 1.0/voxelSize
        t = Transformations()        
        self.translMat = t.transl(offs)@t.rot(angs)
        self.dvs = DefectVoxSampler(stlfile, vox=vox, voxfile=voxfile)
        self.voxShape = [self.detShape[0],self.detShape[1],self.detShape[0]]
        self.voxSize = self.voxelSize*np.array(self.voxShape)
        self.geomSetup = geomSetup
        self.simSetup = simSetup
        
    def inds2recon(self, inds):
        xyz = self.dvs.ijk2xyz(inds)
        voxInds = self.xyz2recon(xyz)
        return voxInds
    
    def xyz2recon(self, xyz):
        c = np.atleast_2d(xyz)
        augVec = np.concatenate((c,np.repeat([1],c.shape[0])[:, np.newaxis]), axis = 1)
        coordPlate = (self.translMat@augVec.T).T[:,:-1]
        voxInds = (coordPlate + 0.5*self.voxSize[np.newaxis,:])*self.invPixSize
        voxInds[:,1] = self.voxShape[1] - voxInds[:,1] # flip y
        voxInds[:,2] = self.voxShape[0] - voxInds[:,2] # flip z
        return voxInds if c.shape == xyz.shape else voxInds[0]
        
    def reconInd2roi(self, voxInds, padding = 20):
        slices = []
        for c,v in zip(voxInds, self.voxShape):
            c0 = max(c - padding, 0)
            c1 = min(c + padding + 1, v)
            s = slice(int(c0),int(c1))
            slices.append(s)
        return tuple(slices)
    
    def ind2roi(self, inds, padding = 20):
        voxInds = self.inds2recon(inds)
        roi = self.reconInd2roi(voxInds, padding)
        return roi
    
    def xyz2roi(self, xyz, padding = 20):
        voxInds = self.xyz2recon(xyz)
        roi = self.reconInd2roi(voxInds, padding)
        return roi
    
    def getDefectReconVoxHits(self, inds, defectSize, defectcad=None):
        '''returns coordinates of recon volume which are affected by defect'''
        # apply rotation to defect cad and voxellise... worry about scaling later in function
        stl = defectcad or self.simSetup.cadpaths[-1] # defect cad should be final in sequence
        transl = Transformations()
        stlPolyData = transl.loadSTL(stl).GetOutput()
        rotmat = np.vstack((np.hstack((self.translMat[:3,:3],[[0]]*3)),[[0,0,0,1]])) # isolate rotation
        normScale = np.array(defectSize)/np.min(defectSize)
        scale = np.vstack((np.hstack((normScale*np.identity(3),[[0]]*3)),[[0,0,0,1]]))
        stlPolyData = transl.applyTransformationMatrixToPolyData(stlPolyData, rotmat@scale)
        vox_spacing=0.1
        dvox = polyDatToVox(stlPolyData, vox_spacing=vox_spacing, printOutput=False)   
        # extract dvox coords
        coords = np.array(np.where(dvox)).T
        # scale to tuv about defect BB centre position
        extents = np.array(dvox.shape)*vox_spacing*np.min(defectSize)
        dcoordOffsets = extents/2
        dcoordsNorm = ((coords + 0.5)/(np.array(dvox.shape)))
        dcoords = dcoordsNorm*extents - dcoordOffsets
        # add defect offset to get true tuv coords
        defectCentrePos = self.dvs.ijk2xyz(inds)
        dcoords += defectCentrePos
        # convert to recon hits
        tuv = self.xyz2recon(dcoords)
        hits, cnts = np.unique(np.round(tuv).astype(int), axis=0, return_counts=True)
        cnts = cnts.astype(float)/cnts.sum()
        return hits, cnts
            

def faceSampling(vox, period = 20, depth = 3, direction = "neg", axis = 1):
    '''Does a periodic LoS analysis, basically'''
    # face sampling
    axis = 1       
    assert (direction in ["neg","pos"])
    axisSlice = slice(vox.shape[axis],0,-1) if (direction == "neg") else slice(0,vox.shape[axis], 1)
    slices = tuple([slice(0, vox.shape[i], period) if i!=axis else axisSlice for i in range(3)])
    inds = np.zeros_like(vox)
    cumulative = vox[slices].cumsum(axis = axis)  == depth
    padding = np.zeros([cumulative.shape[d] if d!= axis else 1 for d in range(3)])
    padded = np.concatenate((padding, cumulative), axis = axis)
    diffs = np.diff(padded, axis = axis) == axis  
    inds[slices] = diffs
    return np.array(np.where(inds)).T
    # periodic sampling

def periodicSamping(vox, period):
    '''Periodically samples the vox grid'''
    slices = tuple([np.arange(0,s,period) for s in vox.shape])
    grid = tuple(np.meshgrid(*slices))
    onVox = vox[grid]
    inds = np.array([g[onVox] for g in grid]).T
    return inds

def periodicFaceSampling(vox, period, depth, direction = "neg"):
    '''Periodically samples a face, as well as the bulk'''
    # get indices
    finds = faceSampling(vox, period, depth, direction)
    pinds = periodicSamping(vox, period)
    # generate boolean arrays
    farr = inds2array(vox, finds)
    parr = inds2array(vox, pinds)
    # bloat up the face samples, and nand with the periodic samples to avoid redundant samples
    fbloat = ndimage.morphology.binary_dilation(farr, iterations = int(0.50*period))
    pNotClose = (parr^fbloat)*parr
    both = farr + pNotClose
    return np.array(np.where(both)).T

def inds2array(vox, inds):
    '''Generates mask array from inds'''
    arr = np.zeros(vox.shape, dtype = bool) 
    arr[tuple([inds[:,i] for i in range(3)])] = True
    return arr
