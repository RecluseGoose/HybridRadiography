# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 13:38:36 2019

@author: robert.culver
"""
import numpy as np
from simulation.engine_interface import RadiographSim, GeomSetup, SimSetup
from hy_rad.registration import FullReg2, GeomRegistration, DEFAULT_FKW
from optimisation.spuci_optimiser import SP_UCI
import pickle
import os

projdir = "d:/Data/32911_Btm Half_RQ0548-08_08May19_2019_05_08_12_11_37/"
offsRegSaveFile = 'opt_2019_10_31_bottom_geom_2.pkl' # Save for offset reg history
fullRegSaveFile = 'opt_2019_10_31_bottom_full_2.pkl' # Save for fullreg history
regOutputFile = '20191105_top_reg.pkl' # Save for final output

simSetup = SimSetup( cadpaths = ["D:/testdata/cad_aligned_cut.stl"],
                     detShape = (1000,1000),
                     detSize = (200.0,200.0))
blur = np.array([0.3866146 , 0.94937065])
with open("startingMpgsObjKwargs.pkl",'rb') as f:
    mpgsObjKwargs = pickle.load(f)

#assert False
#%% Step 1: do a rough geom alignment

if os.path.exists(offsRegSaveFile):
    with open(offsRegSaveFile,'rb') as f:
        data=pickle.load(f)
    best = data['args'][np.argmin(data['vals'])]
    print('Skipping Step 1, loading from file.')
else:
    offsReg = GeomRegistration( 
            projdir,                        # Directory to projections
            simSetup,                       # Kwargs for ttmp obj
            mpgsObjKwargs=mpgsObjKwargs,    # Kwargs for mpgs
            N=3,                            # number of projections to fit
            blur=blur,                       # sigma param for scipy.ndimage.gaussian_filter
            fkw = DEFAULT_FKW,              # list of sub objectives [[fun,kwarg,weights], ...] to run
            )
    argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd']
    bounds = [[-80.0,-70.0],
              [170.0, 180.0],
              [-2.0, 1.0],
              [-3.0, 1.0],
              [-34.0, -30.0],
              [1.0, 3.0],
              [250.0, 260.0],
              [1135.0, 1145.0]]
    opt = SP_UCI(offsReg.objective,bounds)
    opt.optimise(maxEvals = 5000, savefile=offsRegSaveFile)
    best = opt.getBest()

#%% Step 2: use akima to update

geomSetup = GeomSetup(
    angles =  best[0:3],
    offsets = best[3:6],
    sod = best[6],
    sdd = best[7],
    axisOffs = 0.0
    )

rs = RadiographSim(simSetup, geomSetup=geomSetup, projdir=projdir, mpgsObjKwargs={'method':'akima'})
mpgsObjKwargs['mappingKwargs'] = rs.mpgs.getMappingKwargs()

#%% Step 3: Do a full reg

# Set bounds
argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd','axisOffs','akimaArgs']
bounds = [[best[0] - 1, best[0] + 1], # ax
          [best[1] - 1, best[1] + 1], # ay
          [best[2] - 1, best[2] + 1], # az
          [best[3] - 0.5, best[3] + 0.5], # ox
          [best[4] - 0.5, best[4] + 0.5], # oy
          [best[5] - 0.5, best[5] + 0.5], # oz
          [best[6] - 1, best[6] + 1], # sod
          [best[7] - 1, best[7] + 1], # sdd
          [-10, 10], #axis offs
          ]
bounds += list(zip(*[(mpgsObjKwargs['mappingKwargs']['akimaArgs'] * mm).tolist() for mm in [0.8,1.2]]))
bounds [9] = [-0.5,0.5] # zero starting x point for akima starts on 0... has zero range using method above.

fullReg = FullReg2(
        projdir,                        # Directory to projections
        simSetup,                       # Kwargs for ttmp obj
        mpgsObjKwargs=mpgsObjKwargs,    # Kwargs for mpgs
        N=3,                            # number of projections to fit
        blur=blur,                       # sigma param for scipy.ndimage.gaussian_filter
        fkw = DEFAULT_FKW,              # list of sub objectives [[fun,kwarg,weights], ...] to run
        )

initial = np.repeat(np.hstack((best, [0.0], mpgsObjKwargs['mappingKwargs']['akimaArgs']))[None,], 10, axis = 0)
initial += 0.01*2.0*(np.random.random(initial.shape)-0.5) * initial
opt = SP_UCI(fullReg.objective,bounds)
opt.optimise(maxEvals = 50000, savefile=fullRegSaveFile, startCoords = initial)

#%% Step 4: write results to a reg file

mpgsObjKwargs['method'] = 'akima'
geomSetup, mpgsObjKwargs['mappingKwargs'] = fullReg._toKwargs(opt.getBest())

with open(regOutputFile,'wb') as f:
    f.write(pickle.dumps([geomSetup,mpgsObjKwargs]))

#%% Gubbins that I've now removed
#reg = FullRegistration(projdir, simSetup, mpgsObjKwargs, blur=blur)
#print('full reg generated')
#argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'lam', 'offs', 'ampl', 'bgVal']
#bounds = [[ 35.0, 125.0],
#          [-30.0, 10.0],
#          [-20.0, 20.0],
#          [-10.0,10],
#          [-40,-20],
#          [-10,10],
#          [240.0, 260.0],
#          [1130,1150],
#          [-0.001,0.001],
#          [0.4,0.9],
#          [0.0, 10000.0],
#          [35000,55000],
#          [55000,65000]]
#opt = SP_UCI(reg.objective,bounds)
#opt.optimise(maxEvals = 50000, savefile='opt_2019_09_20_top_0.pkl')