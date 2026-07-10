# -*- coding: utf-8 -*-
"""
Created on Mon May  4 12:14:59 2020

@author: robert.culver
"""
import numpy as np
import pickle
import _utilities.img_manip as img_manip

from simulation.engine_interface import RadiographSim, SimSetup

with open("fits2.pkl","rb") as f:
    fit = pickle.load(f)

#%% Define filepaths
dumpdir = "d:/20200504_Defects/"            # output folder
cadfile = "D:/drama/geom/ara.stl"           # stl path
defectfile = "D:/testdata/defect.stl"       # stl path for defect
voxfile = "D:/drama/geom/ara0125_ero6.npy"  # eroded vox path
cleanfile = "D:/drama/geom/clean.npy"    # 
nProj = 3000


#%% SimSetup Obj
simSetup = SimSetup (
    cadpaths = cadfile,
    detSize = (200.0, 200.0),
    detShape = (1000,1000),
    scales = np.ones(3),
    densities = np.array([1]),
    flipnorms = np.array([0])
)
    
rs = RadiographSim ( 
    simSetup = simSetup,
    geomSetup = fit['geomSetup'],
    mpgsObjKwargs = fit['mpgsObjKwargs']
)

thetas = np.linspace(0.0,-360.0, nProj + 1)[:-1]

nBatches = 10
boundaries = np.round(np.linspace(0, nProj, nBatches)).astype(int)
starts = boundaries[:-1]
ends = boundaries[1:]

projs = []
for s,e in zip(starts, ends):
    print("Running {}:{}".format(s,e))
    projs.append(rs.get(thetas[s:e], noisy = 0, blur = 0.5))
    print("Finished {}:{}".format(s,e))
allProj = np.concatenate(projs[:], axis = 0)

outDir = "D:/drama/clean"
import os
if not os.path.exists(outDir): os.mkdir(outDir)
baseName = "JS_32296-11_15318_STEEL ARA POST MACH_NATHAN TURNER_"
allFiles = [os.path.join(outDir, baseName+"{:04d}.tif".format(i) )for i in range(len(allProj))]

nones = [img_manip.imwrite(f,p.astype(np.uint16)) for f,p in zip(allFiles,allProj)]
np.save(cleanfile, allProj)