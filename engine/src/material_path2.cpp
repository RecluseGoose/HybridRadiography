#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "numpy\arrayobject.h"
#include <iostream>

#include <iomanip>
#include "InspecTest.h"

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

/*
Function numbering in comments matches the tutorial on custom types in cpptopythonmodules 
*/

// 1) MatPathObject (struct) definition
typedef struct {
    PyObject_HEAD
    PyObject *filename;
    geom::SuperMesh mesh;
    int xres;
    int yres;
} MatPathObject;

// *12) custom garbage collection
static int MatPath_traverse(MatPathObject *self, visitproc visit, void *arg) {
    Py_VISIT(self->filename);
    return 0;
}

// *12) custom garbage collection
static int MatPath_clear(MatPathObject *self) {
    Py_CLEAR(self->filename);
	self->mesh.clear();
    return 0;
}

// 5) MatPath_dealloc method (void) definition ... destructor
static void MatPath_dealloc(MatPathObject *self) {
    PyObject_GC_UnTrack(self);
    MatPath_clear(self);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

// 6) MatPath_new method(PyObject *) definition ... basically __new__
static PyObject * MatPath_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    MatPathObject *self;
	self = (MatPathObject *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->filename = PyUnicode_FromString("");
        if (self->filename == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->xres = 100; // defaults
		self->yres = 100; // defaults
    }  
    return (PyObject *) self;
}

// 7) MatPath_init method(int) definition ... basically __init__
static int MatPath_init(MatPathObject *self, PyObject *args, PyObject *kwds) {
	/*static char *kwlist[] = {"filename", "xres", "yres","flipnorms", NULL};
	char * filename;
	bool flipnorms = false;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|siib", kwlist,
                                     &filename,
									 &self->xres,
                                     &self->yres,
									 &flipnorms))*/
	static char *kwlist[] = {"filenames", "xres", "yres","angles","offsets","scales","densities","flipnorms", NULL };
	import_array();
	PyObject * fileList;
	PyArrayObject *anglesObj = NULL;
	PyArrayObject *offsetsObj = NULL;
	PyArrayObject *scalesObj = NULL;
	PyArrayObject *densObj = NULL;
	PyArrayObject *flipnorms = NULL;
	PyObject * strObj;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!ii|OOOOO", kwlist,
		&PyList_Type, &fileList,
		&self->xres,
		&self->yres,
		&anglesObj,
		&offsetsObj,
		&scalesObj,
		&densObj,
		&flipnorms	
	))
        return -1;
	
	int nMesh = (int)PyList_Size(fileList);
	
	std::string* filenames = new std::string[nMesh];
	vm::vector* angles = new vm::vector[nMesh];
	vm::vector* offsets = new vm::vector[nMesh];
	vm::vector* scales = new vm::vector[nMesh];
	double* densities = new	double[nMesh];
	bool* normFlips = new bool[nMesh];

	for (int iMesh = 0; iMesh < nMesh; ++iMesh) {
		//strObj = PyList_GetItem(fileList, i);
		//PyObject * temp_bytes = PyUnicode_AsEncodedString(strObj, "UTF-8", "strict");
		//char * my_result = PyBytes_AS_STRING(temp_bytes); // Borrowed pointer
		//filenames[i] = (std::string)my_result;
		for (int j = 0; j < 3; ++j) {
			if (anglesObj)
				angles[iMesh][j] = *(double*)PyArray_GETPTR2(anglesObj, iMesh, j);
			if (offsetsObj)
				offsets[iMesh][j] = *(double*)PyArray_GETPTR2(offsetsObj, iMesh, j);
			if (scalesObj)
				scales[iMesh][j] = *(double*)PyArray_GETPTR2(scalesObj, iMesh, j);
		}

		filenames[iMesh] = (std::string)PyBytes_AS_STRING(PyUnicode_AsEncodedString(PyList_GetItem(fileList, iMesh), "UTF-8", "strict"));
		if (densObj)
			densities[iMesh] = *(double*)PyArray_GETPTR1(densObj, iMesh);
		if (flipnorms)
			normFlips[iMesh] = *(bool*)PyArray_GETPTR1(flipnorms, iMesh);
	}



	self->mesh.setup(nMesh, filenames, angles, offsets, scales, densities, normFlips);
	delete[] filenames;
	delete[] angles;
	delete[] offsets;
	delete[] scales;	
	delete[] densities;
	delete[] normFlips;
	/*Py_DECREF(fileList); // decrefing breaks stuff..
	Py_DECREF(anglesObj);
	Py_DECREF(offsetsObj);
	Py_DECREF(scalesObj);
	Py_DECREF(densObj);
	Py_DECREF(densObj);
	Py_DECREF(strObj);*/
	return 0;
}

