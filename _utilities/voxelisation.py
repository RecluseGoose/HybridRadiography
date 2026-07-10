"""
Created on Wed Oct 04 14:31:10 2017

Functions for voxelisation of stl meshes and vtkPolyData objects.

@author: robert.culver
"""

import vtk
import numpy as np
import vtk.util.numpy_support as numpy_support
from multiprocessing import cpu_count

NUM_CORES = cpu_count()         # Used to multithread _makeSurfaceVox... which is a ridiculously expensive function
SURFACE_THICKNESS = 0.90        # Fudgefactor, used to scale the wall thickness (in units of vox_spacing parameter) for surface mode
FUDGE_OFFSET = [-0.5,-0.5,-0.5]    #[-0.0660906 , -0.40200617, -0.29927936] # Fudgefactor for resolving translation issues

def stlToVox(filename, vox_shape = None, vox_spacing = None, printOutput = True, mode = 'solid', offset = [0.0,0.0,0.0]):
    '''Supply an stl filename, and output a solid voxel array

    Usage: supply either (1) vox_shape (final voxel grid shape)
                      or (2) vox_spacing (physical distance between each voxel... voxel resolution)

           modes available (1) 'solid' (attempts to identify inside/outside to create vox array with filled-in regions)
                           (2) 'surface' (voxel array is true where mesh cell exists... does not fill in solid)...
                                unfortunately, this is very splodgy, I'm not entirely sure why.

           offset: Option to supply an offset (in voxel/vox_spacing units), in the case that you are generating a sub voxel
                   array and you need the grid to line up. Do not use as a fudge factor.

    >>> ## ---- SET INPUT FILE ---- ##
    >>> filename =  'H:/testdata/testsphere.stl'

    >>> ## ------ SOLID MODE ------ ##
    >>> mode = 'solid'
    >>> # Create vox1 and vox2... should ideally be the same voxel arrays, but there's an issue somewhere
    >>> vox1 = stlToVox(filename,vox_spacing = 0.025, mode = mode)
    Generating voxel array of size (81,81,81), with spacing 0.025.
    >>> vox2 = stlToVox(filename,vox_shape = (81,81,81), mode = mode)
    Generating voxel array of size (81,81,81), with spacing 0.0249999982615.
    >>> #Test vox1 and vox2 are the same
    >>> np.all(vox1 == vox2), (vox1.sum(), vox2.sum())
    (True, (234528, 234528))
    >>> ## ----- SURFACE MODE ----- ##
    >>> mode = 'surface'
    >>> # Create vox1 and vox2... should ideally be the same voxel arrays, but there's an issue somewhere
    >>> vox3 = stlToVox(filename,vox_spacing=0.025, mode = mode)
    Generating voxel array of size (81,81,81), with spacing 0.025.
    >>> vox4 = stlToVox(filename,vox_shape = (81,81,81), mode = mode)
    Generating voxel array of size (81,81,81), with spacing 0.0249999982615.
    >>> #Test vox3 and vox4 are the same
    >>> np.all(vox3 == vox4), (vox3.sum(), vox4.sum())
    (True, (44096, 44096))
    '''
    return polyDatToVox(_stlToPolyDat(filename), vox_shape, vox_spacing, printOutput, mode, offset)

def polyDatToVox(polyDat, vox_shape = None, vox_spacing = None, printOutput = True, mode = 'solid', offset = [0.0,0.0,0.0]):
    '''Supply a vtkPolyData object, and output a solid voxel array

    Usage: supply either (1) vox_shape (final voxel grid shape)
                      or (2) vox_spacing (physical distance between each voxel... voxel resolution)

           modes available (1) 'solid' (attempts to identify inside/outside to create vox array with filled-in regions)
                           (2) 'surface' (voxel array is true where mesh cell exists... does not fill in solid)

           offset: Option to supply an offset (in voxel/vox_spacing units), in the case that you are generating a sub voxel
                   array and you need the grid to line up. Do not use as a fudge factor.
    '''
    # Check mode, solid or surface.
    assert (mode.lower() in ['solid','surface'])
    # Calculate spacing (or dimensions) based on input
    spacing, dim = _argsToDim(polyDat,vox_shape,vox_spacing,offset)
    if printOutput: print('Generating voxel array of size (%d,%d,%d), with spacing (%s, %s, %s).'%(dim + tuple(spacing)))
    # Get the vtk array based on the mode
    img_vtk = _makeSolidVox(polyDat,dim,spacing,offset) if (mode.lower() == 'solid') else _makeSurfaceVox(polyDat,dim,spacing,offset)
    # Convert output into numpy array
    imArr = numpy_support.vtk_to_numpy(img_vtk.GetPointData().GetScalars())
    outs = imArr.reshape(np.flipud(img_vtk.GetDimensions()))
    return outs.T

