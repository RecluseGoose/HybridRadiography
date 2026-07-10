# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 16:03:20 2019

@author: robert.culver
"""
import numpy as np
import os

from simulation.engine_interface import MatpathGreyscaleMapping, RadiographSim, TurntableMatpath, GeomSetup, SimSetup
from _utilities.img_manip import imread, imresize
from _utilities.defaults import TEST_DATA_DIR

def test_engineInterface():
    ## MATERIAL PATH GENERATION
    # specify setup
    simSetup = SimSetup(
            detShape = (2000,2000),
            detSize = (200.0,200.0),
            cadpaths = "D:/testdata/artist_placation2.stl"
            )    
    mp = TurntableMatpath(simSetup)
    geomSetup = GeomSetup( angles = [12,22,84],
                           offsets = [-8,-25,.0],
                           sod = 254.0,
                           sdd = 1145.0)
    # make some mp imgs and make sure parallelisation doesn't do anything weird
    imgs1 = mp.getMatPathImgs(N = 10,nThreads=2, geomSetup = geomSetup)
    imgs2 = mp.getMatPathImgs(N = 10,nThreads=1, geomSetup = geomSetup)
    assert (np.all(imgs1 == imgs2))
    print('basic interface checked')
    ## GREYSCALE MAPPING
    # check greyscale mapping... this will match any mp with a testimg radiograph
    tgtpath1 = os.path.join(TEST_DATA_DIR,'testimg0.tif')
    tgt = imresize(imread(tgtpath1), 2000,2000)
    # running this with a tgt radiograph automatically generates a fit
    mpgs = MatpathGreyscaleMapping(imgs1[0], tgt, methodKwargs = {'spuciKwargs':{'maxEvals':500,'yTol':1e-2}})
    assert(np.isclose(mpgs.map(imgs1[0]).mean(), 36662.8540259336))
    assert(np.isclose(mpgs.map(imgs1[0]).std(), 19808.397836809814))
    # check mapping kwargs with what we expect
    expected = { 'bgVal': 59855.28,
                 'bgThreshVal': 0.001,
                 'lam': 1.361362492424985,
                 'offs': 9783.67520150522,
                 'ampl': 87362.2951562202}
    for key, value in mpgs.getMappingKwargs().items():
        assert(np.isclose( expected[key], value ))
    print('greyscale checked')
    # RADIOGRAPHSIM INTERFACE... which is actually a much more streamlined approach
    # specify radiograph sim with ttmp and mapping kwargs
    rad = RadiographSim(simSetup, mpgsObjKwargs = {'mappingKwargs':mpgs.getMappingKwargs()})
    # need a geom kwarg to specify a particular orientation on build plate    
    img3 = rad.get([0], geomSetup)[0]             
    # make sure that the generated radiograph matches output of separate mp and mpgs
    img3_expected = mpgs.map(imgs1[0])
    assert(np.all(img3_expected == img3))
    print('radiograph checked')        
        
