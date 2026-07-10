# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 09:48:54 2019

@author: robert.culver
"""
import numpy as np

from hy_rad.hybrid_radiography import DefectSimulation
from tiles_results.rois import rois as filletSlices
from sampling.samplers import periodicFaceSampling

#%% Define filepaths
dumpdir = "d:/20190926_Defects_050_250/"
cadfile = "D:/testdata/cad_aligned.stl"
defectfile = "D:/testdata/defect.stl"
voxfile = "D:/testdata/eroded5_50.npy"
cleanfile = "d:/testdata/cleanprojs.npy"

#%% Modify eroded vox to ignore fillet regions
eroded = np.load(voxfile)
for slices in filletSlices:
    newSlices = tuple([slice(s.start*2,s.stop*2) for s in slices])
    eroded[newSlices] = False

# %% Format registration values
regDict = {'ax': 72.16588435048402,
 'ay': -6.985965706051154,
 'az': -0.3464760789792969,
 'ox': 0.48769597942763987,
 'oy': -32.169696828230514,
 'oz': -2.535939493718587,
 'sod': 254.17606070065628,
 'sdd': 1142.6250560187339,
 'axisOffs': 5.910892594118071e-05,
 'lam': 0.5465886213448862,
 'offs': 3947.6179165066105,
 'ampl': 40090.031420060455,
 'bgVal': 60616.048427299924}    
angles = np.array([ regDict['ax'], regDict['ay'], regDict['az']])
offsets = np.array([ regDict['ox'], regDict['oy'], regDict['oz']])
defectSize = np.array([0.25, 0.25, 0.25])
detShape = (1000,1000)
detSize = (200.0,200.0)
sod =  regDict['sod']
sdd = regDict['sdd']
axisOffs = 0.12
mappingKwargs = {'bgVal':  regDict['bgVal'],
                 'bgThreshVal': 0.0001,
                 'lam': regDict['lam'],
                 'offs': regDict['offs'],
                 'ampl': regDict['ampl']}
mpgsObjKwargs = {'mappingKwargs': mappingKwargs}
blur = np.array([0.75,0.75])
nProj = 3142

#%% Create defect simulation object
ds = DefectSimulation(cadfile = cadfile,
                     defectfile = defectfile,
                     cleanProjs = cleanfile,
                     angles = angles,
                     offsets = offsets,
                     detShape = detShape,
                     detSize = detSize,
                     sod = sod,
                     sdd = sdd,
                     mpgsObjKwargs = mpgsObjKwargs,
                     blur = blur,
                     nProj = nProj,
                     vox=eroded,
                     axisOffs = axisOffs
                     )

#%% Create viable samples, and start sampling and writing results
allInds = periodicFaceSampling(eroded, 30, 3)
viableInds = ds.keepViableInds(allInds)
ds.sampleInds(viableInds, defectSize, defectDensity = 0.6, nThreads = 20, dumpdir = dumpdir)
