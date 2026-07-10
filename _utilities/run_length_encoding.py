# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 03:02:58 2020

@author: robert.culver
"""

import numpy as np
import pickle

def rleSave(filename, arr):
    '''Save boolean array using run length encoding'''
    assert(arr.dtype == np.bool),'Input must be boolean'
    flat = arr.T.flatten() # transpose for RLE along Z axis.. ~4x faster
    xor = flat[1:]^flat[:-1]
    firstVal = flat[0]
    rleSwitchPoints = 1+ np.where(xor)[0]
    with open(filename,"wb") as f:
        data = dict( arrShape = arr.shape,
                     firstVal = firstVal,
                     rleSwitchPoints = rleSwitchPoints )
        f.write(pickle.dumps(data))
        
def rleLoad(filename):
    '''Load boolean array using run length encoding'''
    with open(filename,"rb") as f:
        data = pickle.load(f)
        keys = ['arrShape','firstVal','rleSwitchPoints']
        arrShape, firstVal, rleSwitchPoints = [data[k] for k in keys]
    output = np.zeros(np.product(arrShape),dtype = np.bool)
    [output.__setitem__(slice(s,e),True) for s,e in rleSwitchPoints.reshape(-1,2)]
    output = output.reshape(arrShape[::-1]).T # untranspose from save func
    if firstVal: output = np.logical_not(output)
    return output