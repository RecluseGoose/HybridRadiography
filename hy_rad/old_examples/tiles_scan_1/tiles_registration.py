# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 13:38:36 2019

@author: robert.culver
"""
print('running here')
import numpy as np
from simulation.engine_interface import RadiographSim, GeomSetup, SimSetup
from hy_rad.registration import FullRegistration, DEFAULT_FKW
from optimisation.spuci_optimiser import SP_UCI
print('things imported')

projdir = "d:/Data/32911_Top Half_RQ0548-08_08May19_2019_05_08_04_34_36/"
angs = np.array([ 75.0,  -8.06288025, -0.469635075])
offs = np.array([0.15604287, -31.3321917,  1.90748051])
defectSize = np.array([.15,.15,0.3])*3.0
thetas = np.linspace(0,-360,3142 + 1)[:-1]
detShape = (1000,1000)
detSize = (200.0,200.0)
sod = 253.03271
sdd = 1137.21059
simSetup = SimSetup( cadpaths = ["D:/testdata/cad_aligned.stl"],
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


reg = FullRegistration(projdir, simSetup, mpgsObjKwargs, blur=blur)

print('full reg generated')
argOrder = ['ax', 'ay', 'az', 'ox', 'oy', 'oz', 'sod', 'sdd', 'axisOffs', 'lam', 'offs', 'ampl', 'bgVal']
bounds = [[ 35.0, 125.0],
          [-30.0, 10.0],
          [-20.0, 20.0],
          [-10.0,10],
          [-40,-20],
          [-10,10],
          [240.0, 260.0],
          [1130,1150],
          [-0.001,0.001],
          [0.4,0.9],
          [0.0, 10000.0],
          [35000,55000],
          [55000,65000]]
opt = SP_UCI(reg.objective,bounds)
opt.optimise(maxEvals = 50000, savefile='opt_2019_09_20_top_0.pkl')