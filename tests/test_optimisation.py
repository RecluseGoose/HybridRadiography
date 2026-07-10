# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 15:48:35 2019

@author: robert.culver
"""

import numpy as np
from optimisation.spuci_optimiser import SP_UCI
import deap.benchmarks
import os

def test_SPUCI():
	bounds = [[-10.0,+10.0]]*30
	s = SP_UCI(deap.benchmarks.griewank,bounds,maxmin='min',m=5,p=None,edges=None,seed=174)
	s.optimise(100,1e5,verbose=False,yTol=1e-2)
	expected = np.array("-0.18529747  10.59894764   7.62981016 -14.7262196   -5.45405869 -9.07402226 -16.86025659   1.85042298 -24.53247031  -9.69295371 -1.34783297  32.44565593  -3.254798   -31.22908031  10.44743536 1.84953808  24.01700892   6.59024889 -47.81959749   7.78098476 -43.24139413  -3.12885955 -45.40410294 5.46946398  40.33441036   -6.37881269 -47.52346599  23.39631421 -22.25955772 -11.54358475".split(),dtype = np.float32)*1e-4
	check = np.all(np.isclose(expected, s.getBest(),rtol = 1e-3))
	assert(check)
    
def test_SPUCI_loading():
    obj = lambda x: (np.abs((x + 0.06)**2 * ((x-0.6) - 8) - (x-0.2)**3 + np.exp(-(x-0.4)**2)).sum(),)
    bounds = [[-20,20]]*20
    savefile = "testopt.pkl"
    if os.path.exists(savefile): os.remove(savefile)
    verbose = False
    # opt0 has no saving, but is run in two parts
    opt0 = SP_UCI(obj,bounds)
    opt0.optimise(maxEvals=300, verbose=verbose,yTol=1e-2)
    best0_300 = opt0.getBest()
    opt0.optimise(maxEvals=1000, verbose=verbose,yTol=1e-2)
    best0_1000 = opt0.getBest()
    # opt1 has no saving, and is run in two parts (reloaded)
    opt1 = SP_UCI(obj,bounds)
    opt1.optimise(savefile=savefile, maxEvals=300, verbose=verbose,yTol=1e-2)
    best1_300 = opt1.getBest()
    opt1 = SP_UCI(obj,bounds)
    opt1.optimise(savefile=savefile, maxEvals=1000, verbose=verbose,yTol=1e-2)
    best1_1000 = opt1.getBest()
    # opt2 runs all as one
    opt2 = SP_UCI(obj,bounds)
    opt2.optimise(maxEvals=1000, verbose=verbose,yTol=1e-2)
    best2_1000 = opt2.getBest()
    # Check values
    assert(np.all((best2_1000==best0_1000)*(best1_1000==best0_1000)))
    assert(np.all((best0_300)*(best1_300)))
    # cleanup
    if os.path.exists(savefile): os.remove(savefile)