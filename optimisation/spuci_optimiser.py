# -*- coding: utf-8 -*-
"""
Created on Sat Oct 20 02:45:10 2018

SP-UCI optimiser, based on the following paper

"A new evolutionary search strategy for global optimization of high-dimensional problems"
(Chu, Gao, Sorooshian) https://www.sciencedirect.com/science/article/pii/S0020025511003318

@author: Robert
"""
import matplotlib.pyplot as plt
import numpy as np
import sklearn.decomposition
import sklearn.preprocessing
import scipy.spatial
#import deap.benchmarks

import os
import shutil
import pickle
import time

from optimisation.coordinate_handling import ParameterCoord

class Vertex():
    def __init__(self,coord,fitness,evalFun,weight,parameterHandler):
        if fitness is None:
            assert callable(evalFun)
        self.weight = weight
        self.coord = coord
        self.fitness = fitness
        self.evalFun = evalFun
        self.parameterHandler = parameterHandler

    def evaluate(self):
#        self.fitness = self.weight*self.evalFun((self.parameterHandler.unnormalise(self.coord)),)[0]
        self.fitness = self.weight*self.evalFun((self.parameterHandler.unnormalise(self.coord)),)
    
    def __getstate__(self):
        if hasattr(self,'evalFun'):
            # If using SPUCI._trackedFun, this cannot be serialised, so just delete
            # for now. The eval fun will be reset in SP_UCI._loadHistory.
            try:
                pickle.dumps(self.evalFun)
            except (pickle.PicklingError, AttributeError):
                del self.evalFun
        return self.__dict__
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        

class Complex():
    def __init__(self, vertices):
        self.vertices = vertices

    def sort(self):
        # ensure all verts evaluated
        self.evaluate()
        # sort for with ascending fitness values
        fitvals = [vert.fitness for vert in self.vertices]
        newOrder = sorted(range(len(self.vertices)), key = lambda i:fitvals[i])
        self.vertices = [self.vertices[i] for i in newOrder]

    def evaluate(self):
        [vert.evaluate() for vert in self.vertices if (vert.fitness is None)]


