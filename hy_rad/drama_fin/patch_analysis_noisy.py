# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 04:22:38 2019

@author: robert.culver
"""

#from metrics.detectability import DetectabilityMetric

try:
    vol0
except:    
    import matplotlib.pyplot as plt
    import pickle
    import numpy as np
    import scipy.ndimage as snd
    from scipy import ndimage

    from reconstruction.recon import NikonRecon
    from simulation.engine_interface import SimSetup
    from _utilities.img_manip import imread, imwrite, imresize, getAllFiles
    import os
    
    from sampling.samplers import DefectReconSampler
    from simulation.transformations import Transformations
    
    #-1.5 0.05
    #-1.7 0.093
    
    reconKwargs = dict(centre=-0.43005249108374866, bhc = 0.4, streakCorrection = [0.0,0.4,5.0])
#    projdir = r"D:/drama/resized"
    projdir = r"D:/drama/noisy"
#    defectdir = "d:/20200506_resized_defects/"
    defectdir = "d:/20200527_noisy/"            # output folder
    
    cadfile = "D:/drama/geom/ara.stl"           # stl path
    voxfile = "D:/drama/geom/ara0125_ero6.npy"  # eroded vox path
    
    with open("fits2.pkl",'rb') as f:
        regDict = pickle.load(f)

    # %% Format registration values
    geomSetup = regDict['geomSetup']

    defectfile = "D:/testdata/defect.stl"       # stl path for defect
    detShape = (1000,1000)
    detSize = (200.0,200.0)
    simSetup = SimSetup(
        cadpaths=[cadfile, defectfile],
        detSize=detSize,
        detShape=detShape,
        densities = np.array([1]),
        flipnorms = np.array([0])
    )
    
    vox = np.load(voxfile)
    voxelSize = 0.1881217281813394
    recon = NikonRecon(projdir, **reconKwargs)
    print('doing initial recon')
    drs = DefectReconSampler(voxelSize, geomSetup, simSetup, vox=vox)
    vol0 = recon.calcVolume()
    print('finished recon')

padding = 50
#vals = {}
conts = []

files = os.listdir(defectdir)

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
    
s = pickle.dumps(conts)
with open("conts.pkl","wb") as f:
    f.write(s)


plt.close('all')
for i in range(len(conts)):
    diffs = conts[i][2] - conts[i][1]
    mask = np.zeros(diffs.shape)
#    centre = (np.array(diffs.shape)/2).astype(int)
#    mask[centre[0]-10:centre[0]+10, centre[1]-10:centre[1]+10, centre[2]-10:centre[2]+10] = 1
#    diffs = diffs*mask
    vol1 = conts[i][1]
    vol2 = vol1 + diffs
    f,ax = plt.subplots(1,2)
    ax[0].matshow(vol1[:,50], cmap = 'gray')
    ax[1].matshow(vol2[:,50], cmap = 'gray')
    plt.savefig('img_{:03}.png'.format(i))
