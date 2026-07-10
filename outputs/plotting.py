# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 10:33:47 2016

@author: nick.brierley
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
eq = np.testing.assert_array_almost_equal
from pdb import set_trace as dbg
import os
from _utilities.defaults import USER_DOCS


publicationType = 'paper'
#publicationType = 'presentation'

#set global plotting defaults
if publicationType=='presentation':
    fontsize=18
    linewidth=2
else: #publicationType=='paper'
    fontsize=11
    linewidth=1
matplotlib.rc('xtick', labelsize=fontsize,direction='in',top=True)
matplotlib.rc('ytick', labelsize=fontsize,direction='in',right=True)
matplotlib.rc('font', family='sans-serif')
matplotlib.rc('legend', fontsize=fontsize-2,fancybox=False,edgecolor='k')
matplotlib.rc('lines', linewidth=linewidth,markeredgewidth=0.4)
matplotlib.rc('font', size=fontsize)


#mask = di['mask']
#arr = di['hof0projsetvals']
##arr = di['hist0projsetvals']
#arr[~mask] = np.nan
#
#fig = plt.figure()
##plt.imshow(arr[:,:,20].T,interpolation='nearest',cmap=plt.cm.plasma,origin='lower',vmin=0,vmax=200)
##plt.imshow(arr[:,:,0].T,interpolation='nearest',cmap=plt.cm.plasma,origin='lower',vmin=0,vmax=120)
##outputs.plotting.figdefaults(fig,'','',colorbar=plt.colorbar(),clabel='Metric')
##fig = plt.figure()
#plt.imshow(arr[:,:,20].T,interpolation='nearest',cmap=plt.cm.plasma,origin='lower',vmin=0)
#outputs.plotting.figdefaults(fig,'','',colorbar=plt.colorbar(),clabel='Metric')
##fig = plt.figure()
##plt.imshow(arr[:,:,-1].T,interpolation='nearest',cmap=plt.cm.plasma,origin='lower',vmin=0,vmax=120)
##outputs.plotting.figdefaults(fig,'','',colorbar=plt.colorbar(),clabel='Metric')
#
#outputs.plotting.createfig(fig,fname='test',format='png')


def createfig(figure,fdir=USER_DOCS,fname=None,format='pdf',transparent=False,bbox_inches='tight',dpi=200,**kwargs):
    'supply matplotlib figure, directory to place in, filename and saving kwargs'
    if publicationType=='presentation':
        #for presentation figs use following block of settings
        format='png'
        dpi=300
    if fname is None: #found by introspection if not supplied
        import inspect
        fname=inspect.stack()[1][3] #may give indexError
        fname=fname.replace('fig_','')
    fo = open(os.path.join(fdir,fname+'.'+str(format)), 'wb')
    kwargs.update(dict(format=format,transparent=transparent,bbox_inches=bbox_inches,dpi=dpi))
    figure.savefig(fo,**kwargs)
    fo.close()
    return

def figdefaults(figure,xlabel,ylabel,colorbar=None,clabel=None,legend=False,legloc='best',reverse=False):
    'apply defaults etc. to figure'
    plt.xlabel(xlabel,fontsize=fontsize)
    if len(xlabel)==0:
        plt.xticks([])
    else:
        plt.ylabel(ylabel,fontsize=fontsize)
    if len(ylabel)==0:
        plt.yticks([])
    else:
        plt.tick_params(labelsize=fontsize)
    if colorbar is not None:
        assert isinstance(clabel,str),'clabel str expected'
        colorbar.set_label(clabel,size=fontsize)
        cblab=plt.getp(colorbar.ax.axes,'yticklabels')
        plt.setp(cblab,size=fontsize)
        colorbar.update_ticks()
    if legend:
        if reverse:
            hands,labs=figure.axes[0].get_legend_handles_labels()
            leg = plt.legend(hands[::-1],labs[::-1],prop={'size':fontsize},loc=legloc)
        else:
            leg = plt.legend(prop={'size':fontsize},loc=legloc)
        leg.get_frame().set_alpha(1)
    return figure

def greyscaleImage(array,vmin=None,vmax=None,fname=None,reverse=False,format='pdf'):
    'convenience method for greyscale images'
    fig = plt.figure()
    if reverse:
        plt.imshow(array,interpolation='nearest',cmap=plt.cm.gray_r,vmin=vmin,vmax=vmax)
    else:
        plt.imshow(array,interpolation='nearest',cmap=plt.cm.gray,vmin=vmin,vmax=vmax)
    ax = plt.gca()
    plt.setp(ax, 'xticklabels', [])
    plt.setp(ax, 'yticklabels', [])
    figdefaults(fig,'','',plt.colorbar(orientation='vertical'),'Greyscale')
    if fname is not None:
        createfig(fig,fname=fname,format=format)
    return fig

