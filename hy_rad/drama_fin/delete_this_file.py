# -*- coding: utf-8 -*-
"""
Created on Thu May 21 11:15:53 2020

@author: robert.culver
"""

import numpy as np
import matplotlib.pyplot as plt
import pickle

from hy_rad.hybrid_radiography import DefectSimulation
from simulation.engine_interface import SimSetup
from sampling.samplers import periodicSamping

#%% Define filepaths
dumpdir = "d:/20200506_resized_defects/"            # output folder
cadfile = "D:/drama/geom/ara.stl"           # stl path
defectfile = "D:/testdata/defect.stl"       # stl path for defect
voxfile = "D:/drama/geom/ara0125_ero6.npy"  # eroded vox path
cleanProjs = "D:/drama/clean.npy"

#%% Load gubbins
eroded = np.load(voxfile)

with open("fits2.pkl",'rb') as f:
    regDict = pickle.load(f)

# %% Format registration values
geomSetup = regDict['geomSetup']
mpgsObjKwargs = regDict['mpgsObjKwargs']
mappingKwargs = regDict['mappingKwargs']

defectSize = np.array([0.4, 0.4, 0.4])
#defectSize = np.array([1.0, 1.0, 1.0])
detShape = (1000,1000)
detSize = (200.0,200.0)

simSetup = SimSetup(
    cadpaths=[cadfile],
    detSize=detSize,
    detShape=detShape,
    densities = np.array([1]),
    flipnorms = np.array([0])
)


import simulation.engine_interface as eng

rs = eng.RadiographSim(simSetup, geomSetup, mpgsObjKwargs)
rad1 = rs.get([100,120,130,140], noggin = False)[2]
rad2 = rs.get([100,120,130,140], normalise = True)[2]
rad3 = rs.get([100,120,130,140], normalise = True, noisy = True)[2]
print(rad1.mean(),rad1.max(),rad1.min(), rad1.sum())

plt.matshow(rad1, cmap = 'gray', vmin = 0, vmax = 65535)
plt.matshow(rad2, cmap = 'gray', vmin = 0, vmax = 65535)
plt.matshow(rad3, cmap = 'gray', vmin = 0, vmax = 65535)
#plt.matshow((rad1-rad2)/65535, cmap = 'bwr', vmin = -0.05, vmax = 0.05)

#52687.91589066019 62030.99878648319 13245.160087840452 52687915890.66019