def _makeSolidVox(polyDat, dim, spacing, offset):
    '''Use method used in https://www.vtk.org/Wiki/VTK/Examples/Cxx/PolyData/PolyDataToImageData to create voxel array'''
    # Setup white image of correct size
    whiteImage = vtk.vtkImageData()
    whiteImage.SetSpacing(spacing)
    whiteImage.SetDimensions(dim)
    whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
    whiteImage.AllocateScalars(vtk.VTK_UNSIGNED_CHAR,1)
    # Set origin
    bounds = [0]*6
    polyDat.GetBounds(bounds)
    origin = [0]*3
    origin[0] = bounds[0] + spacing[0] / 2.0 + spacing[0]*FUDGE_OFFSET[0] - spacing[0]*offset[0]
    origin[1] = bounds[2] + spacing[1] / 2.0 + spacing[1]*FUDGE_OFFSET[1] - spacing[1]*offset[1]
    origin[2] = bounds[4] + spacing[2] / 2.0 + spacing[2]*FUDGE_OFFSET[2] - spacing[2]*offset[2]
    whiteImage.SetOrigin(origin)
    # Use these stencil objects to create the vtk array... I'm not sure exactly how this works...
    # Documentation for these things are sparse... see original example in link above.
    pol2stenc = vtk.vtkPolyDataToImageStencil()
    pol2stenc.SetInputData(polyDat)
    pol2stenc.SetOutputOrigin(origin)
    pol2stenc.SetOutputSpacing(spacing)
    pol2stenc.SetOutputWholeExtent(whiteImage.GetExtent())
    pol2stenc.Update()
    imstence2im = vtk.vtkImageStencilToImage()
    imstence2im.SetInputConnection(pol2stenc.GetOutputPort())
    imstence2im.Update()
    return imstence2im.GetOutput()

# This method is horrendously slow, I think it's using quite old vtk functions which haven't been properly maintained.
#def _makeSurfaceVox(polyDat, dim):
#    '''Use VoxelModeller to create the surface (hollow) voxel array'''
#    voxMod = vtk.vtkVoxelModeller()
#    voxMod.SetScalarTypeToUnsignedChar()
#    voxMod.SetInputData(polyDat)
#    voxMod.SetModelBounds(polyDat.GetBounds())
#    voxMod.SetSampleDimensions(dim)
#    voxMod.Update()
#    return voxMod.GetOutput()

def _makeSurfaceVox(polyDat, dim, spacing, offset):
    '''Use VoxelModeller to create the surface (hollow) voxel array. The results are very splodgy, but it should do the job...
    based on example found at https://www.vtk.org/Wiki/VTK/Examples/Cxx/PolyData/ImplicitModeller'''
    # Use implicit modeller
    impMod = vtk.vtkImplicitModeller()
    impMod.SetInputData(polyDat)
    impMod.SetModelBounds(polyDat.GetBounds())
    impMod.SetSampleDimensions(dim)
    impMod.SetProcessModeToPerVoxel()
    impMod.SetNumberOfThreads(NUM_CORES)
    impMod.Update()
    # Use contour filter... the set value sets the thickness of the wall in the voxel array.
    contFilt = vtk.vtkContourFilter()
    contFilt.SetValue(0,np.mean(spacing)*SURFACE_THICKNESS)
    contFilt.SetInputConnection(impMod.GetOutputPort())
    # Try disabling and enabling various things to try and make thigns faster (I don't think this works)
    contFilt.SetOutputPointsPrecision(1)
    contFilt.SetUseScalarTree(1)
    contFilt.ComputeGradientsOff()
    contFilt.ComputeNormalsOff()
    contFilt.ComputeScalarsOff()
    contFilt.Update()
    # Use the solid vox using the output of contfilt as the polydata...
    return _makeSolidVox(contFilt.GetOutput(),dim,spacing,offset)

def _argsToDim(polyDat, vox_shape, vox_spacing, offset = [0.0,0.0,0.0]):
    '''Returns the required output vox array shape'''
    args = [vox_shape, vox_spacing]
    assert ((None in args) and not all([arg is None for arg in args])), 'Must set either vox_shape or vox_spacing.'
    if (vox_shape is None):
        # Calculate required final vox shape...
        bounds = [0]*6
        polyDat.GetBounds(bounds)
        spacing = vox_spacing if np.iterable(vox_spacing) else tuple([vox_spacing]*3)
        dim=tuple([int(np.round((bounds[i * 2 + 1] - bounds[i * 2] + spacing[i]*offset[i]) / spacing[i])) + 1 for i in range(3)])
    else:
        assert ~np.all(offset == 0.0),'offset not implimented'
        # Use voxel shape as specified
        dim = tuple(vox_shape)
        xmin,xmax,ymin,ymax,zmin,zmax = polyDat.GetBounds()
        spac = np.mean([(xmax-xmin)/(dim[0]-1), (ymax-ymin)/(dim[1]-1), (zmax-zmin)/(dim[2]-1)])
        spacing = tuple([spac]*3)
    return spacing, dim

def _stlToPolyDat(filename):
    '''Converts stl to vtkPolyData object'''
    source = vtk.vtkSTLReader()
    source.SetFileName(filename)
    source.Update()
    return source.GetOutput()