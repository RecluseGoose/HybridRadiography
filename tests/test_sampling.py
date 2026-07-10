# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 02:24:12 2019

@author: robert.culver
"""
import numpy as np
from sampling.samplers import DefectVoxSampler, DefectRadSampler
from simulation.engine_interface import GeomSetup, SimSetup
 
def test_sampling():
    cadfile = "D:/testdata/artist_placation2.stl"
    defectfile = "D:/testdata/cuboid.stl"
    voxfile = "D:/testdata/eroded.npy"  
    angs = np.array([ 1.6166965 ,  5.06288025, -0.46963508])
    offs = np.array([ -4.15604287, -29.33219174,   1.90748051])
    sod = 253.03271016899586
    sdd =1137.2105858471873
    defectSize = np.array([.15,.15,0.3])*3.0
    thetas = np.linspace(0,300,10)
    detShape = (1000,1000)
    detSize = (200.0,200.0)
    boundary = 20
    
    geomSetup = GeomSetup(angs, offs, sod, sdd)
    simSetup = SimSetup( cadpaths = [cadfile, defectfile], detShape = detShape, detSize = detSize)
    mappingKwargs = {'bgVal': 60458.0590116136,
                     'bgThreshVal': 0.0001,
                     'lam': 0.6041077877030052,
                     'offs': 4939.076571656569,
                     'ampl': 41699.92895592637}
    mpgsObjKwargs = {'mappingKwargs': mappingKwargs}

    drs = DefectRadSampler(simSetup, mpgsObjKwargs, geomSetup)
    dvs = DefectVoxSampler(simSetup, voxfile=voxfile,)
    
    allInds = dvs.sampleEvery(10)
    allCoordsXYZ = dvs.ijk2xyz(allInds)
    viableInds = allInds[drs.checkCoordInView(allCoordsXYZ, thetas = thetas)]
    ind = viableInds[174]
    coordXYZ = dvs.ijk2xyz(ind)                 # <--- this defeinitely has unpredicable behaviour #TODO!!
    print(coordXYZ)
    assert (np.isclose(coordXYZ,np.array([ -3.04568643,  -8.59359878, -16.37528781])).all())

    rois = drs.defectRois(coordXYZ, thetas, boundary)    
    expectedRois = [ (slice(878, 918, None), slice(572, 612, None)),
                     (slice(889, 929, None), slice(645, 685, None)),
                     (slice(904, 944, None), slice(668, 708, None)),
                     (slice(920, 960, None), slice(627, 667, None)),
                     (slice(929, 969, None), slice(533, 573, None)),
                     (slice(929, 969, None), slice(417, 457, None)),
                     (slice(919, 959, None), slice(325, 365, None)),
                     (slice(903, 943, None), slice(290, 330, None)),
                     (slice(888, 928, None), slice(317, 357, None)),
                     (slice(877, 917, None), slice(393, 433, None)) ]
    print(rois)
    print(expectedRois)
    assert (rois == expectedRois)
    
    # Test patch roi and full rad based approaches...
    
    # rs0 is non-defective sampler
    rs0 = drs.makeRadSim(coordXYZ, defectSize, densities=[1.0,0.0])
    rads0 = rs0.get(thetas, nThreads = 2)
    patches0 = rs0.get(thetas, rois = rois, nThreads = 1)
    
    # rs1 is defective sampler
    rs1 = drs.makeRadSim(coordXYZ, defectSize, densities=[1.0, -1.0])
    rads1 = rs1.get(thetas, nThreads = 1)
    patches1 = rs1.get(thetas, rois = rois, nThreads = 2)
    
    # all of these should be the same...
    diffs0 = patches1 - patches0
    diffs1 = np.array([d[r] for d,r in zip((rads1 - rads0),rois)])
    diffs2 = np.array([p1 - r0[roi] for p1,r0,roi in zip(patches1,rads0,rois)])
    diffs3 = np.array([r1[roi] - p0 for r1,p0,roi in zip(rads1,patches0,rois)])
    assert diffs0.min() == 0.0
    print('diffs0.max() = ', diffs0.max())
    assert np.isclose(diffs0.max(),1935.7260499496624)
    assert np.all(diffs0 == diffs1)
    assert np.all(diffs0 == diffs2)
    assert np.all(diffs0 == diffs3)
    print('Sampling tested')

