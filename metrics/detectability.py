# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 09:28:44 2019

@author: robert.culver
"""

import numpy as np
import cv2
import scipy.ndimage as spi
from _utilities.img_manip import cropArray
import scipy.spatial as spatial

def structEllipse(size):
    '''
    Generalisation of cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ) to 3D,
    preserving its ideosyncratic assymetry, with all dimensions equal (i.e. a
    sphere). The result is a very...lumpy sphere.
    For a truer sphere, use structSphere().
    '''
    r  = (size - 1)/2
    rr = r**2
    ellipse = np.zeros((size, size, size), dtype = np.uint8)
    for i in range (size):
        dy = i - r
        if np.abs(dy) <= r:
            dx  = r * np.sqrt((rr - dy**2)/rr)
            jLo = int(np.round(max(r - dx,        0) ) )
            jHi = int(np.round(min(r + dx + 1, size) ) )
            for j in range (jLo, jHi):
                dx  = j - r
                if (dy**2 + dx**2) <= rr:
                    dz  = r * np.sqrt((rr - dy**2 - dx**2)/rr)
                else:
                    dz = 0
                kLo = int(np.round(max(r - dz,        0) ) )
                kHi = int(np.round(min(r + dz + 1, size) ) )
                ellipse[i, j, kLo:kHi] = 1
    return ellipse

class _BaseMetricMethods(object):
    @staticmethod
    def _mean_uniform(vals, *args, **kwargs):
        '''
        Calculate mean of vals, ignoring NaNs.
        If vals are all NaN, NaN is returned.
        '''
        if np.count_nonzero(~np.isnan(vals)) > 0:
            return np.nanmean(vals)
        else:
            return np.NaN

    @staticmethod
    def _std_uniform(vals, *args, **kwargs):
        '''
        Calculate standard deviation of vals, ignoring NaNs.
        If vals are all NaN, NaN is returned.
        '''
        if np.count_nonzero(~np.isnan(vals)) > 0:
            return np.nanstd(vals)
        else:
            return np.NaN

    @staticmethod
    def _mean_gaussian(vals, *args, **kwargs):
        if np.count_nonzero(~np.isnan(vals)) > 0:
            sigma = kwargs['sigma']
            vals  = vals[~np.isnan(vals)]
            return np.nanmean(spi.filters.gaussian_filter(vals, sigma))
        else:
            return np.NaN

    @staticmethod
    def _std_gaussian(vals, *args, **kwargs):
        '''
        Calculate standard deviaition as for uniform weighting.
        '''
        return _BaseMetricMethods._std_uniform(vals)
    
    @staticmethod
    def _scale(data, val = None, dtype = np.uint8):
        '''
        Scale data to fit full range of its dtype.
        If val is provided, this will be scaled proportionally.
        '''
        src     = data.astype(np.float64)
        src_min = data.min()
        src_max = data.max()
        dst_min = np.iinfo(dtype).min
        dst_max = np.iinfo(dtype).max
        if src_max != src_min:
            scale = 1.0*(dst_max - dst_min)/(src_max - src_min)
        else:
            scale = 0
        dst = (dst_min + (src - src_min)*scale).astype(dtype)
        if val is not None: #scaled to match data - NOT shifted, as designed for increment!
            valsrc = float(val)
            return dst, valsrc*scale
        return dst
    
    @staticmethod
    def largestSegmentation(labels,numlabels):
        'return only mask segment that relates to largest feature - assumed to be unique...'
        cums        = np.array([(labels == i).sum() for i in range(1, numlabels + 1)])
        return (labels == (1 + np.argmax(cums))).astype(int)

class DetectabilityMetric(object):
    parametersCurrents = {
            'non_neg_diff':-1, # 1, -1 or 0 for all positive, ignore negative or keep negatives
            'pre_kernel' : True,
            'pk':2,
            'k':2,
            'weight' : 'gaussian',
            'contrast_detection_threshold' : 2.0,
            'Otsu': True,
            'crop_margin': (slice(1,-1),)*3,
            'n_openings': 2,
            'basenoise': True,
            'min_std': 1.0, # as far as I can tell, this is a fudge that avoids divisions by zero...
            'max_CNR': 1e4,
            }
    extra_keywords = {'sigma':4}
    NO_DETECTION = np.zeros((1))
    
    
    def indication_evaluation_single(self, baseline, indication):
        '''
        Returns 2D array of columns relating to different metrics.
        '''
        # Input handling...
        dim = np.ndim(baseline)
        assert dim == 2 or dim == 3, "Images must be 2D or 3D, currently is {0}D.".format(dim)
        weightingMethod = self.parametersCurrents['weight']
        assert weightingMethod in ['uniform','gaussian'], "Invalid weighting method"    
        nnd = self.parametersCurrents['non_neg_diff']
        assert nnd in [1,-1,0],'invalid non_neg_diff'
        # baseline values expected to be higher... diffs should be mostly positive
        array_difference = baseline - indication
        if nnd == 1:        # Shift values to be positive only.            
            array_difference += np.abs(np.nanmin(array_difference))+1
        elif nnd == -1:     # Eliminate negative; likely caused by margin artefacts.
            array_difference[array_difference<0] = 0
        else:               # Retain negative values unchanged.            
            pass
        # Setup prefiltering
        pk = self.parametersCurrents['pk']
        pre_length = 2 * pk + 1
        if self.parametersCurrents['pre_kernel']:
            if weightingMethod == 'uniform':
                pre_kernel = np.ones((pre_length, pre_length, pre_length))
            else: # 'gaussian':
                pre_kernel = structEllipse(pre_length)
        else:
            pre_kernel = np.zeros((pre_length, pre_length, pre_length))
            pre_kernel[pk,pk,pk] = 1
        # Setup conv kernel
        weightingMethod = self.parametersCurrents['weight']
        k = self.parametersCurrents['k']
        length = 2 * k + 1
        if weightingMethod == 'uniform':
            kernel        = np.ones((length, length, length)) # 3D
            function_mean = _BaseMetricMethods._mean_uniform
            function_std  = _BaseMetricMethods._std_uniform
        else:# 'gaussian':
            kernel        = structEllipse(length)
            function_mean = _BaseMetricMethods._mean_gaussian
            function_std  = _BaseMetricMethods._std_gaussian
        # if doing 2d, take middle of kernels
        if dim == 2:    
            pre_kernel = pre_kernel[:,:,pk]
            kernel = kernel[:,:,k]
            middle = (slice(1, -1), slice(1, -1) )
            connec = (3, 3)
        else:
            middle = (slice(1, -1), slice(1, -1), slice(1, -1) )
            connec = (3, 3, 3)
        # Check there is even a detection
        if np.sum(array_difference >= self.parametersCurrents['contrast_detection_threshold']) == 0:
            retval = self.NO_DETECTION
        else:
            # Apply a threshold
#            array_prethresh = spi.generic_filter(array_difference, function = function_mean, footprint = pre_kernel, extra_keywords = self.extra_keywords)       
            array_prethresh = spi.gaussian_filter(array_difference, **self.extra_keywords)
            aPre8, quantthresh = _BaseMetricMethods._scale(array_prethresh,max(self.parametersCurrents['contrast_detection_threshold'],0))
            if self.parametersCurrents['Otsu']:
                # cv2.THRESH_OTSU only works for 1D or 2D arrays, so first create nonce 1D array.
#                aPre8 = np.mean([cv2.morphologyEx(aPre8.reshape(aPre8.transpose(i,j,k).shape[0],-1), cv2.MORPH_TOPHAT, np.ones(3)).reshape(aPre8.shape) for i,j,k in ([0,1,2],[1,2,0],[2,1,0])],axis = 0)
                oneD   = aPre8.reshape((aPre8.size)).astype(np.uint8)
                thresh = cv2.threshold(oneD, 0, 1, cv2.THRESH_OTSU)[0]
            else:
                edgepixmask = np.ones(aPre8.shape, dtype = bool)
                edgepixmask[middle] = 0
                thresh      = np.median(aPre8[edgepixmask])
            array_thresh = cv2.threshold(aPre8, max(thresh,quantthresh-1), 1,cv2.THRESH_BINARY)[1]
            cropslices = self.parametersCurrents['crop_margin']
            array_thresh_cropped = array_thresh[cropslices].copy()
            array_cropped = array_difference[cropslices].copy()
            # Do labelling, get biggest region
            array_label, num_features = spi.label(array_thresh_cropped,structure = np.ones(connec, dtype=int))
            if True:
                # Remove some or all segments touching edge of cropped array.
                edgelabels = array_label.copy()
                edgelabels[middle] = 0
                edgelabels = np.unique(edgelabels) #will include 0
                edgelabels = edgelabels[edgelabels!=0]
                if edgelabels.size > 0:
                    if edgelabels.size < num_features:
                        # Some features not at edge of cropped image => eliminate all edge segments.
                        for label in edgelabels:
                            array_label[array_label==label] = 0
                        array_label = (array_label > 0).astype(int)
                    else: #%# TODO: refactor using largestSegmentation
                        # All features touch edge of cropped image  => eliminate all but segment w/ most non-edge pixels.
                        cums        = np.array([(array_label[middle] == i).sum() for i in edgelabels])
                        label       = edgelabels[np.argmax(cums)] # to keep
                        array_label = (array_label == label).astype(int)
                array_label, num_features = spi.label(array_label,structure = np.ones(connec, dtype=int))
                array_label = _BaseMetricMethods.largestSegmentation(array_label, num_features)
            array_morph = (array_label.copy() > 0).astype(np.uint8) # Remove labels (all values in all retained segments = 1).
#            xsf,ysf,zsf = np.array((np.array(array_label.shape) + 1) * 0.5).astype(int)
#            array_morph = (array_label.copy() == array_label[xsf,ysf,zsf]).astype(np.uint8) # Remove labels (all values in all retained segments = 1).
            # Apply closing segmentation.
            openIter = self.parametersCurrents['n_openings']
            if openIter>0:
                array_morph = spi.morphology.binary_dilation(array_morph, kernel, openIter, border_value = 0)
                array_morph = spi.morphology.binary_erosion(array_morph, kernel, openIter, border_value = 1)
#            array_morph = spi.morphology.binary_erosion(array_morph, kernel, 1, border_value = 1)
            array_segmented = array_morph.astype(dtype = np.bool) # segmentation mask for filtered, thresholded diff
            # Apply CNR
            if array_segmented.sum() == 0: # no detections survived
                retval = self.NO_DETECTION
                mask = np.zeros(array_segmented.shape)
            else:
                # Get contrast
                array_contrast = array_cropped.copy().astype(np.float)
                # Get noise
                index = min(4**array_contrast.ndim,array_segmented.sum())
                highcontrast = max(0,np.sort(array_contrast[array_segmented])[-index])
                basevals = baseline[cropslices][array_segmented]#[array_contrast>=highcontrast*0.5]                                       #    <-------------------------------#################
                array_std = np.ones((array_contrast.shape),dtype=np.float)*(np.std(basevals) + self.parametersCurrents['min_std']) #<--------------- minstd usually 5?
                # Nan the outside bits
                array_contrast[~array_segmented] = np.NaN
                array_std[~array_segmented]      = np.NaN
                array_std[~array_segmented]      = np.NaN
                if np.any(array_std==0): assert False, 'Functionality removed. This will never happen' # TODO!
                # Dynamic range irrelevant if contrast and std on same scale.
                with np.errstate(divide='ignore', invalid='ignore'):
                    array_cnr = np.true_divide(array_contrast, array_std)
                    array_cnr = np.minimum(array_cnr,self.parametersCurrents['max_CNR'])
                retval = array_cnr
            # Get size
                sizethresh = np.nanmax(array_cnr)*0.5
                mask = np.logical_and(array_segmented,array_cnr>sizethresh)
            if not mask.sum()>0: #sizing failed as required CNR not reached
                size = 0
            else:
                #find single contiguous blob
                sizelabels, sizecount = spi.label(mask,structure = np.ones(connec,dtype=int))
                mask = _BaseMetricMethods.largestSegmentation(sizelabels, sizecount).astype(bool)
                #find shell to reduce computational load
                shell = np.logical_and(mask,~spi.morphology.binary_erosion(mask,iterations=1))
                shellinds = np.vstack(np.where(shell)).T
                if len(shellinds)>100: #further trim points by taking convex hull
                    hull = spatial.ConvexHull(shellinds)
                    shellinds = shellinds[np.unique(hull.simplices)]
                if len(shellinds)>1:
                    #span as max euclidean distance
                    size = np.max(spatial.distance.pdist(shellinds))
                else:
                    size = 0          
            return retval, size
            

