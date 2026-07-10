# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 15:14:04 2019

@author: robert.culver
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as interp

from simulation.mapping import MatpathGreyscaleMapping
from _utilities.img_manip import getAllFiles, imread, imresize

#import pickle
#regOutputFile = '../hy_rad/tiles_scan_2/20191105_top_reg.pkl'
#with open(regOutputFile,'rb') as f:
#    geomSetup,mpgsObjKwargs = pickle.load(f)

def convertToMp(gs_input, mpgsObjKwargs, mp_max = 100.0, N = 1001, outsize = (1000,1000)):
    ''''''
    # generate interpolation data
    mpgs = MatpathGreyscaleMapping(**mpgsObjKwargs)
    mp_interp = np.linspace(0.0, mp_max, N)
    gs_interp = mpgs.map(mp_interp)
    print('Min Maxes')
    print(mp_interp.min(),mp_interp.max())
    print(gs_interp.min(),gs_interp.max())
    # augment interp with meaningful endpoints
    # gs = 0 corresponds to infinite mp
    # gs = 65535 corresponds to minimum mp, in this case zero
    mp_interp = np.hstack((mp_interp,(0.0, mp_max)))
    gs_interp = np.hstack((gs_interp,(65535, 0.0)))
    # make interpolator
    gs2mp = get_interp(gs_interp, mp_interp)
    # interpolate input
    if isinstance(gs_input, str):
        assert os.path.isdir(gs_input), 'path not found: {}'.format(gs_input)
        files = getAllFiles(gs_input)
        outshape = (len(files), ) + outsize
        mp_imgs = np.zeros(outshape, dtype = np.float16)
        for i,f in enumerate(files):
            mp_imgs[i] = imresize(gs2mp(imread(f)), outsize[0], outsize[1])
            print('Processing: {:1.2f}%'.format((i+1)*100.0/len(files)))
    elif isinstance(gs_input, np.ndarray):
        mp_imgs = imresize(gs2mp(gs_input), outsize[0], outsize[1])
    return np.maximum(mp_imgs, 0.0)

def get_interp(x,y):
    # x data for interp must be strictly ascending
    x_unique, idx = np.unique(x,return_index=True)
    y_unique = y[idx]
    i_sort = x_unique.argsort()
    x_interp = x_unique[i_sort]
    y_interp = y_unique[i_sort]
    # make interpolator
    return interp.Akima1DInterpolator(x_interp, y_interp)