class SP_UCI():
    '''
    n - dimensionality of the problem
    m - number of complexes
    p - number of points per complex
    obj - objective to minimise

    # Test using 30D griewank
    >>> bounds = [[-10.0,+10.0]]*30
    >>> import deap.benchmarks
    >>> s = SP_UCI(deap.benchmarks.griewank,bounds,maxmin='min',m=5,p=None,edges=None,seed=174)
    >>> s.optimise(100,1e5,verbose=False)
    >>> int(s._getAllFitness().min()*1e12)
    5982028

    # Test using 31D Ackley
    >>> bounds = [[-10.0,+10.0]]*31
    >>> s = SP_UCI(deap.benchmarks.ackley,bounds,maxmin='min',m=5,p=None,edges=None,seed=174)
    >>> s.optimise(100,1e5,verbose=False)
    >>> int(s._getAllFitness().min()*1e6)
    10511
    
    >>> bestCoord = s.getBest()
    >>> '{:.5f}'.format(bestCoord.sum())
    '-0.00873'
    '''
    def __init__(self,obj,bounds,maxmin='min',m=5,p=None,edges=None,names=None,seed=0):
        np.random.seed(seed + 20)
        assert maxmin.lower() in ['max','min'],'Must chose max or min.'
        self.weight = 1.0 if maxmin.lower() == 'min' else -1.0
        self.parameterHandler = ParameterCoord(bounds = bounds, edges = edges, names = names)
        self.m = m
        self.n = len(bounds)
        self.p = self.n + 20 if (p is None) else p
        self.obj = self._trackedFun(obj)
        self.complices = None
        self.iterCnt = 0

    def _initialComplices(self,n,m,p,initPointsUnnorm = None):        
        if (initPointsUnnorm is None): initPointsUnnorm = np.zeros((0,n))
        assert (initPointsUnnorm.shape[1] == n)
        nVertsFromRandom = m*p - initPointsUnnorm.shape[0]
        verts = [self._newVertex(np.random.random(n)) for p_ in range(nVertsFromRandom)] 
        verts += [self._newVertex(self.parameterHandler.normalise(p_)) for p_ in initPointsUnnorm]    
        complices = [Complex(verts[(m_*p):(m_*p)+p]) for m_ in range(m)]
        [c.evaluate() for c in complices]
        [c.sort() for c in complices]
        return complices
        
    def _trackedFun(self,fun): #TODO, whilst this is 'pythonic', it is convoluted and creates pickling difficulties.
        '''Wraps function to allow tracking of all args in and all vals out'''
        def wrapped(args):
            val = fun(args)[0]
            wrapped.args.append(args)
            wrapped.vals.append(val)
            wrapped.ts.append(time.time())
            return val
        wrapped.args = []
        wrapped.vals = []
        wrapped.ts = []
        return wrapped

    def _newVertex(self,coord):
        return Vertex(coord,None,self.obj,self.weight,self.parameterHandler)

    def optimise(self,maxIter=50, maxEvals=1e5, xTol=1e-4, yTol=1e-4,verbose=True,nThreads=1,startCoords=None,savefile=None):
        if (self.complices is None):
            if (savefile is not None) and os.path.exists(savefile):
                self._loadHistory(savefile)
            else:
                self.complices = self._initialComplices(self.n,self.m,self.p,startCoords)            
        self._newCoords = self._getAllCoords()
        self._newFitness = self._getAllFitness()
        if verbose: print("iter\tnEvals\t\tfitness")
        # randomly shuffle points into m complexes and sort each complex
        while(maxIter!=0):
            self.complices = self.shuffleComplices(self.complices)
            [c.sort() for c in self.complices]
            self.complices = [self._processComplex(comp) for comp in self.complices]
            self.iterCnt += 1
            if savefile is not None: self.saveHistory(savefile)
            # check termination conditions
            if not self._resumeOptimisation(maxIter,maxEvals,xTol,yTol,verbose): break

    def _processComplex(self,comp):
        '''This is the SP_UCI algorithm in a nutshell...'''
        self.dimensions(comp)   # Reclaim lost dimensions for complex
        self.evolve(comp)       # Evolve using Nelder Mead for best n+1 points in complex
        self.resample(comp)     # Resample using multivariate sampling
        return comp

    def _resumeOptimisation(self,maxIter,maxEvals,xTol,yTol,verbose):
        '''helper function: returns True when optimisation should be resuming'''
        self._oldCoords = self._newCoords
        self._newCoords = self._getAllCoords()
        self._oldFitness = self._newFitness
        self._newFitness = self._getAllFitness()
        xTolMetric = np.abs(self._oldCoords-self._newCoords).mean()
        yTolMetric = 2.0*np.abs((np.abs(self._oldFitness) - np.abs(self._newFitness))).mean()/(np.abs(self._oldFitness) + np.abs(self._newFitness)).mean()
        evalCnt = len(self.obj.vals)
        retVal = True
        if verbose: print("{0}\t{1:1.3e}\t{2:1.3e}".format(self.iterCnt,evalCnt,self._newFitness.min()))
        if (xTolMetric < xTol):
            if verbose: print ("Terminating after {0} iterations with xTol {1:1.3e} < {2:1.3e}".format(self.iterCnt,xTolMetric,xTol))
            retVal = False
        if (yTolMetric < yTol):
            if verbose: print ("Terminating after {0} iterations with yTol, {1:1.3e} < {2:1.3e}".format(self.iterCnt,yTolMetric,yTol))
            retVal = False
        if (evalCnt >= maxEvals):
            if verbose: print ("Terminating after {0} iterations with maxEvals, {1} >= {2}".format(self.iterCnt,evalCnt,maxEvals))
            retVal = False
        if (self.iterCnt >= maxIter):
            if verbose: print ("Terminating with maxIter = {}".format(self.iterCnt))
            retVal = False
        return retVal

    def _getAllFitness(self):
        '''for diagnostic purposes'''
        return np.array([vert.fitness for comp in self.complices for vert in comp.vertices])

    def _getAllCoords(self):
        '''for diagnostic purposes'''
        return np.array([vert.coord for comp in self.complices for vert in comp.vertices])

    def shuffleComplices(self,complices):
        '''shuffles vertices in a list of complices, and generates new complices'''
        m = len(complices)
        p = len(complices[0].vertices)
        vertices = sum([c.vertices for c in complices],[])
        np.random.shuffle(vertices)
        return [Complex(vertices[p*i : p*i+p]) for i in range(m)]

    def dimensions(self,complex_,lostDimThresh = 0.2):
        '''detects gradients along lost principal components'''
        xs = np.vstack([v.coord for v in complex_.vertices])
        n = xs.shape[1]
        # Get lost principal components using PCA
        normaliser= sklearn.preprocessing.StandardScaler()
        normaliser.fit(xs)
        xs_n = normaliser.transform(xs)
        pca = sklearn.decomposition.PCA(n)
        pca.fit(xs_n)
        expectedVariance = 1.0/n
        threshVariance = expectedVariance*lostDimThresh
        lostPCs = pca.components_[pca.explained_variance_<threshVariance]
        if (len(lostPCs) > 0):
            centroid_n = 0.0
            radius_n = scipy.spatial.distance.pdist(xs_n).max()
            # Loop through each lostPC
            for l in lostPCs:
                complex_.sort()
                # try positive step
                a = np.random.normal(2,1)
                posStep_n = centroid_n + a*radius_n*l
                posVert = self._newVertex(normaliser.inverse_transform(posStep_n))
                # if no better, try negative step
                if (self._replaceWorst(complex_,posVert)): continue
                negStep_n = centroid_n - a*radius_n*l
                negVert = self._newVertex(normaliser.inverse_transform(negStep_n))
                self._replaceWorst(complex_,negVert)

    def _replaceWorst(self,complex_,newVert):
        '''if vert is better than worst vertex, worst vertex is replaced by vert'''
        if (newVert.fitness is None):
            newVert.evaluate()
        if (newVert.fitness < complex_.vertices[-1].fitness):
            complex_.vertices[-1] = newVert
            complex_.sort()
            return True
        else:
            return False

    def evolve(self,complex_):
        xs = np.vstack([v.coord for v in complex_.vertices])
        p,n = xs.shape
        for iteration in range(n+1):
            complex_.sort()
            # assign triangular pdf to vertices
            triProbs = 1.0*(p-np.arange(1,p))
            triProbs /= triProbs.sum()
            # select d+1 vertices in complex, store in S
            simplexInds = np.random.choice(np.arange(1,p),replace=False,p=triProbs,size=n)
            simplex = Complex([complex_.vertices[0]] + [complex_.vertices[i] for i in simplexInds])
            # perform a simple nmo iteration on simplex
            simplex = self._nmo(simplex)
            # update complex
            complex_.vertices[0] = simplex.vertices[0]
            [complex_.vertices.__setitem__(i_2,simplex.vertices[i]) for i_2,i in zip(simplexInds,range(1,n+1))]

    def resample(self,complex_):
        complexPts = np.array([v.coord for v in complex_.vertices])
        centroid = complexPts.mean(0)
        p,n = complexPts.shape
        cov = np.cov(complexPts.T)
        try:    ##TODO... this is troubleshooting inf or nans in cov
            newCoords = np.random.multivariate_normal(centroid,cov,size = p)
        except ValueError:
            np.save("d:/complexPts.npy",complexPts)
            # attempt to rectify
            complexPts = complexPts + (0.5-np.random.random(complexPts))*0.01*complexPts.std(0)
            centroid = complexPts.mean(0)
            p,n = complexPts.shape
            cov = np.cov(complexPts.T)
            newCoords = np.random.multivariate_normal(centroid,cov,size = p)
        # combine all points
        allVerts = [self._newVertex(newCoord) for newCoord in newCoords] + complex_.vertices
        uncroppedComplex = Complex(allVerts)
        uncroppedComplex.evaluate()
        uncroppedComplex.sort()
        [complex_.vertices.__setitem__(i,uncroppedComplex.vertices[i]) for i in range(p)]

    def _nmo(self,simplex):
        '''a single nelder mead iteration'''
        simplex.evaluate()
        simplex.sort()
        ndim = len(simplex.vertices) - 1
        centroid = np.mean([simplex.vertices[i].coord for i in range(ndim)],0)
        worst = simplex.vertices[-1]
        secondWorst = simplex.vertices[-2]
        bestFitness = simplex.vertices[0].fitness
        # reflect
        refl = self._newVertex(2.0*centroid - worst.coord)
        refl.evaluate()
        if ((bestFitness < refl.fitness) and (refl.fitness < secondWorst.fitness)):
            offspring = refl
        elif (refl.fitness <= bestFitness):
            # expand
            exp = self._newVertex(2.0*refl.coord-centroid)
            exp.evaluate()
            offspring = exp if (exp.fitness < refl.fitness) else refl
        elif ((secondWorst.fitness <= refl.fitness) and (refl.fitness < worst.fitness)):
            # contract outside
            ctro = self._newVertex(centroid + 0.5*(refl.coord-centroid))
            ctro.evaluate()
            offspring = ctro if (ctro.fitness < refl.fitness) else refl
        elif (worst.fitness <= refl.fitness):
            # contract inside
            ctri = self._newVertex(centroid + 0.5*(worst.coord-centroid))
            ctri.evaluate()
            if (ctri.fitness < worst.fitness):
                offspring = ctri
            else:
                # random point
                simplexPts = np.array([v.coord for v in simplex.vertices])
                diag = np.cov(simplexPts.T).diagonal()
                diag = 2.0*(diag + diag.mean())
                ## TODO! check this is actually what the paper is recommending...
                offspring = self._newVertex(np.random.normal(centroid,diag))
