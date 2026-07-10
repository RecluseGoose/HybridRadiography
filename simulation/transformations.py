# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 14:56:47 2019

@author: robert.culver
"""
import numpy as np
import engine.rays as rays
import simulation.coordinates
import vtk

class Transformations(object):
    def transl(self, t):
        mat = np.identity(4)
        mat[:-1,-1] = t
        return mat
    
    def invtransl(self, t):
        return np.linalg.inv(self.transl(t))
    
    def rot(self, angs):
        if angs.shape == (1,3):
            print('Assert false coming, ', angs)
            assert False
            angs = angs[0]
        rx,ry,rz = np.deg2rad(angs)
        return simulation.coordinates.euler_matrix(rx,ry,rz,'sxyz')
    
    def invrot(self, angs):
        return np.linalg.inv(self.rot(angs))
    
    def rotabout(self, angs, rot_centre):
        return self.transl(rot_centre)@self.rot(angs)@self.invtransl(rot_centre)
    
    def invrotabout(self, angs, rot_centre):
        return np.linalg.inv(self.rotabout(angs, rot_centre))
        
    def trans2angsAndOffs(self, matrices):
        '''Converts transformation matrices to angles and offsets'''
        assert (matrices.ndim in [2,3])
        if (matrices.ndim == 3):
            angs, offs = [np.array(_) for _ in zip(*[self._trans2angsAndOffs(t) for t in matrices])]
            return angs, offs
        elif (matrices.ndim == 2):
            ang, off = self._trans2angsAndOffs(matrices)
            return ang, off
        
    def angsAndOffs2trans(self, angs, offs):
        return np.array([self.transl(o) for o in offs]) @ np.array([self.rot(a) for a in angs])
        
    def _trans2angsAndOffs(self, trans_matrix):
        rotmat = trans_matrix[:3,:3]
        angs = np.rad2deg(simulation.coordinates.euler_from_matrix(rotmat))
        offs = trans_matrix[:3,-1]
        return angs, offs
    
    def invmats(self, mats):
        return np.array([np.linalg.inv(mat) for mat in mats])

    @staticmethod
    def loadSTL(stlfile):
        '''loads stl into vtk poly data algorithm object'''
        reader = vtk.vtkSTLReader()
        reader.SetFileName(stlfile)
        reader.Update()
        return reader
    
    @staticmethod
    def getCentreOfSTL(stlfile=None, reader = None):
        '''Gets centre of stl'''
        assert (stlfile is None) ^ (reader is None), 'Must specify either stlfile or reader'
        reader = Transformations.loadSTL(stlfile) if (reader is None) else reader
        return np.array(reader.GetOutput().GetCenter())
    
    @staticmethod
    def getBoundsOfSTL(stlfile=None, reader = None):
        '''Gets bounds of stl, x0,x1,y0,y1,z0,z1'''
        assert (stlfile is None) ^ (reader is None), 'Must specify either stlfile or reader'
        reader = Transformations.loadSTL(stlfile) if (reader is None) else reader
        return np.array(reader.GetOutput().GetBounds())
    
    @staticmethod
    def getLengthOfSTL(stlfile=None, reader = None):
        '''Gets bounds of stl, x0,x1,y0,y1,z0,z1'''
        assert (stlfile is None) ^ (reader is None), 'Must specify either stlfile or reader'
        reader = Transformations.loadSTL(stlfile) if (reader is None) else reader
        return np.array(reader.GetOutput().GetLength())  
    
    def matrixToTransform(self, matrix):
        trans = vtk.vtkTransform()
        trans.SetMatrix(matrix.flatten())
        trans.Update()
        return trans

    def applyTransformToPolyData(self,polydata,transform):
        transfilt = vtk.vtkTransformFilter()
        transfilt.SetInputData(polydata)
        transfilt.SetTransform(transform)
        transfilt.Update()
        return transfilt.GetOutput()

    def applyTransformationMatrixToPolyData(self,polydata, matrix):
        trans = self.matrixToTransform(matrix)
        return self.applyTransformToPolyData(polydata,trans)
    
		
class TT_Transformations(Transformations):
    '''Turntable transformations
       
    # generate angles and offsets
    >>> stlfile = 'f:/test_pyramid.stl'
    >>> N = 4
    >>> srcToObjDist = 20.0
    >>> tt = TT_Transformations()
    >>> part_centre = tt.getCentreOfSTL(stlfile)
    >>> part_orientation = np.array([10.0, 0.0, 60.0])
    >>> part_offset = + part_centre - 2.0*np.ones(3)
    >>> camera_elevation = -10.0
    >>> camera_yaw = 15.0
    >>> camera_roll = 25.0
    >>> lateral_offset = 5.0    
    >>> angles, offsets = tt.turntableAnglesOffsetsSweep(N, part_orientation, part_offset, part_centre, srcToObjDist, camera_elevation, camera_yaw, camera_roll, lateral_offset)

    # check things
    >>> print (np.round(part_centre,4))
    [0.6342 0.3776 0.4   ]
    >>> print(np.round(angles,4))
    [[  1.6112 -15.9423  37.4965]
     [ 84.0847  19.291   59.6185]
     [172.0584  -0.9082  96.4632]
     [-99.279  -38.3808  77.2529]]
    >>> print(np.round(offsets,4))
    [[  0.1738  -0.3763 -21.1335]
     [ -1.3348  -0.1416 -19.0323]
     [  0.5412  -1.1836 -17.569 ]
     [  2.0498  -1.4183 -19.6703]]
    
    # Try with specifying angles explicitly
    >>> thetas = [0.0, 90.0, 180.0, 270.0]
    >>> angles, offsets = tt.turntableAnglesOffsetsPositions(thetas, part_orientation, part_offset, part_centre, srcToObjDist, camera_elevation, camera_yaw, camera_roll, lateral_offset)
    
    # check things...
    >>> print (np.round(part_centre,4))
    [0.6342 0.3776 0.4   ]
    >>> print(np.round(angles,4))
    [[  1.6112 -15.9423  37.4965]
     [ 84.0847  19.291   59.6185]
     [172.0584  -0.9082  96.4632]
     [-99.279  -38.3808  77.2529]]
    >>> print(np.round(offsets,4))
    [[  0.1738  -0.3763 -21.1335]
     [ -1.3348  -0.1416 -19.0323]
     [  0.5412  -1.1836 -17.569 ]
     [  2.0498  -1.4183 -19.6703]]
    
    '''
    def __init__(self,rotSign = -1.0):
        assert np.abs(rotSign) == 1.0
        self.rotSign = rotSign  # minus 1 corresponds to nikon machines
    
    def createTurntableRotationTransMats(self, ax_pos, N):
        '''Creates stack of transformation matrices for rot about y-axis'''
        ax_rots = np.zeros((N,3))
        ax_rots[:,1] = (np.linspace(0.0,self.rotSign*360.0,N + 1)[:-1])%360.0
        return np.array([self.rotabout(a,ax_pos) for a in ax_rots])
    
    def alignedTurntableAnglesOffsetsSweep(self, N, part_orientation, part_offset, part_centre, srcToObjDist):
        '''
        Generates set of angles and offsets representing tt rotation
        
        part_orientation    euler angles for rotation about part centre
        
        part_offset         alignment of part centre with tt axis.
                            eg1: value of zero aligns stl centre with tt axis
                            eg2: value of (+centre) aligns stl zero with tt axis
        
        part_centre         vector to centre of part
        
        srcToObjDist        distance of axis from camera
        
        N                   Number of shots around axis
        '''
        matrices = self._alignedTurntableSweep(N, part_orientation, part_offset, part_centre, srcToObjDist)
        # convert to angles and offsets
        angles,offsets = self.trans2angsAndOffs(matrices)
        return angles, offsets
    
    def turntableAnglesOffsetsSweep(self, N, part_orientation, part_offset, part_centre, srcToObjDist,
                               camera_elevation=0.0, camera_yaw=0.0, camera_roll=0.0, lateral_offset=0.0, vert_offset=0.0):
        '''
        Generates set of angles and offsets representing tt rotation, with misalignment
        
        N                   Number of shots around axis
       
        part_orientation    euler angles for rotation about part centre
        
        part_offset         alignment of part centre with tt axis.
                            eg1: value of zero aligns stl centre with tt axis
                            eg2: value of (+centre) aligns stl zero with tt axis
                            eg3: +10 on y coord raises height on tt
        
        part_centre         vector to centre of part
        
        srcToObjDist        distance of axis from camera
               
        camera_elevation    angle between camera view vector and tt plane (positive looks upward)
        
        camera_yaw          yaw of camera (positive looks left)
        
        camera_roll         roll of camera (positive rolls camera to left wing down, world rotates right)
        
        lateral_offset      lateral offset of camera, note vertical offsets are replicated in part_offset,
                            and longitudinal offsets replicated in srcToObjDist (positive moves right)
        '''
        # Start off with fully aligned
        aligned_matrices = self._alignedTurntableSweep(N, part_orientation, part_offset, part_centre, srcToObjDist)
        # Apply misalignment
        final_matrices = self._misalign(aligned_matrices, camera_elevation, camera_yaw, camera_roll, lateral_offset, vert_offset)
        angles, offsets = self.trans2angsAndOffs(final_matrices)
        return angles, offsets
    
    def _alignedTurntableSweep(self, N, part_orientation, part_offset, part_centre, srcToObjDist):
        '''Creates matrices for part oriented and positioned on turntable, no alignments at this stage'''
        ax_pos = np.array([0.0, 0.0, -srcToObjDist])
        # orient part and place wrt axis
        initialPosTransMat = self.transl(part_offset +  ax_pos) @ self.rotabout(part_orientation, np.zeros(3))
        # rotations about axis
        ttRotationTransMats = self.createTurntableRotationTransMats(ax_pos, N)
        # resultant transformation matrices... note broadcasting, (N,4,4) @ (4,4) -> (N,4,4)
        matrices = ttRotationTransMats @ initialPosTransMat
        return matrices                        

    def _misalign(self, aligned_matrices, camera_elevation, camera_yaw, camera_roll, lateral_offset, vert_offset):
        '''Applies misalignments to transformation matrices'''
        # As rotation order in rotabout is x,y,z, we can apply elevation, yaw and roll accordingly
        camera_centre = np.zeros(3)
        elevyaw_matrix = self.rotabout(np.array([-camera_elevation, -camera_yaw, -camera_roll]), camera_centre)
        # Translate world according to lateral offset
        camtransl_matrix = self.transl(np.array([-lateral_offset, -vert_offset , 0.0]))
        # Produce final matrix via matrix multiplication and generate angles and offsets
        final_matrices = camtransl_matrix @ elevyaw_matrix @ aligned_matrices
        return final_matrices
    
    def turntableAnglesOffsetsPositions(self, thetas, part_orientation, part_offset, part_centre, srcToObjDist,
                               camera_elevation=0.0, camera_yaw=0.0, camera_roll=0.0, lateral_offset=0.0, vert_offset=0.0):
        '''
        Generates set of angles and offsets representing tt rotation, with misalignment
        
        thetas              specific rotations around axis
       
        part_orientation    euler angles for rotation about part centre
        
        part_offset         alignment of part centre with tt axis.
                            eg1: value of zero aligns stl centre with tt axis
                            eg2: value of (+centre) aligns stl zero with tt axis
                            eg3: +10 on y coord raises height on tt
        
        part_centre         vector to centre of part
        
        srcToObjDist        distance of axis from camera
               
        camera_elevation    angle between camera view vector and tt plane (positive looks upward)
        
        camera_yaw          yaw of camera (positive looks left)
        
        camera_roll         roll of camera (positive rolls camera to left wing down, world rotates right)
        
        lateral_offset      lateral offset of camera, note vertical offsets are replicated in part_offset,
                            and longitudinal offsets replicated in srcToObjDist (positive moves right)
        '''
        # Start off with fully aligned
        aligned_matrices = self._alignedTurntablePositions(thetas, part_orientation, part_offset, part_centre, srcToObjDist)
        # Apply misalignment
        final_matrices = self._misalign(aligned_matrices, camera_elevation, camera_yaw, camera_roll, lateral_offset, vert_offset)
        angles, offsets = self.trans2angsAndOffs(final_matrices)
        return angles, offsets
    
    def _alignedTurntablePositions(self, thetas, part_orientation, part_offset, part_centre, srcToObjDist):
        '''Based on defined thetas, creates matrices for part oriented and positioned on turntable'''
        ax_pos = np.array([0.0, 0.0, -srcToObjDist])
        # orient part and place wrt axis
        initialPosTransMat = self.transl(part_offset +  ax_pos) @ self.rotabout(part_orientation, np.zeros(3))
        # rotations about axis
        rotspecs = np.zeros((len(thetas),3))
        rotspecs[:,1] = thetas
        ttRotationTransMats = np.array([self.rotabout(t,ax_pos) for t in rotspecs])
        # resultant transformation matrices... note broadcasting, (N,4,4) @ (4,4) -> (N,4,4)
        matrices = ttRotationTransMats @ initialPosTransMat
        return matrices

    
def test():
    stlfile = 'h:/testdata/fork.stl'
    fov = 30.
    xres = yres = 300
    N = 500
    srcToObjDist = 500.0
    flipNorms = False
    
    t = TT_Transformations()
    part_centre = t.getCentreOfSTL(stlfile)
    part_orientation = np.array([40,0.0,3.])
    part_offset = + part_centre - 2.0*np.ones(3)
    camera_elevation = -0.0
    camera_yaw = 0.0
    camera_roll = -90.0
    lateral_offset = 0.0
    
    angles, offsets = t.turntableAnglesOffsetsSweep(N, part_orientation, part_offset, part_centre, srcToObjDist, camera_elevation, camera_yaw, camera_roll, lateral_offset)
    
    mpis = rays.zbuffer(stlfile,xres,yres,fov,angles,offsets,flipNorms)
    non_default = mpis[mpis!=mpis[0,0,0]]
    playStack(mpis, non_default.min(), non_default.max(), loops = 1)

#
def playStack(mpi_stack, vmin=None, vmax=None, rate=60.0, loops=3, cmap ='gray_r'):
    import pylab as pl
    vmin = vmin if not (vmin is None) else mpi_stack.min()
    vmax = vmax if not (vmax is None) else mpi_stack.max()
    img = pl.imshow(mpi_stack[0], vmin = vmin, vmax = vmax, cmap = cmap)
    pl.grid()
    for _ in range(loops):
        for im in mpi_stack:
            img.set_data(im)
            pl.pause(1.0/rate)
            pl.draw()
    pl.close()


##test()
#
#if __name__ == "__main__":
#    import utilities
#    utilities.runDoctest(dict(locals()))
#    pass
