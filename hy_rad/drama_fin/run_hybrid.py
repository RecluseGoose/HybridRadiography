# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 12:15:24 2020

@author: robert.culver
"""
import numpy as np
import os
import time

from sampling.samplers import periodicSamping
from hy_rad.hybrid_radiography import DefectSimulation
from hy_rad.drama_fin.patch_analysis import defectAnalysis, showDefects
import _utilities.img_manip as img_manip

tStart = time.time()

#%% ===========================================================================
#  Setup
# =============================================================================
hybrid = False
noise = True
blur = 0.5
nProj = 3000
period = 20
defectSize = np.array([0.4,0.4,0.4])
padding = 20

# =============================================================================
# More setup
# =============================================================================

projdir = r"D:/drama/resized" if hybrid else r"D:/drama/noisy"
dumpdir = "d:/20200527_noisy/"    # output folder
cadfile = "D:/drama/geom/ara_modified.stl"           # stl path
defectfile = "D:/testdata/defect.stl"       # stl path for defect
voxfile = "D:/drama/geom/ara0125_ero6_modified.npy"  # eroded vox path
cleanProjs = "D:/drama/clean.npy"           # non-defective

# Get geomSetup and mpgsObjKwargs
import pickle
with open("fits2.pkl",'rb') as f:
    regDict = pickle.load(f)
geomSetup = regDict['geomSetup']
mpgsObjKwargs = regDict['mpgsObjKwargs']
# Get SimSetup
from simulation.engine_interface import SimSetup
#defectSize = np.array([1.0, 1.0, 1.0])
detShape = (1000,1000)
detSize = (200.0,200.0)
simSetup = SimSetup(
    cadpaths=[cadfile, defectfile],
    detSize=detSize,
    detShape=detShape,
    densities = np.array([1]),
    flipnorms = np.array([0])
)


#%% ===========================================================================
# Generate non-defective projection stack
# =============================================================================

# Seed some defects
eroded = np.load(voxfile)
allInds = periodicSamping(eroded, period)[:]

ds = DefectSimulation (
    simSetup=simSetup,
    geomSetup=geomSetup,
    cleanProjs=None,
    mpgsObjKwargs=mpgsObjKwargs,
    blur = blur,
    nProj = nProj,
    vox = eroded
)

viableInds = ds.keepViableInds(allInds)
#    outOfView = np.array([a for a in allInds if not sum([np.all(v==a) for v in viableInds])])
#assert(False)
ds.sampleIndBatch(viableInds, defectSize, defectDensity = 0.0, nThreads = 20, dumpdir = dumpdir, roiBoundary=padding)

#%% ===========================================================================
# Write to projdir
# =============================================================================

def cast(x,dtype):
    info=np.iinfo(dtype)
    return np.maximum(np.minimum(x,62000),info.min).astype(dtype)

if not(hybrid):
    allProj = ds.generateCleanSims(None, noisy = noise)
    if not os.path.exists(projdir): os.mkdir(projdir)
    baseName = "JS_32296-11_15318_STEEL ARA POST MACH_NATHAN TURNER_"
    allFiles = [os.path.join(projdir, baseName+"{:04d}.tif".format(i) )for i in range(1,len(allProj)+1)]
    nones = [img_manip.imwrite(f,cast(p, np.uint16)) for f,p in zip(allFiles,allProj)]
    
#%% ===========================================================================
#  Analyse defects
# =============================================================================

conts = defectAnalysis(
    projdir,
    defectdir = dumpdir,
    simSetup = simSetup,
    geomSetup = geomSetup,
    vox = eroded,
    blur = blur,
)

#conts, outvol = defectAnalysis(
#    projdir,
#    defectdir = dumpdir,
#    simSetup = simSetup,
#    geomSetup = geomSetup,
#    vox = eroded,
#    blur = blur,
#    returnFullVox = True
#)

#d = "hybrid_rere"
#showDefects(conts, d, show=False)