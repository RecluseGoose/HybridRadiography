#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

namespace py = pybind11;

py::array_t<double> calc(MaterialPath matPath, geom::Mesh mesh){
    matPath.calcLengthBuffer(mesh);
    
    // copy data
    py::array_t<double> result({matPath.det_xres_, matPath.det_yres_});
    auto buf = result.mutable_unchecked<2>();
    for (int x = 0; x < matPath.det_xres_; ++x){
        for (int y = 0; y < matPath.det_yres_; ++y){
            buf(x,y) = matPath.lBuffer(x,y);
        }
    }	
    return result;
}

PYBIND11_MODULE(py_matpath, m, py::mod_gil_not_used()) {
    py::class_<MaterialPath>(m, "MaterialPath")
        .def(py::init<
            uint,           // xres
            uint,           // yres
            double,         // hfov
            double,         // euler x
            double,         // euler y
            double,         // euler z 
            double,         // offset x
            double,         // offset y
            double>()       // offset z
        ),
    py::class_<geom::Mesh>(m, "Mesh")
        //.def(py::init<const std::string, bool>(), py::arg("flipNorms")=false),
        .def(py::init<const std::string>()),
    m.def("func", &calc);
}