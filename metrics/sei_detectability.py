# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 18:47:19 2019

@author: robert.culver
"""
import numpy as np
import scipy.ndimage as spi
import cv2
from collections import Counter
from scipy import interpolate

def largestSegmentation(labels,numlabels):
    'return only mask segment that relates to largest feature - assumed to be unique...'
    cums        = np.array([(labels == i).sum() for i in range(1, numlabels + 1)])
    return (labels == (1 + np.argmax(cums))).astype(int)

def extract_detectability(indication_survival,cnr=None,area=None):
    'interrogate sf by interpolated evaluation for a given cnr / area'
    assert indication_survival.shape[0]>0,'unexpected input shape'
    assert indication_survival.shape[1]==2,'unexpected input shape'
    assert (cnr is None) ^ (area is None),'exactly one of cnr and area is required'
    if cnr is not None:
        x,y = indication_survival.T
        ex = cnr
    else: #are is not None
        y,x = indication_survival.T #interpolating other way round
        ex = area
    fill = (np.max(y),0) #works both ways
    if indication_survival.shape[0]==1: #no interp
        return fill[0] if ex<=x[0] else fill[1]
    inter = interpolate.interp1d(x,y,kind='linear',axis=-1,bounds_error=False,fill_value=fill)
    return float(inter(ex))

class RadiographEvaluation(object):
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
        return RadiographEvaluation._std_uniform(vals)

    @staticmethod
    def _f_reciprocal (x, k, n):
        return k/x**n

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


settings = dict(weight = "uniform",
                basenoise= 5,
                pre_kernel = 0,
                Otsu = True,
                kernel = 3,
                n_openings = 0,
                max_CNR = 1e4,
                min_std = 5,
                use_largest_segmentation = False,
                crop_margin = 3,
                quant_threshold = 1,
                non_neg_diff = -1,
                remove_edge_segments = False,
                sizing = True,
                showplots = False,
                savedir=None,
                emailSkip=None)

def indication_evaluation_single(baseline, indication):
#    from time import time as time
#    print("doing", time())
    array_difference = baseline - indication
    # TO 3D: Check dimensionality of image.
    dim = len(baseline.shape)
    assert dim == 2 or dim == 3, \
       "Images must be 2D or 3D, not {0}D.".format(dim)
    if settings['non_neg_diff'] > 0:
        # Shift values to be positive only.
        array_difference += np.abs(np.nanmin(array_difference))+1
    elif settings['non_neg_diff'] < 0:
        # Eliminate negative; likely caused by margin artefacts.
        array_difference[array_difference<0] = 0
    else:
        # Retain negative values unchanged.
        pass

    ### Contrast-mean-to-noise ratio evaluation.
    # Set appropriate kernels and functions to be called later.
    pre_kernel = False
    if settings['pre_kernel'] > 0:
        pk         = settings['pre_kernel']
        pre_length = 2 * pk + 1
    k      = settings['kernel']
    length = 2 * k + 1
    if settings['weight'] == 'uniform':
        if settings['pre_kernel'] > 0:
            pre_kernel = np.ones((pre_length, pre_length, pre_length))
        kernel        = np.ones((length, length, length)) # 3D
        function_mean = RadiographEvaluation._mean_uniform
        function_std  = RadiographEvaluation._std_uniform
        exta_keywords = {} # Empty dict.

    elif settings['weight'] == 'gaussian':
        if settings['pre_kernel'] > 0:
            pre_kernel = structEllipse(pre_length)
        kernel        = structEllipse(length)
        function_mean = RadiographEvaluation._mean_gaussian
        function_std  = RadiographEvaluation._std_gaussian
        exta_keywords = {'sigma': 3}
    elif settings['weight'] == 'sobel':
        raise NotImplementedError
    else:
        raise KeyError
    # TO 3D: Set differences for 2D and 3D cases.
    if dim == 2:
        # Take middle of kernels.
        if pre_kernel:
            pre_kernel = pre_kernel[:,:,pk]
        kernel = kernel[:,:,k]
        middle = (slice(1, -1), slice(1, -1) )
        connec = (3, 3)
    else:
        middle = (slice(1, -1), slice(1, -1), slice(1, -1) )
        connec = (3, 3, 3)
    # Given quantisation, enforce minimum contrast.
    if np.sum(array_difference >= settings['quant_threshold']) > 0:
        array_prethresh = array_difference.copy()
        # Obtain meaned/blurred array from difference.
        if settings['pre_kernel'] > 0:
            # Apply pre-threshold kernel if requested.
            array_prethresh = spi.generic_filter(array_prethresh,function = function_mean,footprint = pre_kernel,extra_keywords = exta_keywords)
        # Scale array to range of uint8, along with treshold.
        aPre8, quantthresh = RadiographEvaluation._scale(array_prethresh,max(settings['quant_threshold'],0))
        if settings['Otsu']:
            # Threshold derived by Otsu method, using cv2's treshold()
            # function. This returns the treshold used as well as the
            # tresholded array, but (TO 3D) cv2.THRESH_OTSU only works for
            # 1D or 2D arrays, so first create nonce 1D array.
            oneD   = aPre8.reshape((aPre8.size))
            thresh = cv2.threshold(oneD, 0, 1, cv2.THRESH_OTSU)[0]
        else:
            # Threshold it and apply morphology operations to obtain
            # segmentation - determine background from edge pixels.
            # Edge mask assumes array length >2 in each dimension.
            edgepixmask = np.ones(aPre8.shape, dtype = bool)
            edgepixmask[middle] = 0
            # Mask array_prethresh_uint8 and take median.
            thresh      = np.median(aPre8[edgepixmask])
        # Now threshold array, with greater of quant_threshold and threshold
        # determined above. This cv2 can do in 3D.
        # quant_threshold - 1 is used as cv2 uses >, but we want >=.
        array_thresh = cv2.threshold(aPre8, max(thresh,quantthresh-1), 1,cv2.THRESH_BINARY)[1]
        # Crop the difference to a suitable size
        from _utilities.img_manip import cropArray
        cropslices = cropArray(array_thresh,margin=settings['crop_margin'])[1]
        array_cropped = array_difference[cropslices].copy()
#            array_cropped[~array_thresh[cropslices].astype(bool)] = 0
        # Label features (connected 1-values in thresholded array) with
        # full connectivity (3 x 3 x 3).
        array_label, num_features = spi.label(array_cropped,structure = np.ones(connec,dtype=int))
        # If more than 2 labels applied, can filter by labels.
        if (settings['use_largest_segmentation'] and num_features > 1):
            array_label = largestSegmentation(array_label, num_features)
        elif (settings['remove_edge_segments']
              and num_features > 1):
            # Remove some or all segments touching edge of cropped array.
            edgelabels = array_label.copy()
            edgelabels[middle] = 0
            edgelabels = np.unique(edgelabels) #will include 0
            edgelabels = edgelabels[edgelabels!=0]
            if edgelabels.size > 0:
                if edgelabels.size < num_features:
                    # Some features not at edge of cropped image
                    # => eliminate all edge segments.
                    for label in edgelabels:
                        array_label[array_label==label] = 0
                    array_label = (array_label > 0).astype(int)
                else: #%# TODO: refactor using largestSegmentation
                    # All features touch edge of cropped image
                    # => eliminate all but segment w/ most non-edge pixels.
                    cums        = np.array([(array_label[middle] == i).sum()
                                            for i in edgelabels])
                    label       = edgelabels[np.argmax(cums)] # to keep
                    array_label = (array_label == label).astype(int)
        # Remove labels (all values in all retained segments = 1).
        array_morph = (array_label.copy() > 0).astype(np.uint8)
        # Apply closing segmentation.
        # TO 3D: Now using spi.morphology, since its erosion/dilation
        # functions are in general dimensions.
        if settings['n_openings']>0:
            array_morph = spi.morphology.binary_erosion(array_morph, kernel,settings['n_openings'],border_value = 1)
            array_morph = spi.morphology.binary_dilation(array_morph, kernel,settings['n_openings'],border_value = 0).astype(int)
        array_segmented = array_morph.astype(dtype = np.bool)
        if array_segmented.sum() > 0:
            # If indications have survived segmentation:
            # Obtain contrast-to-noise ratio based on segmentation.
            array_contrast = array_cropped.copy().astype(np.float)
            if settings['basenoise'] is True: #array of single unique value
                index = min(4**array_contrast.ndim,array_segmented.sum())
                highcontrast = max(0,np.sort(array_contrast[array_segmented])[-index])
                basevals = baseline[cropslices][array_contrast>=highcontrast]
#                    #shift to positive only values
#                    basevals -= basevals.min()-1
#                    #eliminate unwanted background pixels
#                    basevals = np.hstack((basevals,np.zeros((1,)))) #concatenate low val to make sure 2nd class exists
#                    scale = 255/basevals.max()
#                    basethresh = 1.1*float(cv2.threshold((basevals*scale).astype(np.uint8),0,1,cv2.THRESH_OTSU)[0])/scale #incl fudge factor
                array_std = np.ones((array_contrast.shape),dtype=np.float)*(np.std(basevals) + settings['min_std'])
            elif settings['basenoise']: #assumed to be numerical value - specifying 1 allows contrast to be extracted directly
                array_std = np.ones((array_contrast.shape),dtype=np.float)*settings['basenoise']
            else: #noise computed locally
                array_std = spi.generic_filter(array_contrast,function = function_std,footprint = kernel) + settings['min_std']
            array_contrast[~array_segmented] = np.NaN
            array_std[~array_segmented]      = np.NaN
            # Try to kill off zero noise values by custom median-filtering.
            if np.any(array_std==0):
                array_std[array_std==0]     = spi.generic_filter(array_std,
                       RadiographEvaluation.custmedian,size=5)[array_std==0]
                array_std[~array_segmented] = np.NaN
            # Dynamic range irrelevant iff contrast and std on same scale.
            with np.errstate(divide='ignore', invalid='ignore'):
                array_cnr = np.true_divide(array_contrast, array_std)
                array_cnr = np.minimum(array_cnr,settings['max_CNR'])
            if settings['sizing']:
                #compute size as max span across voxels achieving specified CNR (or contrast preferable??)
                if settings['sizing'] is True:
                    sizethresh = 2 #default CNR threshold
                else:
                    sizethresh = settings['sizing']
                #bool defect mask
                mask = np.logical_and(array_segmented,array_cnr>sizethresh)
                if not mask.sum()>0: #sizing failed as required CNR not reached
                    size = 0
                else:
                    #find single contiguous blob
                    sizelabels, sizecount = spi.label(mask,structure = np.ones(connec,dtype=int))
                    mask = largestSegmentation(sizelabels, sizecount).astype(bool)
                    #find shell to reduce computational load
                    import scipy.spatial as spatial
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
            # Obtain area as a function of CNR.
            ratios_cdict     = Counter(array_cnr[array_segmented])
            ratios_hist      = np.array(list(ratios_cdict.items()))
            sind             = np.argsort(ratios_hist[:, 0])[::-1]
            ratios_hist      = ratios_hist[sind] # Decreasing index order.
            ratios_cumpixels = np.cumsum(ratios_hist[:, 1])
            ratios           = ratios_hist[:, 0]
        else:
            shape            = np.zeros(array_cropped.shape)*np.NaN
            array_contrast   = shape
            array_std        = shape
            array_cnr        = shape
            ratios_cumpixels = (0,)
            ratios           = (0,)
            size = 0 #ignored if not required
    else:
        # No difference detected
        shape                = np.zeros(array_difference.shape)*np.NaN
        array_cropped        = shape
        array_prethresh      = shape
        array_thresh         = shape
        array_label          = shape
        array_morph          = shape
        array_segmented      = shape
        array_contrast       = shape
        array_std            = shape
        array_cnr            = shape
        ratios_cumpixels     = (0,)
        ratios               = (0,)
        size = 0 #ignored if not required
    indication_survival = (np.vstack((ratios,ratios_cumpixels))).T
    data = {'baseline': baseline,
            'indication': indication,
            'array_difference': array_difference,
            'array_cropped': array_cropped,
            'array_prethresh': array_prethresh,
            'array_thresh': array_thresh,
            'array_label': array_label,
            'array_morph': array_morph,
            'array_segmented': array_segmented,
            'array_contrast': array_contrast,
            'array_std': array_std,
            'array_cnr': array_cnr,
            'indication_survival': indication_survival}
    if not settings['sizing']:
        return indication_survival
    else:
#            return self.evaluate_detectability(indication_survival),size
        try:
            return extract_detectability(indication_survival,sizethresh),size
        except:
            print('failure')
            return (0.0,0.0)