// 8) MatPath_members(PyMemberDef *) ... provides access to c members from python
static PyMemberDef MatPath_members[] = {
    {"xres", T_INT, offsetof(MatPathObject, xres), 0, "custom number"},
	{"yres", T_INT, offsetof(MatPathObject, yres), 0, "custom number"},
    {NULL}  /* Sentinel */
};

static PyObject * MatPath_calculate(MatPathObject *self, PyObject *args) {
	/*
	Returns a stack of material path images.
	
	arguments:
		fov	(double)
		angles (2d np.array)	stack of angle specifications
		offsets (2d np.array)	stack of offset specifications
	*/
	import_array();
	double fov;
	PyArrayObject *anglesObj = NULL;
	PyArrayObject *offsetsObj = NULL;
	PyArrayObject *roiArrObj = NULL;
	if (!PyArg_ParseTuple(args, "dOO|O", &fov, &anglesObj, &offsetsObj, &roiArrObj))
		return NULL;
	/* prepare output array */
	int N_shots =(int)PyArray_SHAPE(anglesObj)[0];
	npy_intp dims[] = { N_shots, self->xres, self->yres}; 	// output dims (dim sizes)
	int n_out = N_shots * self->xres * self->yres;
	int nd = 3;					// output dim length (number of dims)
	double* outArr = (double *)PyArray_malloc(n_out*sizeof(double));
	if (!outArr){
		std::cout << "Unable to allocate memory." << std::endl;
		return Py_None; 
	}
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
		MaterialPath d(self->xres, self->yres, fov, ax, ay, az, ox, oy, oz);
		if (false){
			d.calcLengthBuffer(self->mesh);
		}
		else{
			double roi_b = *(double*)PyArray_GETPTR2(roiArrObj, i_shot, 0);
			double roi_l = *(double*)PyArray_GETPTR2(roiArrObj, i_shot, 1);
			double roi_t = *(double*)PyArray_GETPTR2(roiArrObj, i_shot, 2);
			double roi_r = *(double*)PyArray_GETPTR2(roiArrObj, i_shot, 3);
			coord2d roi_bl = { roi_b, roi_l };
			coord2d roi_tr = { roi_t, roi_r };
			d.calcLengthBuffer(self->mesh, roi_bl, roi_tr);
		}
		/* populate output array */
		int idxRes = self->xres * self->yres;
		for (int x = 0; x < self->xres; x++) {
			for (int y = 0; y < self->yres; y++) {
				outArr[i_shot*idxRes + y + x*self->yres] = d.lBuffer.buf[x + y*self->xres];
			}
		}
	}
	PyArrayObject* outArrObj = (PyArrayObject*)PyArray_SimpleNewFromData(nd, dims, NPY_DOUBLE, outArr);
	PyArray_ENABLEFLAGS(outArrObj, NPY_ARRAY_OWNDATA);
	return PyArray_Return(outArrObj);
}


// 10) MatPath_methods(PyMemberDef *) ... provides access to(PyObject *) functions as instance methods
static PyMethodDef MatPath_methods[] = {
	{ "calculate",(PyCFunction) MatPath_calculate, METH_VARARGS, "generates material path image for given setup" },
	{NULL}  /* Sentinel */
};


// 2) MatPathType(PyTypeObject) definition
static PyTypeObject MatPathType = []()-> PyTypeObject{
    PyTypeObject type = {PyVarObject_HEAD_INIT(NULL, 0)};
    type.tp_name = "material_path2.MatPath";
    type.tp_doc = "MatPath objects";
    type.tp_basicsize = sizeof(MatPathObject);
    type.tp_itemsize = 0;
    type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC;
	type.tp_new = MatPath_new;									// specify the default creator
	type.tp_init = (initproc)MatPath_init;						// specify the init method
	type.tp_dealloc = (destructor)MatPath_dealloc;				// specify the dealloc method
	type.tp_traverse = (traverseproc)MatPath_traverse;			// *
	type.tp_clear = (inquiry)MatPath_clear;						// *
	type.tp_members = MatPath_members;							// specify insance variables with PyMemberDef
	type.tp_methods = MatPath_methods;							// specify PyMethodDefs
	return type;
}();

// 3) custommodule(PyModuleDef) definition
static PyModuleDef custommodule = []()-> PyModuleDef{
	PyModuleDef mod = {PyModuleDef_HEAD_INIT};
    mod.m_name = "material_path2";
    mod.m_doc = "Example module that creates an extension type.";
    mod.m_size = -1;
	return mod;
}();

// 4) PyInit_custom(PyMODINIT_FUNC) definition
PyMODINIT_FUNC PyInit_material_path2(void) {
    PyObject *m;
    if (PyType_Ready(&MatPathType) < 0)
        return NULL;

    m = PyModule_Create(&custommodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&MatPathType);
    PyModule_AddObject(m, "MatPath", (PyObject *) &MatPathType);
    return m;
}
