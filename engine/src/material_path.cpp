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
    geom::Mesh mesh;
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
    static char *kwlist[] = {"filename", "xres", "yres","flipnorms", NULL};
	char * filename;
	bool flipnorms = false;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|siib", kwlist,
                                     &filename,
									 &self->xres,
                                     &self->yres,
									 &flipnorms))
        return -1;
	self->mesh.readin(filename);   
	self->mesh.flipNorms = flipnorms;
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
	if (!PyArg_ParseTuple(args, "dOO", &fov, &anglesObj, &offsetsObj))
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
		d.calcLengthBuffer(self->mesh);
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
    type.tp_name = "material_path.MatPath";
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
    mod.m_name = "material_path";
    mod.m_doc = "Example module that creates an extension type.";
    mod.m_size = -1;
	return mod;
}();

// 4) PyInit_custom(PyMODINIT_FUNC) definition
PyMODINIT_FUNC PyInit_material_path(void) {
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
