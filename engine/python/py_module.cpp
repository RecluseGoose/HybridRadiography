#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

namespace py = pybind11;

py::array_t<double> calculate_material_path(MaterialPath& matPath, const geom::Mesh& mesh){
    matPath.calcLengthBuffer(mesh);
    
    // copy data
    py::array_t<double> result({matPath.det_xres_, matPath.det_yres_});
    auto buf = result.mutable_unchecked<2>();
    for (size_t x = 0; x < matPath.det_xres_; ++x){
        for (size_t y = 0; y < matPath.det_yres_; ++y){
            buf(x,y) = matPath.lBuffer(x,y);
        }
    }	
    return result;
}

PYBIND11_MODULE(py_matpath, m) {
    py::class_<MaterialPath>(m, "MaterialPath")
        .def(
            py::init<
                uint,uint,double,
                double,double,double,
                double,double,double
            >(),
            py::arg("xres"),
            py::arg("yres"),
            py::arg("hfov"),
            py::arg("euler_x"),
            py::arg("euler_y"),
            py::arg("euler_z"),
            py::arg("offset_x"),
            py::arg("offset_y"),
            py::arg("offset_z")
        ),
        // .def_property_readonly(
        //     "xres",
        //     &MaterialPath::det_xres_
        // )
        // .def_property_readonly(
        //     "yres",
        //     &MaterialPath::det_yres_
        // ),
    py::class_<geom::Mesh>(m, "Mesh")
        //.def(py::init<const std::string, bool>(), py::arg("flipNorms")=false),
        .def(
            py::init<const std::string&, bool>(),
            py::arg("filename"),
            py::arg("flip_norms") = false
    ),
    m.def(
        "calculate_material_path",
        &calculate_material_path,
        "Calculate material path image",
        py::arg("material_path"),
        py::arg("mesh")
    );
}

