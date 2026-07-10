# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 13:38:36 2019

@author: robert.culver
"""
print('running here')
import numpy as np
projdir = r"D:/drama/JS_32296-11_15318_STEEL ARA POST MACH_NATHAN TURNER"
angs = np.array([ 75.0,  -8.06288025, -0.469635075])
offs = np.array([0.15604287, -31.3321917,  1.90748051])
defectSize = np.array([.15,.15,0.3])*3.0
thetas = np.linspace(0,-360,3142 + 1)[:-1]
detShape = (1000,1000)
detSize = (200.0, 200.0)
sod = 253.03271
sdd = 1137.21059
from simulation.engine_interface import RadiographSim, GeomSetup, SimSetup
from hy_rad.registration import FullRegistration, DEFAULT_FKW
from optimisation.spuci_optimiser import SP_UCI
print('things imported')

simSetup = SimSetup( cadpaths = ["D:/Drama/geom/ara.stl"],
                     detShape = (1000,1000),
                     detSize = (200.0,200.0))
geomSetup = GeomSetup( sod = 254.0,
                       sdd = 1145.0 )
mappingKwargs = {'bgVal': 60458.0590116136,
                 'bgThreshVal': 0.0001,
                 'lam': 0.6041077877030052,
                 'offs': 4939.076571656569,
                 'ampl': 41699.92895592637}
mpgsObjKwargs = {'mappingKwargs': mappingKwargs}
blur = np.array([0.3866146 , 0.94937065])



from simulation.engine_interface import RadiographSim, DEFAULT_BG_THRESH, GeomSetup
from metrics.registration_metrics import histSimilarity, homogSimilarity, greySimilarity
from metrics.blur_matching import matchBlur
from _utilities.img_manip import imread, imresize,getAllFiles

DEFAULT_FKW = [ # [function, kwargs, weight]
#                [histSimilarity, dict(bins = 500, vmax = 50000), 1.0],
#                [homogSimilarity, dict(patchSize = 50, evalFeatures = 100), 1.0],
                [greySimilarity, dict(), 1.0]
]

fkw = DEFAULT_FKW

reg = FullRegistration(projdir, simSetup, mpgsObjKwargs, blur=blur, fkw= fkw, N = 7)

print('full reg generated')
argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'lam', 'offs', 'ampl', 'bgVal']
bounds = [[ -55.0, -46.0],
          [ 44.5, 48.5],
          [ 46.0, 57.0],
          [-15.0, -7.0],
          [-16.0, -8.0],
          [3.5, 13.5],
          [450.0, 500.0],
          [950.0,1070.0],
          [-2.0,2.0],
          [0.19,0.23],
          [8000.0, 12000.0],
          [54000,60000],
          [58000,63000]]
startCoords = np.array([-5.17547911e+01,  4.65984801e+01,  5.23182792e+01, -1.18595328e+01,
       -1.31935247e+01,  8.69224067e+00,  4.75523816e+02,  1.01535079e+03,
        4.27048542e-01,  2.08878720e-01,  1.02809416e+04,  5.78513813e+04,
        6.20365640e+04])
opt = SP_UCI(reg.objective,bounds) 
opt.optimise(maxEvals = 150000, maxIter=200, savefile='opt_2020_04_22_fin2_03.pkl', startCoords = np.atleast_2d(startCoords))
