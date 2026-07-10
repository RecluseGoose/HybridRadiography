# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 04:22:38 2019

@author: robert.culver
"""

#from metrics.detectability import DetectabilityMetric
from scipy import ndimage

try:
    vol0
except:    
    from reconstruction.recon import NikonRecon
    import matplotlib.pyplot as plt
    import pickle
    from time import time as time
    import numpy as np
    import scipy.ndimage as snd
    from scipy.ndimage import median_filter
    from _utilities.img_manip import imread, imwrite, imresize, getAllFiles
    import os
    
    from sampling.samplers import DefectReconSampler
    from simulation.transformations import Transformations
    
    
    geomKwargs = {'offsets': np.array([  0.48769598, -32.16969683,  -2.53593949]),
                  'angles': np.array([72.16588435, -6.98596571, -0.34647608]),
                  'detShape': (1000, 1000)}
    reconKwargs = dict(centre=-2.0, bhc = 0.4, streakCorrection = [0.0,0.4,5.0])
    #reconKwargs = dict(centre=-6.5, bhc = 0.4, streakCorrection = [0.0,0.4,5.0])
    projdir = "D:/resized"
    #projdir = "D:/defective"
#    defectdir="D:\\20190926_Defects_050_250\\transferred"
    defectdir = "C:/Users/robert.culver/main_body"
    cadfile = "D:/testdata/cad_aligned.stl"
    vox = np.load("D:/testdata/eroded5_50.npy")
    voxelSize = 0.0889232427777848
    recon = NikonRecon(projdir, **reconKwargs)
    print('doing initial recon')
    drs = DefectReconSampler(voxelSize, geomKwargs, cadfile, vox)
    vol0 = recon.calcVolume()
    print('finished recon')

padding = 50
#vals = {}
conts = []

files = os.listdir(defectdir)
assert(False)
for i,filename in enumerate(files):
    
    try:
        with open(os.path.join(defectdir,filename), "rb") as f:
            defect = pickle.load(f)
    except UnicodeDecodeError:
        print("Unicode error", filename)
        continue
    
    inds = defect['ind']
    diffs = defect['diffs']
    defectRois = defect['rois']
    
    if len(conts)>0 and np.all(inds == [c[0] for c in conts], axis = 1).sum():
        continue
    
    diffs2 = diffs.copy().astype(np.float32)
    diffs2[diffs<0] = ndimage.maximum_filter(diffs,3)[diffs<0]          # Fix glitches... very rare
    #diffs2 = np.array([gaussian_filter(d,postBlur) for d in diffs])
    t = 5
    modProjData = tuple(zip([(slice(i,i+1), ) + tuple([slice(max(r.start +t,0), min(r.stop-t, 1000)) 
                                for r in roi])
                                for i, roi in enumerate(defectRois)],(2**16)*diffs2[:,t:-t,t:-t]))
    
    if len([(slices, diffs) for slices, diffs in modProjData if tuple([s.stop - s.start for s in slices])[1:] != diffs.shape]):
        newModProjData = []
        for slices, diffs in modProjData:
            if tuple([s.stop - s.start for s in slices])[1:] != diffs.shape:
                xc = np.round(0.5*(slices[1].start + slices[1].stop)).astype(int)
                xd = int(diffs.shape[0]*0.5)
                x0, x1 = np.round([xc-xd,xc+xd+1])
                yc = np.round(0.5*(slices[2].start + slices[2].stop)).astype(int)
                yd = int(diffs.shape[1]*0.5)
                y0, y1 = np.round([yc-yd,yc+yd+1])
                newModProjData.append(((slices[0], slice(x0,x1), slice(y0,y1)),diffs))
        modProjData = newModProjData
        print("Rejigging roi")
    
    roi = drs.ind2roi(inds,padding=padding)
    vol1 = vol0[roi]
    vol2 = recon.calcModified(modProjData, roi=roi)
    
    contrast = vol1 - vol2
    
#    dm = DetectabilityMetric()
#    try:
    conts.append([inds, vol1, vol2])
    print("{:1.1f} %".format(100.0*i/len(files)))
#    out,size = dm.indication_evaluation_single(vol1, vol2)
#    except ValueError:
#        vals[tuple(inds)]=('failed')
#        print('ind totally failed')
#    out2 = np.zeros_like(out)
#    nans = np.isnan(out)
#    out2[~nans] = out[~nans]
#    N = (out2 > 0.2).sum()
#    vals[tuple(inds)]=(N, size, np.nanmax(out))
#    print(filename,N,size)
#    
#    x,y,z = np.round(drs.inds2recon(inds) - np.array([r.start for r in roi])).astype(int)
#    f,ax = plt.subplots(1,3,figsize=(20,5))
##    vmax = vol2[:,y,:].flatten()[np.argsort(vol2[:,y,:].flatten())[-50]]
#    vmin = vol2[padding, padding, padding] - 400
#    vmax = vol2[padding, padding, padding] + 400
#    ax[0].imshow(vol2[:,y,:], cmap = 'gray', vmin =vmin,vmax = vmax)
#    ax[1].imshow(contrast[:,y,:])
#    ax[2].imshow(np.nanmax(out, axis = 1))
#    plt.title("{}_{:1.3f}".format(inds,N))
#    plt.savefig("segs/{}.png".format(inds))
#    plt.close()



#plt.figure(figsize = (10,10))
#plt.imshow(vol[:,100],vmin = 0, cmap = 'gray')
#plt.show()