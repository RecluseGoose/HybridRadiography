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
from sampling.samplers import DefectVoxSampler, DefectRadSampler
from tiles_results.rois import rois as filletSlices

projdir = "d:/Data/32911_Top Half_RQ0548-08_08May19_2019_05_08_04_34_36/"
simdir =  "d:/Data/32911_Top Half_RQ0548-08_08May19_2019_05_08_04_34_36/sims"
dumpdir = "d:/defects/"
#
#try:
#    recon
#except:
#    recon = NikonRecon(projdir)

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

cadfile = "D:/testdata/cad_aligned.stl"
defectfile = "D:/testdata/defect.stl"
voxfile = "D:/testdata/eroded4.npy"

eroded = np.load(voxfile)
filletVox = np.zeros_like(eroded)
for slices in filletSlices:
    filletVox[slices] = eroded[slices]

angs = np.array([ regDict['ax'], regDict['ay'], regDict['az']])
offs = np.array([ regDict['ox'], regDict['oy'], regDict['oz']])
defectSize = np.array([0.2, 0.2, 0.2])
thetas = np.linspace(0,-360,3142 + 1)[:-1]
detShape = (1000,1000)
detSize = (200.0,200.0)
sod =  regDict['sod']
sdd = regDict['sdd']
boundary = 20

mappingKwargs = {'bgVal':  regDict['bgVal'],
                 'bgThreshVal': 0.0001,
                 'lam': regDict['lam'],
                 'offs': regDict['offs'],
                 'ampl': regDict['ampl']}
mpgsObjKwargs = {'mappingKwargs': mappingKwargs}
blur = np.array([0.3866146 , 0.94937065])

print('Making samplers')
dvs = DefectVoxSampler(cadfile, vox=filletVox)
drs = DefectRadSampler(cadfile, defectfile, angs, offs, detShape, detSize, sod, sdd, mpgsObjKwargs)

allInds = dvs.sampleEvery(7)
allCoordsXYZ = dvs.ijk2xyz(allInds)
viableInds = allInds[drs.checkCoordInView(allCoordsXYZ, thetas = thetas)]
viableInds = allInds[drs.checkCoordInView(allCoordsXYZ, thetas = thetas)]

#print('Loading projs')
#coordXYZ = dvs.ijk2xyz(viableInds[0])
#rs1 = drs.makeRadSim(coordXYZ, defectSize, densities=[1.0,0.0])
try:
    cleanProjs
except:
    cleanProjs = np.load("d:/testdata/cleanprojs.npy")
print('Projs loaded')

for i,ind in enumerate(viableInds):
    try:
        t0 = time()
        coordXYZ = dvs.ijk2xyz(ind)
        rois = drs.defectRois(coordXYZ, thetas, boundary)
        rs0 = drs.makeRadSim(coordXYZ, defectSize, densities=[1.0,-0.4])
        p0 = rs0.get(thetas, geomKwargs={'nThreads': 20}, rois = rois)
        pc = np.array([img[r] for r, img in zip(rois,cleanProjs)])
        diffs = np.array([gaussian_filter(pdef,0)-gaussian_filter(pclear,0) for pdef, pclear in zip(p0,pc)])
        defectData = dict( diffs = diffs, rois = rois, ind = ind)
        s = pickle.dumps(defectData)
        fn = "_".join(["{}".format(i) for i in ind]) + '.pkl'
        with open(os.path.join(dumpdir,fn),'wb') as f:
            f.write(s)
        t1 = time()
        print("Finished ind {},  {}/{} in {}s".format(ind, i, len(viableInds),t1-t0))
        if(diffs.min() != 0): print('dodgy diffs')
    except:
        print('ind failed', ind)
