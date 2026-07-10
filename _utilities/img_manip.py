# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 14:38:33 2019

@author: robert.culver
"""
import cv2
import glob
import os
import numpy as np

def imread(filepath):
    return cv2.imread(filepath,cv2.IMREAD_UNCHANGED)

def imwrite(filepath, img):
    return cv2.imwrite(filepath, img)

def imresize(image, width = None, height = None, inter = cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation = inter)
    return resized

def getAllFiles(projdir, duplicateLast = True):
        allFiles = glob.glob(os.path.join(projdir, "*.tif*"))
        return allFiles[:-1] if duplicateLast else allFiles
    
def loadAll(projdir):
    return np.array([imread(f) for f in getAllFiles(projdir)])
    
def renorm(img, normpatch, normTarget):
    norm = normTarget*1.0/np.median(img[normpatch])
    return img*norm

def makeModifiedDirectory(projdir, outdir, fun, funkw):
    '''Applies callable (or list of callables) fun to projdir and rewrites to outdir'''
    files = getAllFiles(projdir)
    assert (callable(fun) or (type(fun) is list)),"fun must be callable or list of callables"
    assert ((type(funkw) is dict) or (type(funkw) is list)),"fnkw must be dict or list"
    fun_ = [fun] if callable(fun) else fun                  # fun_ must be list of functions
    funkw_ = [funkw] if (type(funkw) is dict) else funkw    # funkw_ must be list of function kws
    if not (os.path.exists(outdir) and os.path.isdir(outdir)):
        os.mkdir(outdir)
    for f in files:
        fn = os.path.join(outdir, os.path.split(f)[-1])
        img = imread(f)
        dtype = img.dtype
        # modify img function by funciton
        for jib, kws in zip(fun_, funkw_):
            img = jib(img, **kws)
        if os.path.exists(fn):
            os.remove(fn)
        imwrite(fn, img.astype(dtype))
        print(fn)
        
def resizeDirectory(projdir, outdir, size):
    makeModifiedDirectory(projdir, outdir, imresize, {'width':size[0],'height':[1]})
    

def cropArray(array,slices=None,margin=0,projectmethod=None):
    """
    Crop ND-array to eliminate zeros in edges, potentially updating provided slices, too

    >>> array = np.zeros((5,6))
    >>> array[1:,2:4] = 1
    >>> array
    array([[ 0.,  0.,  0.,  0.,  0.,  0.],
           [ 0.,  0.,  1.,  1.,  0.,  0.],
           [ 0.,  0.,  1.,  1.,  0.,  0.],
           [ 0.,  0.,  1.,  1.,  0.,  0.],
           [ 0.,  0.,  1.,  1.,  0.,  0.]])
    >>> cropArray(array,(slice(5,10),slice(4,10)))
    (array([[ 1.,  1.],
           [ 1.,  1.],
           [ 1.,  1.],
           [ 1.,  1.]]), (slice(1, 5, None), slice(2, 4, None)), (slice(6, 10, None), slice(6, 8, None)))
    >>> array = np.concatenate((array[:,:,np.newaxis],array[:,:,np.newaxis]),axis=2)
    >>> slices = (slice(10,15),slice(11,17),slice(2,4))
    >>> cropArray(array,slices,projectmethod=False)[1:]
    ((slice(1, 5, None), slice(2, 4, None), slice(0, 2, None)), (slice(11, 15, None), slice(13, 15, None), slice(2, 4, None)))
    >>> cropArray(array,slices)[1:]
    ((slice(1, 5, None), slice(2, 4, None), slice(0, 2, None)), (slice(11, 15, None), slice(13, 15, None), slice(2, 4, None)))

    #handling of completely empty array
    >>> array = np.zeros((5,6))
    >>> np.all(cropArray(array,(slice(5,10),slice(4,10)))[0] == np.zeros((5,6)))
    True
    """
    #if array empty, just pass through
    if np.all(array==0):
        return array,tuple([slice(None) for count in range(array.ndim)]),slices
    if projectmethod is None: #used by default for 3D
        projectmethod = array.ndim==3
    if projectmethod and array.ndim==3: #faster for large arrays, only tested in 3D
        boolarray = array!=0
        #project data
        projs = [np.sum(boolarray,axis=count) for count in range(1,array.ndim)]
        indices= [np.argwhere(np.sum(proj,axis=axis)) for proj,axis in zip((projs[0],projs[1],projs[0]),(1,0,0))]
        starts,stops = np.asanyarray([[ind.min()-margin,ind.max()+margin+1] for ind in indices]).T
    else:
        indices = np.argwhere(array)
        starts = indices.min(0) - margin
        stops  = indices.max(0) + margin + 1
    #slices on array to use
    localslices = tuple(slice(max(starts[count],0),min(stops[count],array.shape[count])) for count in range(array.ndim))
    if slices is None:
        return array[localslices],localslices
    else:
        #clean None from starts
        slices = tuple(slice(0 if sl.start is None else sl.start,sl.stop) for sl in slices)
        #transform new slices to old cooridnate system
        slices = tuple(slice(sl.start+lsl.start,sl.start+lsl.stop) for sl,lsl in zip(slices,localslices))
        return array[localslices],localslices,slices