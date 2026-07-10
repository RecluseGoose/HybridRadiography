# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 21:24:14 2019

@author: Robert.Culver
"""
from reconstruction.image_stack import Volume
import xAID
import psutil
import numpy as np

class NikonRecon(object):
    '''
    '''
    def __init__(
            self,
            projDir,
            sigtype = 'Intensities',
            binningIn = 1,
            binningOut = 1,
            chunksize = 200,
            centre = None,
            bhc = 0.0,
            normPatch = None,
            normTarget = 60000,
            streakCorrection = None #[scaling, factor, threshold]
        ):
        ''''''
        assert sigtype in ['Intensities','LineIntegrals'],'signal type invalid'
        self.scaleFactor = 2**16 -1 # xAid's P.data will be zero to this value, convention outside of xAid will be 0.0 to 1.0.
        self.projDir = projDir
        self.binningIn = binningIn # <---- cannot change binning in without setting up recon, which takes a lot of time
        self.binningOutDefault = binningOut
        self.sigtype = sigtype        
        self._chunksize = chunksize
        self.bhcDefault = bhc
        self.streakDefault = streakCorrection
        self.P, self.nProj = self._setupRecon(projDir, binningIn, centre, normPatch, normTarget)
         
    def calcVolume(
            self,
            roi = None,
            outArr = None,
            bhc = None,
            save = None, ##TODO! make this save actually do something
            binningOut = None,
            streakCorrection = None,
        ):
        '''Computes reconstruction'''
        self._setBHC(bhc)
        self._setStreakCorr(streakCorrection)
        self._setBinningOut(binningOut)
        offsets, widths = self._getRoiOffsAndWidths(roi)
        assert(all([w >= 0 for w in widths])), 'Bad ROI widths: {}'.format(widths)
        assert ((outArr is None) or (outArr.shape == widths)),'out shape does not match roi shape'
        self.P.mod_img_vols(widths, offsets = offsets)
        memCheck = self._memCheck(widths, self.P.data.size,outArr)
        if (memCheck == 1):
            vol = self.P.compute_fdk(out=outArr)
        elif (memCheck == 0):
            vol = self._inplaceRecon()            
        else:
            raise MemoryError('Memory categorically not available')
        vol = np.swapaxes(vol, 0, 2)
        self.P.mod_img_vols(widths, offsets = [-offsets[0],-offsets[1],-offsets[2]])
        ## TODO... some gubbins about saving
        return vol
        
    def calcModified( 
            self,
            modProjData,
            roi = None, # <--- roi for calc, nothing to do with modProjData
            outArr = None,
            bhc = None,
            save = None,
            binningOut = None,
            streakCorrection = None,
            mode = 'add',
        ):
        '''Compute reconstruction with modified proj data'''
        origProjData = [(slices, self.P.data[slices].copy()) for slices,_ in modProjData]
        self._modifyProjData(modProjData, mode)
        try:
            vol = self.calcVolume(roi,outArr,bhc,save, binningOut, streakCorrection)
            return vol
        except Exception as e:
            raise(e)
        finally:
            self._modifyProjData(origProjData, 'replace')
            

    def _modifyProjData( self, modProjData , mode):
        '''Modifies P.data with for given modProjData and mode'''
        modes = ['add', 'replace']
        assert mode in modes, '{} not a recognised mode, must be of {}'.format(mode, modes)
        getModified = (lambda slices, proj : self.P.data[slices] + proj) if (mode == 'add') else \
                      (lambda slices, proj : proj)                       if (mode == 'replace') else None
        for slices, proj in modProjData:
                self.P.data[slices] = getModified(slices, proj)
    
    def _setupRecon( self, projDir, binningIn, centre, normPatch, normTarget ):
        '''Helper function which sets up P for recon'''
        assert ((binningIn % 1.0 == 0.0) and (binningIn >= 1)), 'binningIn must be positive integer'
        P = xAID.io.nikon_read(projDir, progress_callback=None, is_geometry_only=True)._as_Tomo()
        P.mod_rot_imgs(-P.get_thetas()[0])
        nProj = P.get_size()
        dask = Volume(projDir, normPatch=normPatch, normTarget=normTarget).projections() # Get dask array of projection data
        ## The bit below is the loading bit that takes ages
        for ind in range(int(np.ceil(nProj/self._chunksize))):
            i0 = int( ind*self._chunksize )
            i1 = int( min((ind+1)*self._chunksize,nProj) )
            P.data[i0:i1] = dask[i0:i1,:,:]
        ## The bit above is the loading bit that takes ages            
        P.data *= self.scaleFactor
        P.data_flags.sig_type = self.sigtype
        P.data_flags.is_roi = False
        # default centreshift correction if none given.
        cs_opt = P.opt_centershift()['opt_val']
        if binningIn != 1:
            P.mod_proj_rebin([binningIn]*2)
        if (centre is None): # corrects detector offsets
            cs_opt = P.opt_centershift()['opt_val']
            P.mod_proj_offsets([cs_opt,None])
        elif (centre is not None) and (centre!=False):
            P.mod_proj_offsets([centre,None])
        return P, nProj
    
    def _getVolShape(self):
        '''Returns default shape of voxel array'''
        projshape = self.P.get_proj_areas()[0]
        return (projshape[0], projshape[1], projshape[0])
    
    def _setBHC(self, bhc):
        '''Sets bhc'''
        valToSet = self.bhcDefault if (bhc is None) else bhc
        self.P.set_beamhard_cupping_factor(valToSet)
    
    def _setStreakCorr(self, streakCorrection):
        valToSet = self.streakDefault if (streakCorrection is None) else streakCorrection
        if (valToSet is not None):
            self.P.set_beamhard_streaks_scaling(valToSet[0])
            self.P.set_beamhard_streaks_factor(valToSet[1])
            self.P.set_beamhard_streaks_threshold(valToSet[2])
    
    def _setBinningOut(self, binningOut):
        '''Updates output binning'''
        valToSet = self.binningOutDefault if (binningOut is None) else binningOut
        if valToSet!=1:
            print("Output binning not tested...")## TODO! not tested! ##
            self.P.mod_img_rebin([valToSet]*3)
    
    def _getRoiOffsAndWidths(self, roi):
        '''Gets offsets and widths of recon vol for given roi'''
        if roi:
            assert (len(roi)==3 and isinstance(roi[0],slice)), 'roi expected to be tuple of three slices'
            offs = tuple([sl.start for sl in roi])
            widths = tuple([sl.stop-sl.start for sl in roi])
        else:
            offs = (0, 0, 0)
            widths = self._getVolShape()
        return (offs, widths)
    
    def _memCheck(self, outShape, dataSize, outArr):
        '''Somehow checks if memory is available'''
        outsize = np.product(outShape)
        dupbytes = dataSize*4
        reqbytes = outsize*4+dupbytes if (outArr is None) else dupbytes
        allbytes = psutil.virtual_memory()
        avbytes = allbytes.available
        surpbytes = avbytes-reqbytes# surplus bytes
        totbytes = allbytes.total
        if (surpbytes)>256*2**20 and (totbytes-dupbytes*2-outsize*4)>256*2**20:
            return 1 # Mem is available
        if (surpbytes+dupbytes)<128*2**20 or (totbytes-dupbytes-outsize*4)<128*2**20:
            return -1 # Mem categorically not available
        else:
            return 0 # In place reconstruction viable, but will require a projection data reset...
    
    def _inplaceRecon(self):
        raise MemoryError('In place recon possible, but not implimented in this repo.')
    #            ## INPLACE RECONSTRUCTION, PROJ DATA RESET REQUIRED
#            fdk = P.compute_fdk(is_inplace=True,out=out)
#            # wiping something???
#            P = P._as_Geometry()
#            gc.collect() ## TODO ??
#            P = P._as_Tomo()
#            setprojdata(parameters['scalein']) #basically, P needs to be set up again.
