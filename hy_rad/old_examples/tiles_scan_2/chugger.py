# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 13:42:49 2019

@author: robert.culver
"""

import numpy as np
import os
import pickle
from scipy import ndimage
import scipy.interpolate as interp

from reconstruction.recon import NikonRecon
from hy_rad.hybrid_radiography import DefectSimulation
from sampling.samplers import DefectReconSampler
from tiles_results.rois import rois as filletSlices
from metrics.sei_detectability import indication_evaluation_single
from simulation.engine_interface import SimSetup, GeomSetup
from _utilities.img_manip import imwrite

#%% Define filepaths
regOutputFile = '20191105_top_reg.pkl'
cadfile = "D:/testdata/cad_aligned.stl"     #
defectfile = "D:/testdata/defect.stl"       #
voxfile = "D:/testdata/eroded5_50.npy"      #
vox = np.load(voxfile)                      #
cleanfile = "d:/testdata/cleanprojs.npy"    #
outputDir = "Z:/33740 - Tiles XCT Validation/Scan 2 Results/detectability_{:03d}.tif" # final outputdir
projdir =  "D:/resized_top/"
defectdir = "C:/Users/robert.culver/main_body"
dumpdir = "d:/20191114_Defects_050_250/"    # Intermediate directory for dumping subvols

#%% Modify eroded vox to be restricted to fillet regions
eroded = np.load(voxfile)
filletVox = np.zeros_like(eroded)
for slices in filletSlices:
    newSlices = tuple([slice(s.start*2,s.stop*2) for s in slices])
    filletVox[newSlices] = eroded[newSlices]

detShape = (1000,1000)
detSize = (200.0,200.0)
defectSize = np.array([0.25, 0.25, 0.25])
blur = np.array([0.75,0.75])
nProj = 3142

with open(regOutputFile,"rb") as f:
    geomSetup, mpgsObjKwargs = pickle.load(f)
    geomSetup = GeomSetup(geomSetup.angles,geomSetup.offsets, geomSetup.sod, geomSetup.sdd, geomSetup.axisOffs)

simSetup = SimSetup(
    cadpaths = ["D:/testdata/cad_aligned_cut.stl", "D:/testdata/defect.stl"],
    detShape = detShape,
    detSize = detSize,
)

#%% Create defect simulation object
ds = DefectSimulation(simSetup, geomSetup, cleanfile,  mpgsObjKwargs, blur, nProj, filletVox)

#%% Create defect recon sarmpler and get initial recon
reconKwargs = dict(centre=-2.0, bhc = 0.4, streakCorrection = [0.0,0.4,5.0])
voxelSize = 0.0889232427777848
recon = NikonRecon(projdir, **reconKwargs)
print('doing initial recon')
drs = DefectReconSampler(voxelSize, geomSetup, simSetup, vox)
vol0 = recon.calcVolume()
print('finished recon')
padding = 50 # how much space to have around the defect

#%% Create viable samples
viableInds = ds.sampleEveryViable(12)
# start sampling and writing results
#try:
#    i0 = np.where(metrics[:,0] == 0)[0][0]
#except:
#    metrics = np.zeros((len(viableInds),2))
#    i0 = 0

metrics = np.zeros((len(viableInds),2))

for i,ind in enumerate(viableInds):
    print('running {}'.format(i))
    j = 0
    while(j<3):
        try:
            # Get difference images in 2D data
        #    while True:
        #        try:
            diffResults_2d = ds.sampleInd(ind, defectSize, defectDensity = 0.6, nThreads = 20)
        #            break
        #        except:
        #            pass
            diffs2d = diffResults_2d['diffs']
            defectRois = diffResults_2d['rois']
            # Fix glitches, very rare
            glitches = diffs2d<0
            diffs2d[glitches] = ndimage.maximum_filter(diffs2d,3)[glitches]
            # Generate modified projection data, t trims the edges down, just because depending on how the blur is applied, you might get weird bits round the edges
            t = 5
            modProjData = tuple(zip([(slice(i,i+1), ) + tuple([slice(max(r.start +t,0), min(r.stop-t, 1000)) 
                                        for r in roi])
                                        for i, roi in enumerate(defectRois)],(2**16)*diffs2d[:,t:-t,t:-t]))
            # Check and fix roi issues. #TODO! it feels like this shouldn't be here?
            if len([(slices, diffs) for slices, diffs in modProjData if tuple([s.stop - s.start for s in slices])[1:] != diffs.shape]):
                newModProjData = []
                for slices, diffs in modProjData:
                    if tuple([s.stop - s.start for s in slices])[1:] != diffs.shape:
                        xc = np.round(0.5*(slices[1].start + slices[1].stop)).astype(int) # centre
                        xd = int(diffs.shape[0]*0.5)                                      # half diff length
                        x0, x1 = np.round([xc-xd,xc+xd])                                # start and ends
                        yc = np.round(0.5*(slices[2].start + slices[2].stop)).astype(int) # centre
                        yd = int(diffs.shape[1]*0.5)                                      # half diff length
                        y0, y1 = np.round([yc-yd,yc+yd])                              # start and ends
                        newModProjData.append(((slices[0], slice(x0,x1), slice(y0,y1)),diffs))
                print("\nRejigging roi")
                modProjData = newModProjData
            
            # Get vols
            roi3d = drs.ind2roi(ind,padding=padding)    
            vol1 = vol0[roi3d]
            vol2 = recon.calcModified(modProjData, roi=roi3d)
            # Save to file, just in case
            toSave = dict(vol1 = vol1, vol2 = vol2, ind = ind)
            saveAs = os.path.join(dumpdir,"_".join(["{}".format(i) for i in ind]) + '.pkl')
            with open(saveAs, 'wb') as f:
                f.write(pickle.dumps(toSave))
            # Calc metric
            if np.isnan(vol1).sum() or np.isnan(vol2).sum():
                print('nans in vol')
                break
            metrics[i] = indication_evaluation_single(vol1, vol2)    
            print("Ind {} of {}, {:1.2f}%, metric val = {}".format(i,len(viableInds),(i+1)*100.0/len(viableInds),metrics[i]))
            break
        except:
            j+=1

##%% interpolate across vox
#valid = ~np.all(metrics == 0,1)
#interpVals = metrics[valid]
#interpInds = viableInds[valid]
#metric = interpVals[:,0]**(2/3) + 5.0
#
#subvox = vox[:,:,:].astype(bool)
#outVox = np.nan * np.logical_not(subvox)
#coords = np.array(np.where(subvox)).T
#interpvals = interp.griddata(interpInds, metric, coords, method='nearest')
#outVox[tuple(tuple(c) for c in coords.T)] = interpvals
#
##%% Write outputs
#
## remove nans for image writing
#outVox2 = -1 * np.logical_not(subvox)
#outVox2[tuple(tuple(c) for c in coords.T)] = interpvals
#
#print('writing outputs')
#[imwrite(os.path.join(outputDir.format(i)),s.astype(np.float32)) for i,s in enumerate(outVox2)]