# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 00:13:56 2019

@author: Robert.Culver
"""
import numpy as np
import os
import h5py
import dask.array
import dask.array.image
import cv2
import time
from _utilities.defaults import TEMP_STACK_DIR
from _utilities.hashing import getHashString

def imread(filepath):
    return cv2.imread(filepath,cv2.IMREAD_UNCHANGED)

class _GenericVolume(object):
    """
    Parent for Volume
    """
    _ctr = 0
    def __init__(self):
        _GenericVolume._ctr += 1
        self._name = self._assignName()
        
    def _assignName(self):
        return "volume_" + getHashString(_GenericVolume._ctr, os.getpid(), time.time()%1.0)
    
    def _loadImgStack(self, imgDir):
        '''Loads from directory'''
        globstring = os.path.join(imgDir, '*.tif*')
        out = dask.array.image.imread(globstring,imread) if self.useOpenCV else dask.array.image.imread(globstring)
        return out

    def _loadHDF5(self, hdfFile):
        '''Loads from hdf5'''
        with h5py.File(hdfFile) as f:
            arr = f['data']
            chunkShape = (arr.shape[0], 1, arr.shape[-1]) ## TODO! Is this optimal?
            out = dask.arr.from_array(arr, chunks=chunkShape)
        return out

    def data(self, dtype = None):
        '''Returns dask array in required dtype'''
        return self._data.astype(dtype) if (dtype) else self._data
    
    def saveHDF5( self,
                  filename = None,
                  filedir = None,
                  overwrite = True
                 ):
        '''Saves data to hdf5'''
        if filename is None:
            filename = 'tempvol.hdf5'
        if filedir is None:
            filedir = TEMP_STACK_DIR
        if not (os.path.isdir(filedir)):
            os.mkdir(filedir)
        fullpath = os.path.join(filedir,filename)
        if (os.path.exists(fullpath) and overwrite):
            os.remove(fullpath)
        self._data.to_hdf5(fullpath,'data')
    
#... there's just no need for custom pickling at the moment...
#    def __getstate__(self):
#        if self.resaveOnPickle:
#            self.saveHDF5(self._tempname())
#        ret = self.__dict__
#        del ret['_data']
#        return ret#
#    def __setstate__(self,dict):
#        super(self.__class__,self).__setstate__(dict)
#        self._data = self._loadHDF5(self._tempname()) 
#    def _tempname(self):
#        return os.path.join(TEMP_STACK_DIR, self._name + '.hdf5')
#    def _clean(self):
#        f = self._tempname()
#        if os.path.exists(f):
#            os.remove(f)
#... there's just no need for custom pickling at the moment...
        

class Volume(_GenericVolume):
    """
    Class for data volumes / image stacks
    """
    def __init__( self,
                  imgDir = None,
                  hdfFile = None,
                  useOpenCV = False,
                  normPatch = None,
                  normTarget = 60000,
                  resaveOnPickle = False,
                 ):
        ''''''
        super(Volume,self).__init__()
        assert ((imgDir is None) ^ (hdfFile is None)),'Specify inputfolder and inputfile cannot both be specified'
        assert (normPatch is None) or ((len(normPatch)==2) and all([isinstance(el,slice) for el in normPatch])), 'normPatch must be two slices'
        self.imgDir = imgDir
        self.hdfFile = hdfFile
        self.useOpenCV = useOpenCV # Use opencv's imread
        self.normPatch = normPatch
        self.normTarget = normTarget
        self.resaveOnPickle = resaveOnPickle
        self._data = self._loadImgStack(imgDir) if imgDir else self._loadHDF5(hdfFile)

    def projections(self, dtype = 'float16'):
        '''Returns projection stack'''
        stack = self.data(dtype)
        if self.normPatch:
            norms = self.normTarget/np.median(stack[self.normPatch], axis = 0)
            return stack*norms[:, None, None]  ##TODO... is this 0 to 63565 or what?
        else:
            return stack ##TODO... is this 0 to 63565 or what?
        

if __name__ == '__main__':
    pass