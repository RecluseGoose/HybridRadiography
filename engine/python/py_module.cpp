#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

namespace py = pybind11;

using pyvec3 = std::array<double, 3>;

struct SetupContainer{
    uint xres;
    uint yres;
    double hfov;
    pyvec3 euler{0.0};
    pyvec3 offset{0.0};
};

struct SetupContainerMulti{
    uint xres;
    uint yres;
    std::vector<double> hfov;
    std::vector<pyvec3> euler {{0.0}};
    std::vector<pyvec3> offset {{0.0}};
};

py::array_t<double> calculate(const geom::Mesh& mesh, const SetupContainer& setup){
    MaterialPath mp(
        setup.xres, setup.yres, setup.hfov,
        setup.euler[0], setup.euler[1], setup.euler[2],
        setup.offset[0], setup.offset[1],setup.offset[2]
    );
    mp.calcLengthBuffer(mesh);
    
    // copy data to numpy
    py::array_t<double> result({setup.xres, setup.yres});
    auto buf = result.mutable_unchecked<2>(); // 2D accessor
    for (py::ssize_t x = 0; x < setup.xres; ++x){
        for (py::ssize_t y = 0; y < setup.yres; ++y){
            buf(x,y) = mp.lBuffer(x,y);
        }
    }	
    return result;
}

py::array_t<double> calculate_multi(const geom::Mesh& mesh, const SetupContainerMulti& setup){
    py::ssize_t nShots = setup.hfov.size();
    if (setup.euler.size() != nShots || setup.offset.size() != nShots)
        throw std::runtime_error("Multi setup arrays must have same lengths");

    py::array::ShapeContainer shape = {
        static_cast<py::ssize_t>(nShots),
        static_cast<py::ssize_t>(setup.yres),
        static_cast<py::ssize_t>(setup.xres)
    };

    py::array_t<double> result(shape);

    auto info = result.request();
    double* buffer_ptr = static_cast<double*>(info.ptr);
    py::ssize_t shot_stride = setup.xres*setup.yres;

    #pragma omp parallel for
    for (py::ssize_t iShot = 0; iShot< nShots; ++iShot){
        double* shot_ptr = buffer_ptr + iShot * shot_stride;
        MaterialPath mp(
            setup.xres, setup.yres, setup.hfov[iShot],
            setup.euler[iShot][0], setup.euler[iShot][1], setup.euler[iShot][2],
            setup.offset[iShot][0], setup.offset[iShot][1],setup.offset[iShot][2], shot_ptr
        );
        mp.calcLengthBuffer(mesh);
    }
    return result;
}

PYBIND11_MODULE(py_matpath, m) {
    py::class_<geom::Mesh>(m, "Mesh")
        .def(
            py::init<const std::string&, bool>(),
            py::arg("filename"),
            py::arg("flip_norms") = false
    ),
    py::class_<SetupContainer>(m, "SetupContainer")
        .def(
            py::init<
                uint,uint,double,
                pyvec3,
                pyvec3
            >(),
            py::arg("xres"),
            py::arg("yres"),
            py::arg("hfov"),
            py::arg("eulers"),
            py::arg("offsets")
    ),
    py::class_<SetupContainerMulti>(m, "SetupContainerMulti")
        .def(
            py::init<
                uint,uint,std::vector<double>,
                std::vector<pyvec3>,
                std::vector<pyvec3>
            >(),
            py::arg("xres"),
            py::arg("yres"),
            py::arg("hfov stack (N,)"),
            py::arg("eulers stack (N,3)"),
            py::arg("offset stack (N,3)")
    ),
    m.def(
        "calculate",
        &calculate,
        "Calculate material path image",
        py::arg("Mesh"),
        py::arg("SetupContainer")
    ),
    m.def(
        "calculate_multi",
        &calculate_multi,
        "Calculate a stack of material path images",
        py::arg("Mesh"),
        py::arg("SetupContainerMulti")
    );
}