def colourMap(array,colorbarlabel=None,vmin=None,vmax=None,fname=None,ticks=False,format='pdf',cmap=plt.cm.plasma):
    'convenience method for colourmaps images'
    fig = plt.figure()
    if colorbarlabel is None:
        colorbarlabel = 'Values'
    plt.imshow(array,interpolation='nearest',cmap=cmap,vmin=vmin,vmax=vmax)
    if not ticks:
        ax = plt.gca()
        plt.setp(ax, 'xticklabels', [])
        plt.setp(ax, 'yticklabels', [])
    figdefaults(fig,'','',plt.colorbar(orientation='vertical'),colorbarlabel)
    if fname is not None:
        createfig(fig,fname=fname,format=format)
    return fig

def imagestack(array,axis,indices,fname=None,format='png',**kwargs):
    'create image stack for array'
    assert array.ndim == 3,'3D array expected'
    figs = []
    for ind in indices:
        slices = tuple([slice(ind,ind+1) if ax==axis else slice(None,None) for ax in range(3)])
        fig = plt.figure()
        plt.imshow(np.squeeze(array[slices]),interpolation='nearest',**kwargs)
        figdefaults(fig,'Elements','Elements',plt.colorbar(orientation='vertical'),'Values')
        if fname is not None:
            createfig(fig,fname=fname+'_'+str(ind),format=format)
        figs.append(fig)
    return figs

def volSlices(vol,ind=100,vmin=None,vmax=None,fname=None,format='png'):
    'subplots of slices'
    assert vol.ndim==3,'3D array expected'
    fig, axs = plt.subplots(1,3)
    arrays = []
    for dim in range(3):
        slices = tuple([slice(ind,ind+1) if el==dim else slice(None) for el in range(3)])
        arrays.append(vol[slices])
    if (vmin is None) or (vmax is None): #even if only one supplied
        stack = np.concatenate([array.flatten() for array in arrays])
        vmin = stack.min()
        vmax = stack.max()
    for dim in range(3):
        im = axs[dim].imshow(np.squeeze(arrays[dim]),interpolation='nearest',cmap=plt.cm.gray,vmin=vmin,vmax=vmax)
        plt.setp(axs[dim], 'xticklabels', [])
        plt.setp(axs[dim], 'yticklabels', [])
        axs[dim].set_aspect('equal', adjustable='box')
    cb = fig.colorbar(im, ax=axs.ravel().tolist())
    figdefaults(fig,'','',cb,'Greyscale')
    if fname is not None:
        createfig(fig,fname=fname+'_'+str(ind),format=format)
    return fig

def hist2Image(im0,im1,levelled=False,refline=False,percentile=None,filename=None,figsize = (9,8),format='pdf',gsMax=2**16-1,grid = False,cmap =plt.cm.gray_r, **kwargs):
    'produce 2D histogram, from provided 2 images'
    fig = plt.figure(figsize=figsize)
    from matplotlib.colors import LogNorm
    diff = np.abs(im1 - im0)
    if levelled:
        im1 = diff
        rangey = (-gsMax,gsMax)
    else:
        rangey = (0,gsMax)
    if percentile is not None:
        halfrange = np.percentile(np.abs(diff.flatten()),percentile)
        print ('half-range value is '+str(halfrange))
    plt.hist2d(im0.flatten(),im1.flatten(),bins=(128,128*(levelled+1)),range=((0,gsMax),rangey),cmap=cmap,norm=LogNorm(),**kwargs)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlim((0,gsMax))
    plt.gca().set_facecolor(plt.cm.get_cmap(cmap)(0))
    if grid: plt.grid()
    if levelled:
        if percentile is not None:
            plt.plot((0,gsMax),(halfrange,)*2,'k-.')
            plt.plot((0,gsMax),(-halfrange,)*2,'k-.')
        plt.ylim((im1.min(),im1.max()))
        figdefaults(fig,'Reference pixel value','Residual pixel value',colorbar=plt.colorbar(),clabel='Count')
    else:
        if percentile is not None:
            hyp = np.sqrt(2)*halfrange #hypothenuse of right-angled triangle
            plt.plot((0,gsMax-hyp),(hyp,gsMax),'k-.')
            plt.plot((hyp,gsMax),(0,gsMax-hyp),'k-.')
        plt.ylim((0,gsMax))
        if refline:
            plt.plot((0,gsMax),(0,gsMax),'k:')
        figdefaults(fig,'Reference pixel value','Simulated pixel value',colorbar=plt.colorbar(),clabel='Count')
    if filename is None:
        plt.show()
    else:
        createfig(fig,fname=filename,format=format)
        plt.close()