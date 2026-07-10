#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "numpy\arrayobject.h"
#include <iostream>

#include <iomanip>
#include "InspecTest.h"

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

typedef double vector[3];
typedef unsigned long ulong;
void cArr2vectorArr(PyArrayObject* coords_npArr, vector* coords_vectorArr, ulong n_el);
bool memcheck(double* arr);

static PyObject * mp(PyObject *dummy, PyObject *args) {
	/*
	Returns a stack of material path images.
	
	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	bool normFlip = false;
	double fov;
	PyArrayObject *anglesObj = NULL;
	PyArrayObject *offsetsObj = NULL;
	if (!PyArg_ParseTuple(args, "siidOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	/* prepare output array */
	int N_shots =(int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, xres, yres}; 	// output dims (dim sizes)
	int n_out = N_shots * xres * yres;
	int nd = 3;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for(int i_shot=0; i_shot<N_shots; i_shot++){
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate
		MaterialPath d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.calcLengthBuffer(mesh);
		/* populate output array */
		int idxRes = xres * yres;
		for (int x = 0; x < xres; x++) {
			for (int y = 0; y < yres; y++) {
				outArr[i_shot*idxRes + y + x*yres] = d.lBuffer.buf[x + y*xres];
			}
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	return PyArray_Return(outArrObj);
}

static PyObject * zbuffer(PyObject *dummy, PyObject *args) {
	/*
	Returns a stack of zbuffer images.
	
	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	bool normFlip = false;
	double fov;
	PyArrayObject *anglesObj = NULL;
	PyArrayObject *offsetsObj = NULL;
	if (!PyArg_ParseTuple(args, "siidOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	/* prepare output array */
	int N_shots =(int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, xres, yres}; 	// output dims (dim sizes)
	int n_out = N_shots * xres * yres;
	int nd = 3;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for(int i_shot=0; i_shot<N_shots; i_shot++){
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate
		LineOfSight d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.calcVisible(mesh);
		/* populate output array */
		int idxRes = xres * yres;
		for (int x = 0; x < xres; x++) {
			for (int y = 0; y < yres; y++) {
				outArr[i_shot*idxRes + y + x*yres] = d.lBuffer.buf[x + y*xres];
			}
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	return PyArray_Return(outArrObj);
}

static PyObject * coordHitImage(PyObject *dummy, PyObject *args) {
	/*
	Maps coords onto a pixel-hit count image. Useful for masking mat path images.

	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
		coords (2d np.array)	stack of coords of interest
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	double fov;
	bool normFlip = false;
	PyArrayObject *anglesObj = NULL, *offsetsObj = NULL, *coordsObj;
	if (!PyArg_ParseTuple(args, "siidOOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &coordsObj, &normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	ulong n_el = (int)PyArray_SHAPE(coordsObj)[0];
	vector *coords_w = new vector[n_el];
	cArr2vectorArr(coordsObj, coords_w, n_el);
	/* prepare output array */
	int N_shots =(int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, xres, yres}; 	// output dims (dim sizes)
	int n_out = N_shots * xres * yres;
	int nd = 3;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for(int i_shot=0; i_shot<N_shots; i_shot++){
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate
		MaterialPath d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.coordinateHitImage(n_el, coords_w, mesh.centre);
		/* populate output array */
		int idxRes = xres * yres;
		for (int x = 0; x < xres; x++) {
			for (int y = 0; y < yres; y++) {
				outArr[i_shot*idxRes + y + x*yres] = d.lBuffer.buf[x + y*xres];
			}
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	delete[] coords_w;
	return PyArray_Return(outArrObj);
}

static PyObject * coordsToPixelHit(PyObject *dummy, PyObject *args) {
	/*
	Returns a stack of coordinates in frame of detector (pixel units)

	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
		coords (2d np.array)	stack of coords of interest
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	double fov;
	bool normFlip = false;
	PyArrayObject *anglesObj = NULL, *offsetsObj = NULL, *coordsObj;
	if (!PyArg_ParseTuple(args, "siidOOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &coordsObj,&normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	ulong n_el = (int)PyArray_SHAPE(coordsObj)[0];
	vector *coords_w = new vector[n_el];
	coord2d *coords_d = new coord2d[n_el];
	cArr2vectorArr(coordsObj, coords_w, n_el);
	// Prep output
	int N_shots = (int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, n_el, 2}; 	// output dims (dim sizes)
	int n_out = N_shots * n_el * 2;
	int nd = 3;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for(int i_shot=0; i_shot<N_shots; i_shot++){
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate
		MaterialPath d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.projectAllToDet(n_el, coords_w, mesh.centre,coords_d);
		// Copy into numpy array
		int idxRes = n_el * 2;
		for (ulong i = 0; i < n_el; i++) {
			outArr[i_shot*idxRes + i*2 + 0] = coords_d[i][0];
			outArr[i_shot*idxRes + i*2 + 1] = coords_d[i][1];
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	delete[] coords_w;
	delete[] coords_d;
	return PyArray_Return(outArrObj);
}

static PyObject * mpCoordHitStats(PyObject *dummy, PyObject *args) {
	/*
	Returns four statistical value for mat paths for coords specified.

	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
		coords (2d np.array)	stack of coords of interest
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	double fov;
	bool normFlip = false;
	PyArrayObject *anglesObj = NULL, *offsetsObj = NULL, *coordsObj;
	if (!PyArg_ParseTuple(args, "siidOOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &coordsObj,&normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	ulong n_el = (int)PyArray_SHAPE(coordsObj)[0];
	vector *coords_w = new vector[n_el];
	coord2d *coords_d = new coord2d[n_el];
	cArr2vectorArr(coordsObj, coords_w, n_el);
	// Prep output
	int N_shots = (int)PyArray_SHAPE(anglesObj)[0];
	int n_vals = 4;		// number of statistical parameters
	npy_intp dims[] = { N_shots, n_vals}; 	// output dims (dim sizes)
	int n_out = N_shots * n_vals;
	int nd = 2;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for(int i_shot=0; i_shot<N_shots; i_shot++){
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate pix hit img
		double oov; // out of view
		MaterialPath chi(xres, yres, fov, ax, ay, az, ox, oy, oz);
		chi.doFilpCorrection = false;
		oov = (double)chi.coordinateHitImage(n_el, coords_w, mesh.centre);
		// Calculate mp image
		MaterialPath d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.doFilpCorrection = false;
		d.calcLengthBuffer(mesh);
		// Merge and collect stats
		double min = 1e9;
		double max = 0.0;
		double mean = 0.0;
		double counts = 0.0;
		for (uint i = 0; i < chi.lBuffer.wh; ++i) {
			double count = chi.lBuffer.buf[i];
			if (count == 0) {
				continue;
			}
			double value = d.lBuffer.buf[i];
			if (value == 0.0) {
				continue;
			}
			else {				
				mean += (value * count);
				counts += count;
				if (value < min) {
					min = value;
				}
				if (value > max) {
					max = value;
				}
			}
		}
		mean /= counts;
		// Copy into numpy array
		ulong idx = i_shot*n_vals;
		outArr[idx + 0] = min;
		outArr[idx + 1] = max;
		outArr[idx + 2] = mean;
		outArr[idx + 3] = oov;
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	delete[] coords_w;
	return PyArray_Return(outArrObj);
}

static PyObject * mpCoordHit(PyObject *dummy, PyObject *args) {
	/*
	Returns mat path statistics for coords specified.

	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
		coords (2d np.array)	stack of coords of interest
		nsv						value given if element not seen
	*/
	import_array();
	int xres;
	int yres;
	int xmin = 1;	//0; // TODO: we're using minimum of 1 rather than 0, to match edge glitch in rasterer...
	int ymin = 1;	//0;
	double nsv; // not seen value
	char * filename;
	double fov;
	bool normFlip = false;
	PyArrayObject *anglesObj = NULL, *offsetsObj = NULL, *coordsObj;
	if (!PyArg_ParseTuple(args, "siidOOOd|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &coordsObj,&nsv,&normFlip))
		return NULL;
	int xmax = (xres - 1);
	int ymax = (yres - 1);
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	ulong n_el = (int)PyArray_SHAPE(coordsObj)[0];
	coord2d *coords_d = new coord2d[n_el];
	vector *coords_w = new vector[n_el];
	cArr2vectorArr(coordsObj, coords_w, n_el);
	// Prep output
	int N_shots = (int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, n_el}; 	// output dims (dim sizes)
	int n_out = N_shots * n_el;
	int nd = 2;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (memcheck(outArr)){ return Py_None; }
	// Loop through
	for (int i_shot = 0; i_shot<N_shots; i_shot++) {
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate mp image
		MaterialPath d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.doFilpCorrection = false;
		d.calcLengthBuffer(mesh);
		// Calculate pix hits
		d.projectAllToDet(n_el, coords_w, mesh.centre, coords_d);
		// Copy into array
		for (ulong i_el = 0; i_el < n_el; i_el++) {
			// check if pixel on detector... if so, append mpVal, else nsv
			int x = (int)(coords_d[i_el][0] + 0.5);
			int y = (int)(coords_d[i_el][1] + 0.5);
			if ((x <= xmax) && (x >= xmin) && (y <= ymax) && (y >= ymin)) {
				outArr[i_shot*n_el + i_el] = d.lBuffer.buf[x + xres*y];
			}
			else {
				outArr[i_shot*n_el + i_el]  = nsv; // not seen value
			}		
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	delete[] coords_w;
	delete[] coords_d;
	return PyArray_Return(outArrObj);
}

static PyObject * los(PyObject *dummy, PyObject *args) {
	/*
	Returns a stack of visibility vectors.

	arguments:
		filename				filepath to stl
		xres (int)
		yres (int)
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
	*/
	import_array();
	int xres;
	int yres;
	char * filename;
	double fov;
	bool normFlip = false;
	PyArrayObject *anglesObj = NULL, *offsetsObj = NULL;
	if (!PyArg_ParseTuple(args, "siidOO|b", &filename, &xres, &yres, &fov, &anglesObj, &offsetsObj, &normFlip))
		return NULL;
	// Load the data
	geom::Mesh mesh(filename);
	if (normFlip)
		mesh.flipNorms = true;
	// Prep output
	ulong facCount = mesh.facetCount;
	int N_shots = (int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, facCount}; 	// output dims (dim sizes)
	int n_out = N_shots * facCount;
	int nd = 2;					// output dim length (number of dims)
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNew(nd, dims, NPY_BOOL);
	PyArrayObject* dotArrObj = (PyArrayObject*)PyArray_SimpleNew(nd, dims, NPY_DOUBLE);
	// Loop through
	for (int i_shot = 0; i_shot<N_shots; i_shot++) {
		// Get arguments
		double ax = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 0);
		double ay = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 1);
		double az = *(double*)PyArray_GETPTR2(anglesObj, i_shot, 2);
		double ox = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 0);
		double oy = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 1);
		double oz = *(double*)PyArray_GETPTR2(offsetsObj, i_shot, 2);
		// Calculate
		LineOfSight d(xres, yres, fov, ax, ay, az, ox, oy, oz);
		d.calcVisible(mesh);
		// Copy into numpy array
		for (ulong x = 0; x < facCount; x++) {
			bool* visEl = (bool*)PyArray_GETPTR2(outArrObj, i_shot, x);
			double* dotEl = (double*)PyArray_GETPTR2(dotArrObj, i_shot, x);
			*visEl = (bool)d.visVec[x];
			*dotEl = (double)d.dpVec[x];

		}
	}
	return Py_BuildValue( "OO", outArrObj, dotArrObj );
}

void cArr2vectorArr(PyArrayObject* coords_npArr, vector* coords_vectorArr, ulong n_el){
	for (unsigned long i_el = 0; i_el < n_el; ++i_el) {
		coords_vectorArr[i_el][0] = *(double*)PyArray_GETPTR2(coords_npArr, i_el, 0);
		coords_vectorArr[i_el][1] = *(double*)PyArray_GETPTR2(coords_npArr, i_el, 1);
		coords_vectorArr[i_el][2] = *(double*)PyArray_GETPTR2(coords_npArr, i_el, 2);
	}
}

bool memcheck(double* arr){
	bool ret = !arr;
	if (ret){std::cout << "Unable to allocate memory." << std::endl;}
	return ret;
}

// Our Module's Function Definition struct
static PyMethodDef myMethods[] = {
    { "mp", mp, METH_VARARGS, "generates material path image for given setup" },
	{ "los", los, METH_VARARGS, "line of sight" },
	{ "zbuffer", zbuffer, METH_VARARGS, "gives zbuffer image" },
	{ "coordHitImage", coordHitImage, METH_VARARGS, "converts coordinates of interest into a pixel hit count image" },
	{ "coordsToPixelHit", coordsToPixelHit, METH_VARARGS, "maps world coordinates to det pixel coords" },
	{ "mpHitStats", mpCoordHitStats, METH_VARARGS, "provides mp statistics for coordinates of interest" },
	{ "mpCoordHit", mpCoordHit, METH_VARARGS, "mpCoordHit" },
    { NULL, NULL, 0, NULL }
};

// Our Module Definition struct
static struct PyModuleDef myModule = {
    PyModuleDef_HEAD_INIT,
    "rays",
    "rays module",
    -1,
    myMethods
};

// Initializes our module using our above struct
PyMODINIT_FUNC PyInit_rays(void)
{
    return PyModule_Create(&myModule);
}