#                offspring = self._newVertex(random.normalvariate(centroid,diag))
                offspring.evaluate()
        else:
            print(refl.fitness, [v.fitness for v in simplex.vertices])
            assert(False),"This should never happen"
        simplex.vertices[-1] = offspring
        return simplex

    def plotEvals(self):
        plt.plot(np.minimum.accumulate(self.obj.vals))
        
    def saveHistory(self,filename):
        assert filename.split('.')[-1].lower() == 'pkl'
        # Write temp
        filetowrite = '.'.join(filename.split('.')[:-1] + ['_pkl'])
        with open(filetowrite,'wb') as f:
            data = dict(args=self.obj.args,
                        vals=self.obj.vals,
                        ts = self.obj.ts,
                        names = self.parameterHandler.names,
                        complices = self.complices,
                        iterCnt = self.iterCnt,
                        randstate = np.random.get_state())
            pickle.dump(data,f)
        # Replace old
        if os.path.exists(filename): os.remove(filename)
        os.rename(filetowrite,filename)
            
    def loadHistory(self, filename):
        '''Loads pkl into dict'''
        assert os.path.exists(filename)
        with open(filename,'rb') as f:
            data = pickle.load(f)
        return data
    
    def _loadHistory(self,filename):
        '''Loads data into instance'''
        data = self.loadHistory(filename)
        self.obj.args = data['args']
        self.obj.vals = data['vals']
        self.obj.ts = data['ts']
        self.parameterHandler.names = data['names']
        self.complices = data['complices']
        self.iterCnt = data['iterCnt']
        np.random.set_state(data['randstate'])
        ## SPUCI._trackedFun cannot be pickled, must reload into complex vertices
        if not hasattr(self.complices[0].vertices[0],'evalFun'):
            [v.__setattr__('evalFun',self.obj) for c in self.complices for v in c.vertices]

    def getBest(self):
        return self.parameterHandler.unnormalise(self._getAllCoords()[0])

    def getBestBounds(self):
        return self._getAllCoords()[0]
    
    def getBestDict(self):
        return {k:v for k,v in zip(self.parameterHandler.names, self.getBest())}