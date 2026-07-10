# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 09:48:54 2019

@author: robert.culver
"""
import numpy as np
import matplotlib.pyplot as plt




#%% Create viable samples, and start sampling and writing results
#allInds = periodicSamping(eroded, 20)


def runSamples(
        simSetup,
        geomSetup,
        mpgsObjKwargs,
        voxfile,
        cleanProjs,
        defectSize = np.array([0.4, 0.4, 0.4]),
        dumpdir,
        blur,
        nProj,
        period
    ):
    eroded = np.load(voxfile)
    allInds = periodicSamping(eroded, period)

    ds = DefectSimulation (
        simSetup=simSetup,
        geomSetup=geomSetup,
        cleanProjs=cleanProjs,
        mpgsObjKwargs=mpgsObjKwargs,
        blur = blur,
        nProj = nProj,
        vox = eroded
    )

    viableInds = ds.keepViableInds(allInds)
#    outOfView = np.array([a for a in allInds if not sum([np.all(v==a) for v in viableInds])])
    ds.sampleIndBatch(viableInds, defectSize, defectDensity = 0.0, nThreads = 20, dumpdir = dumpdir, roiBoundary=20)
    