# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 22:00:54 2019

@author: robert.culver
"""
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure
from skimage.morphology import disk
from skimage.filters.rank import entropy
from scipy import ndimage
from scipy import spatial
import cv2

def _castCheck(im):
    'cast to uint8'
    return (im/256.0).astype(np.uint8)

def _castCheck2(im, stdn):
    '''clamps, normalises and casts image to uint8'''
    m = im.mean()
    s = im.std()
    vmax = m + stdn*s
    vmin = m - stdn*s
    im_norm = (np.maximum(np.minimum(im, vmax), vmin) - vmin)/(vmax - vmin)
    return (im_norm*255.0).astype(np.uint8)

def histSimilarity(img1, img2, bins = 200, vmin = 0, vmax = 50000):
    totalCounts1 = np.product(img1.shape)
    totalCounts2 = np.product(img2.shape)
    cnts1 = np.histogram(img1.flatten(),bins = bins,range = (vmin,vmax))[0]
    cnts2 = np.histogram(img2.flatten(),bins = bins,range = (vmin,vmax))[0]
    diffs = np.abs(cnts1/totalCounts1 - cnts2/totalCounts2)
    return diffs.sum()*0.5

def homogSimilarity(img1_, img2_, patchSize = 100, maxFeatures=1000, evalFeatures = 100, show = False):
    '''Homographic distance metric; returns None if not enough keypoints identified for a given pose'''
    img1 = _castCheck(img1_)
    img2 = _castCheck(img2_)
    orb = cv2.ORB_create(patchSize = patchSize)
    orb.setMaxFeatures(maxFeatures)   
    # find the keypoints and descriptors
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)   
    # create BFMatcher object
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)   
    # Match descriptors.
    try:
        matches = bf.match(des1,des2)
    except: # if there are no descriptors
        return None
    # Sort them in the order of their score.
    matches = sorted(matches, key = lambda x:x.distance)
    matches = matches[:evalFeatures]
    if show:
        matchImg = cv2.drawMatches(img1,kp1,img2,kp2,matches, flags=2, outImg = None)
        plt.imshow(matchImg),plt.show()
    # Get kp points
    points1 = np.array([kp1[m.queryIdx].pt for m in matches])
    points2 = np.array([kp2[m.trainIdx].pt for m in matches])
    # Do homography
    homo, mask = cv2.findHomography(points1, points2, cv2.RANSAC)
    if homo is None:
        return None # failure to find
    # calc movement vector required for images to align using corners
    h, w = img1.shape
    ptsAug = np.array([[0, 0, 1], [0, h - 1,  1], [w - 1, h - 1, 1], [w - 1,  0, 1]])
    dstAug = (ptsAug@homo.T)
    mVec = (ptsAug - dstAug)[:,:-1]    
    return np.linalg.norm(mVec, axis = 1).mean()/np.sqrt(h*h + w*w)

def structSimilarity(ref, sim, nPatches, edgeMin = 40, edgeMax = 200):
    ss = _StructuralSimilarity()
    out = ss.ssim(ref, sim, nPatches, edgeMin, edgeMax)
    return np.mean(out)

def greySimilarity(ref, sim):
    diffs = np.abs(ref - sim)
    return diffs.mean() / (2**16 - 1)

class _StructuralSimilarity(object):
    def __init__(self):
        pass
           
    def ssim(self, img1, img2, nPatches, edgeMin = 40, edgeMax = 200):
        '''Compares img to base img'''
        patches1, slices = self.features(img1, nPatches, edgeMin = edgeMin, edgeMax = edgeMax)
        patches2, _ = self.features(img2, nPatches, slices)
        ssims = [self._ssim(p1, p2) for p1, p2 in zip(patches1, patches2)]
        return ssims
    
    def ssimShow(self, img, nPatches, edgeMin = 40, edgeMax = 200):
        '''shows patches being used'''
        vmax = (2**16 -1.0)
        arr = vmax*((img/vmax)*0.5 + 0.5) # a dimmed image
        for p, s in zip(*self.features(img, nPatches, edgeMin =edgeMin, edgeMax = edgeMax)):
            arr[s] = img[s]
        plt.matshow(arr, vmin = 0, vmax = vmax, cmap = 'gray')
        plt.show()
    
    def _ssim(self, im0, im1):
        return 1-measure.compare_ssim(im0,im1,win_size=min(11,(round(min(im0.shape)/2)*2)-1))
        
    def features(self, im, patches = 10, slices = None, edgeMin = 40, edgeMax = 200):
        if slices is None: slices, mask = self._slices(im,patches,edgeMin,edgeMax)
        out = [self.entropy(im[self._growslices(slicepair,im.shape)])[self._shrinkslices(slicepair,im.shape)] for slicepair in slices]
        return out,slices
        
    def _slices(self, im, patches, edgeMin, edgeMax):
        '''identify slices for required number of image patches'''
        #estimate size of object impression
        otsu = self.otsu(im,fac=1.2)
        projslices = self._binranges(otsu)
        shape = tuple([ps.stop-ps.start for ps in projslices])
        assert min(shape)>100, 'provided image too small'
        edge = int(min(shape)/float(1.2*patches))
        #impose limits on patch edge length
        edge = max(min(edge,edgeMax),edgeMin)
        margin = int(edge*1.1)
        #prevent truncated patches at edges
        gradlim = int(np.ceil(edge/2.))
        gradslices = (slice(gradlim,-gradlim),slice(gradlim,-gradlim))
        #limited grad image
        grad = np.zeros(im.shape)
        gradient = self.gradient(im)
        grad[gradslices] = (np.copy(gradient)*ndimage.morphology.binary_dilation(otsu,iterations=5))[gradslices]
        mask = np.zeros(im.shape)
        initslices = []
        centres = []
        for patch in range(int(patches*2)):
            if not np.any(grad>0):
                break
            ind = np.unravel_index(np.argmax(grad),im.shape)
            newslices = (slice(max(0,int(ind[0]-edge/2.)),min(int(ind[0]+edge/2.),im.shape[0])),slice(max(0,int(ind[1]-edge/2.)),min(int(ind[1]+edge/2.),im.shape[1])))
            #cut-off early if only in noise now - inidcated by greatly reduced gradient sum
            if len(initslices)>0 and np.sum(gradient[newslices])<0.1*np.sum(gradient[initslices[-1]]):
                break
            centres.append(ind)
            initslices.append(newslices)
            grad[self._growslices(initslices[-1],im.shape,margin)] = 0
        #select patches to maximise overall spread
        centreinds = [0]
        mask[initslices[centreinds[-1]]] = 1
        slices = [initslices[0]]
        for patch in range(1,min(patches,len(centres))):
            current = np.vstack([centres[ind] for ind in range(len(centres)) if ind in centreinds])
            candidates = np.vstack([centres[ind] for ind in range(len(centres)) if not ind in centreinds])
            canditateinds = [ind for ind in range(len(centres)) if not ind in centreinds]
            distances = spatial.distance.cdist(current,candidates)
            #max min distance - need to convert index given varying entity being indexed
            centreinds.append(canditateinds[np.argmax(np.min(distances,axis=0))])
            slices.append(initslices[centreinds[-1]])
            mask[slices[-1]] = patch+1
        return tuple(slices),mask
    
    def gradient(self,im):
        'return gradient magnitude image'
        #https://www.learnopencv.com/image-alignment-ecc-in-opencv-c-python/
        grad_x = cv2.Sobel(im.astype(np.float32),cv2.CV_32F,1,0,ksize=3)
        grad_y = cv2.Sobel(im.astype(np.float32),cv2.CV_32F,0,1,ksize=3)
        # Combine the two gradients
        out = np.hypot(grad_x,grad_y)
        return out
    
    def otsu(self,im=None,fac=1):
        'return binary image, after Otsu thresholding'
        im8 = _castCheck(im)
        ret,thresh = cv2.threshold(im8,0,np.iinfo(np.uint8).max,cv2.THRESH_OTSU)
        return im8<(ret*fac)
        
    def _binranges(self,im):
        'extract slices for binary image'
        slices = []
        for dim in range(2):
            sum1d = np.sum(im,axis=dim)
            inds = np.where(sum1d)[0]
            slices.append(slice(inds[0],inds[-1]+1))
        return tuple(slices)
    
    def entropy(self,im):
        'return entropy image'
        im = _castCheck(im)
        #entropy calc quite slow
        return entropy(im,disk(min(9,*im.shape)))
    
    def _growslices(self,slicepair,shape,mar=0):
        'expand slices by margin within constraints of image shape'
        return tuple([slice(max(0,sl.start-mar), min(sl.stop+mar,sh)) for sl,sh in zip(slicepair,shape)])

    def _shrinkslices(self,slicepair,shape,mar=0):
        'shrink slices by margin within constraints of image shape, undoing effect of _growslices on local patch'
        return tuple([slice(min(mar,sl.start), min(mar,sl.start)+sl.stop-sl.start) for sl,sh in zip(slicepair,shape)])
    