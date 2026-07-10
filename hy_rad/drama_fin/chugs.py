# -*- coding: utf-8 -*-
"""
Created on Mon May 11 16:08:22 2020

@author: robert.culver
"""
import pickle
import numpy as np
import os
import scipy.interpolate as interp

from metrics.sei_detectability import indication_evaluation_single
from _utilities.img_manip import imwrite

outputDir = "D:/drama/output/output_{:04d}.png"

outOfViewInds = np.load("oov.npy")

with open("conts.pkl","rb") as f:
    conts = pickle.load(f)

inds = [] + outOfViewInds.tolist()
vals = [] + np.zeros((len(outOfViewInds),2)).tolist()

valMax = 200.0
valMin = 0

for i, (ind, vol1, vol2) in enumerate(conts):
    val = indication_evaluation_single(vol1,vol2)
    if (val[0] < valMax) and (val[0] > valMin):
        inds.append(ind)
        vals.append(val)
        print(i)
    else:
        print("ind {} failed".format(i))
    
interpVals = np.array(vals)
interpInds = np.array(inds)
metric = interpVals[:,0]**(2/3) + 5.0

vox = np.load("D:/drama/geom/ara0125.npy")

subvox = vox[:,:,:].astype(bool)
outVox = np.nan * np.logical_not(subvox)
coords = np.array(np.where(subvox)).T
interpvals = interp.griddata(interpInds, metric, coords, method='nearest')
outVox[tuple(tuple(c) for c in coords.T)] = interpvals


# remove nans for image writing
outVox2 = -1 * np.logical_not(subvox)
outVox2[tuple(tuple(c) for c in coords.T)] = interpvals

print('writing outputs')
[imwrite(os.path.join(outputDir.format(i)),s.astype(np.float32)) for i,s in enumerate(outVox2)]