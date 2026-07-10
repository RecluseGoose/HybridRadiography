# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 12:51:48 2019

@author: robert.culver
"""

import numpy as np
from scipy import fftpack, ndimage
import matplotlib.pyplot as plt
import itertools
from metrics.registration_metrics import structSimilarity

from optimisation.spuci_optimiser import SP_UCI

def matchBlur(sim, ref, show = False, bounds = [[0.0,1.9]]*2):
    '''A matching function to vaguely match the blur'''
    sig_fft = 2
    r_fft = ndimage.gaussian_filter(np.abs(fftpack.fft2(ref)),sig_fft)
    r_fft -= r_fft.mean()
    r_fft /= r_fft.std()
    obj = lambda sig: (_matchBlur(sim, sig[0], sig[1], r_fft, sig_fft) + structSimilarity(ref,sim,20),)
    opt = SP_UCI(obj, bounds)
    opt.optimise(maxEvals = 5000, verbose = False)
    sig = opt.getBest()
    if show:
        [opt.obj(arg) for arg in itertools.product(*bounds)]
        blr = ndimage.gaussian_filter(sim,sig)
        plt.matshow(blr, vmin = 0, vmax = 2**16 -1, cmap = 'gray')
        plt.matshow(ref, vmin = 0, vmax = 2**16 -1, cmap = 'gray')
        plt.figure()
        xs = np.array(opt.obj.args)
        ys = np.array(opt.obj.vals)
        plt.tricontourf(xs[:,0],xs[:,1],ys, 15, cmap = 'gnuplot_r')
        plt.plot(xs[:,0],xs[:,1],'kx')
        plt.colorbar()
        plt.show()
    return sig
            
def _matchBlur(sim, sigx, sigy, r_fft, sig_fft):
    crop = 1    # some crop to desensitise wrt geometrical alignment, but I think in general alignment has to be pretty spot on to begin with.
    sim2 = ndimage.gaussian_filter(sim,(sigx, sigy))
    s_fft = ndimage.gaussian_filter(np.abs(fftpack.fft2(sim2)),sig_fft)
    s_fft -= s_fft.mean()
    s_fft /= s_fft.std()
    return np.abs(r_fft[crop:-crop] - s_fft[crop:-crop]).mean()