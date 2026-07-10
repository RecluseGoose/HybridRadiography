# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 12:39:29 2019

@author: robert.culver
"""
import numpy as np
from reconstruction.recon import NikonRecon

TEST_DIR = "D:/resized"

def notest_init():
	recon = NikonRecon(TEST_DIR) ##TODO! un hard code
	evaluatedSum = recon.P.data.sum()
	evaluatedStd = recon.P.data.std()
	check1 = np.isclose(evaluatedSum,7.4438405e+18, rtol = 1e-6)
	check2 = np.isclose(evaluatedStd, 1.443399e+9, rtol = 1e-6)
	assert(check1)
	assert(check2)
	#def testCalcVolume():
	recon2 = NikonRecon("D:/generated/") ##TODO! un hard code
	slices = (slice(550,750),slice(400,600),slice(400,600))
	# regardless of how the volume is gerenated, the use of slices should result in the same behaviour
	o1 = recon2.calcVolume()[slices]
	print(o1.shape, o1.sum())
	o2 = recon2.calcVolume(roi = slices)
	check3 = np.isclose(o1,o2,1e-4).sum()*1.0/(o1.size) > 0.97
	assert(check3)