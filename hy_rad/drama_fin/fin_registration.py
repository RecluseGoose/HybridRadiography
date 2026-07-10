# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 13:38:36 2019

@author: robert.culver
"""
print('running here')
import numpy as np
projdir = r"D:/drama/JS_32296-11_16477_FINAL STEEL ARA_NATHAN TURNER"
angs = np.array([ 75.0,  -8.06288025, -0.469635075])
offs = np.array([0.15604287, -31.3321917,  1.90748051])
defectSize = np.array([.15,.15,0.3])*3.0
thetas = np.linspace(0,-360,3142 + 1)[:-1]
detShape = (1000,1000)
detSize = (200.0,200.0)
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
                [histSimilarity, dict(bins = 500, vmax = 50000), 1.0],
                [homogSimilarity, dict(patchSize = 50, evalFeatures = 100), 1.0],
                [greySimilarity, dict(), 5.0]
]

fkw = DEFAULT_FKW

reg = FullRegistration(projdir, simSetup, mpgsObjKwargs, blur=blur, fkw= fkw, N = 9)

print('full reg generated')
argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'lam', 'offs', 'ampl', 'bgVal']
bounds = [[ -120.0, -100.0],
          [ -30.0, -10.0],
          [ 30.0, 50.0],
          [-25.0,-15.0],
          [-15, -5.0],
          [-15, 0.0],
          [430.0, 520.0],
          [950.0,1170.0],
          [-1.0,1.0],
          [0.15,0.25],
          [8000.0, 12000.0],
          [50000,65000],
          [55000,65000]]
startCoords = np.array([-5.17343471e+01,  4.65975667e+01,  5.23381760e+01, -1.18546750e+01,
       -1.32089374e+01,  8.71309717e+00,  4.97626529e+02,  1.06454317e+03,
        4.30052491e-01,  2.16737286e-01,  1.05214099e+04,  5.93557957e+04,
        6.20309988e+04])
opt = SP_UCI(reg.objective,bounds)
opt.optimise(maxEvals = 150000, maxIter=100, savefile='opt_2020_04_22_fin_1_02.pkl', startCoords = np.atleast_2d(startCoords))


#array([-1.03269224e+02, -1.47452455e+01,  3.83141004e+01, -2.28837349e+01,
#       -9.70743934e+00, -4.18514319e+00,  4.77652551e+02,  1.04879867e+03,
#        6.38784138e-01,  2.18480712e-01,  9.28339753e+03,  5.75306825e+04,
#        6.00343827e+04])

#array([-1.09463122e+02, -2.95287486e+01,  4.15247803e+01, -1.98766253e+01,
#       -5.07146431e+00, -1.26539586e+01,  4.80323983e+02,  1.03056869e+03,
#        3.81806457e-02,  2.05223047e-01,  6.91992347e+03,  5.43332000e+04,
#        5.90336430e+04])