def exampleApplication():
    '''specific application of material path reconstr. for RR Tiles data (33740)'''
    import pickle

    regOutputFile = 'C:/Users/robert.culver/Documents/git/HybridRadiography/hy_rad/tiles_scan_2/20191105_top_reg.pkl'
    with open(regOutputFile,'rb') as f:
        geomSetup,mpgsObjKwargs = pickle.load(f)
    
    #%%============================================================================
    # Bespoke reconstr.
    # =============================================================================
    import os
    
    outdir = "D:/mat_path_imgs"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
        from _utilities.img_manip import imwrite
        
        projdir = "D:/Data/32911_Top Half_RQ0469-08_18April19_2019_04_08_09_31_53/"
        mpImgStack = convertToMp(projdir, mpgsObjKwargs, outsize = (1000,1000))
        norm = 65535.0/mpImgStack.max()
        mpImgStack *= norm
        mpImgStack = mpImgStack.astype(np.uint16) # round down and integise
        nones = [imwrite(os.path.join(outdir,'mp_img_{:04d}.tif'.format(i)),m) for i,m in enumerate(mpImgStack)]
    
        del mpImgStack
    
    from reconstruction.recon import NikonRecon
    
    cba1 = NikonRecon(outdir,sigtype = 'LineIntegrals',centre=-5.9)
    vol1 = cba1.calcVolume()
    cba2 = NikonRecon("D:/resized",sigtype = 'Intensities',centre=-5.9, bhc = 0.4, streakCorrection = [0.0,0.4,5.0])
    vol2 = cba2.calcVolume()
    
    #%% Plot BHC1
    sub1 = vol1[420:480,837,510:570]
    sub2 = vol2[420:480,837,505:565]
    vol1_n = vol1/ (sub1.max() - sub1.min())
    vol2_n = vol2/ (sub2.max() - sub2.min())
    
    inds = [822,836,842,852,856,859]
    nRows = len(inds)
        
    fig, big_axes = plt.subplots(figsize= (10,28), nrows=nRows, ncols=1,) 
    
    for row, big_ax in enumerate(big_axes, start=1):
        big_ax.set_title("Slice %s \n" % inds[row-1], fontsize=16)
        big_ax.axis('off')
        big_ax._frameon = False
    
    for i in range(1,2*nRows + 1):
        j = inds[int((i-0.5)/2)]
        ax = fig.add_subplot(nRows,2,i)
        toPlot = vol1_n[250:550,j,450:-250]-0.05 if not (i%2) else vol2_n[250:550,j,450:-250]   #if even
        ax.imshow(toPlot, vmin = 0.0, vmax = 1.0, cmap = 'gray')
        ax.axis('off')
        toLabel = 'Custom BHC' if not (i%2) else 'Standard BHC'
        ax.set_title(toLabel)
        
    #fig.set_facecolor('w')
    plt.tight_layout()
    plt.show()
    fig.savefig('BHC_comparison1.pdf')
    
    #%% plot BHC2 and 3
    for i in [580,600]:
        fig,axs = plt.subplots(1,2,figsize = (7,10))
        fig.suptitle('Slice {}\n'.format(i), fontsize = 16)
        axs[1].imshow(vol1_n[:,i,500:750] - 0.1, vmin = 0.0, vmax = 1.0, cmap = 'gray')
        axs[0].imshow(vol2_n[:,i,500:750], vmin = 0.0, vmax = 1.0 , cmap = 'gray')
        axs[0].set_title("\n\nStandard BHC")
        axs[0].axis('off')
        axs[1].set_title("\n\nCustom BHC")
        axs[1].axis('off')
        fig.tight_layout()
        fig.savefig('BHC_comparison_{}.pdf'.format(i))
        
    i= 750
    fig,axs = plt.subplots(1,2,figsize = (7,10))
    fig.suptitle('Slice {}\n'.format(i), fontsize = 16)
    axs[1].imshow(vol1_n[:,i,450:700], vmin = 0.0, vmax = 1.0, cmap = 'gray')
    axs[0].imshow(vol2_n[:,i,450:700], vmin = 0.0, vmax = 1.0 , cmap = 'gray')
    axs[0].set_title("\n\nStandard BHC")
    axs[0].axis('off')
    axs[1].set_title("\n\nCustom BHC")
    axs[1].axis('off')
    fig.tight_layout()
    fig.savefig('BHC_comparison_{}.pdf'.format(i))
    # =============================================================================
    # Plotting from here onwards
    # =============================================================================
        
    
        
    from simulation.engine_interface import TurntableMatpath, SimSetup
    
    simSetup = SimSetup("D:/testdata/cad_aligned_cut.stl")
    
    
    
    ref = imread("d:/resized_top/32911_Btm Half_RQ0548-08_08May19_0001.tif")
    ttmp = TurntableMatpath(simSetup, geomSetup)
    mps = ttmp.getMatPathImgs([0])[0]
    mpgs = MatpathGreyscaleMapping(**mpgsObjKwargs)
    gs = mpgs.map(mps)
    
    import matplotlib.pyplot as plt
    
    from matplotlib.colors import LogNorm
    from outputs.plotting import hist2Image
    
    
    #%% side-by-side comparison
    import scipy.ndimage as snd
    f,ax = plt.subplots(1,3,figsize = (18,6))
    pcm = ax[1].imshow(snd.gaussian_filter(gs,1.0), cmap = 'gray', vmin = 0.0, vmax = 65535)
    ax[1].axis('off')
    ax[1].set_title('Simulated Radiograph')
    
    pcm = ax[0].imshow(ref, cmap = 'gray', vmin = 0.0, vmax = 65535)
    ax[0].axis('off')
    ax[0].set_title('Experimental Radiograph')
    
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    
    jib= ax[2].imshow(snd.gaussian_filter(mps,1.0), cmap = 'gray_r', vmin = 0.0, vmax = 20)
    #divider = make_axes_locatable(ax[2])
    
    ax[2].axis('off')
    ax[2].set_title('Material Path')
    plt.colorbar()
    plt.colorbar(jib ,ax=ax[2])
    
    #f.tight_layout()
    plt.savefig('D:/radiographs.pdf')
    
    #%% Beam hardening illustration
    plt.figure()
    mp2plot = mps[mps!=0]
    ref2plot = ref[mps!=0]
    xs = np.linspace(0,14.5,1001)
    ys = mpgs.map(xs)
    plt.hist2d(mp2plot, -np.log(ref2plot/65535.0)/mp2plot, bins = (100,100), cmap ='gray_r', norm = LogNorm(), range = ((0,14),(0,2)))
    cbar = plt.colorbar()
    cbar.set_label('Counts')
    plt.plot(xs, -np.log(ys/65535.0)/xs, 'r', linewidth = 2)
    plt.ylabel('Absorption Coefficient (1/mm)')
    plt.xlabel('Material Depth (mm)')
    plt.savefig('d:/Beam Hardening.pdf')
    
    #%% Ref vs sim 2d hist
    hist2Image(ref/65535.0, gs/65535.0, gsMax = 1.0, refline = True, percentile = 95.0, filename = "d:\hist2d_gs_comp")
    
    #%% MP vs I
    plt.figure()
    plt.hist2d(mp2plot, ref2plot/65535.0, bins = (100,100), cmap ='gray_r', norm = LogNorm(), range = ((0,14),(0,1)))
    cbar = plt.colorbar()
    cbar.set_label('Counts')
    plt.plot(xs, ys/65535.0, 'r', linewidth = 2)
    plt.ylabel('Greyscale Value')
    plt.xlabel('Material Depth (mm)')
    plt.savefig('d:/IvsMP.pdf')