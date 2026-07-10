# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 14:47:57 2019

@author: robert.culver
"""
from os.path import exists,join
import numpy as np

import _utilities.hashing
from _utilities.defaults import USER_DOCS, TEMP_STACK_DIR, TEST_DATA_DIR
from _utilities.img_manip import imread, imresize

def assertExists(f):
    assert(exists(f)),'{} not found.'.format(f)

def test_defaults():
    [assertExists(f) for f in [USER_DOCS, TEMP_STACK_DIR, TEST_DATA_DIR]]
    
def test_hashString():
    args = ['john', 'locke', 4, 8 , 15, 16 , 23, 42]
    assert(_utilities.hashing.getHashString(args) == '422NKDHQ2Q')  

def test_imgManip():
    testFile = join(TEST_DATA_DIR,'testimg0.tif')
    img1 = imread(testFile)
    assert (img1.sum() == 2188136199)
    assert (np.isclose(img1.mean(),35980.51424175))
    assert (img1.shape == (2000,2000))
    assert (img1.dtype == np.uint16)
    img2 = imresize(img1, 1000,1000)
    assert (img2.sum() == 1620900500)
    assert (np.isclose(img2.mean(),35980.638868))
    assert (img2.shape == (1000,1000))
    assert (img2.dtype == np.uint16)