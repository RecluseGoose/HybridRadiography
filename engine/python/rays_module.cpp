#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>

#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

namespace py = pybind11;

using pyvec2 = std::array<double, 2>;
using pyvec3 = std::array<double, 3>;

struct SetupContainer{
    uint xres;
    uint yres;
    double hfov;
    pyvec3 euler{0.0};
    pyvec3 offset{0.0};
};

py::array_t<double> coordsToPixelHit(
    geom::Mesh& mesh,
    const SetupContainer& setup,
    const std::vector<pyvec3>& coordsIn_w
){
    MaterialPath mp(
        setup.xres, setup.yres, setup.hfov,
        setup.euler[0], setup.euler[1], setup.euler[2],
        setup.offset[0], setup.offset[1],setup.offset[2]
    );

    py::ssize_t N = coordsIn_w.size();
    py::array::ShapeContainer shape = {
        static_cast<py::ssize_t>(N),
        static_cast<py::ssize_t>(2)
    };
    py::array_t<double> result(shape);
    auto buf = result.mutable_unchecked<2>(); // 2D accessor

    // UGLY UGLY UGLY make a coords_glm
    std::vector<vec3> coords_glm;
    vec3 centre_glm = {mesh.centre[0],mesh.centre[1],mesh.centre[2]};
    coords_glm.reserve(coordsIn_w.size());
    for (const auto& c : coordsIn_w){ coords_glm.emplace_back(c[0],c[1],c[2]);}
    // UGLY UGLY UGLY

    std::vector<vec2> detCoords_dp(N);
    mp.projectAllToDet(N, coords_glm.data(), centre_glm, detCoords_dp);
    
    std::cout<< coords_glm[0][0] << " " << coords_glm[0][1] << std::endl;
    // copy results for now
    for (py::ssize_t iCoord = 0; iCoord< N; ++iCoord){
        buf(iCoord,0) = detCoords_dp[iCoord][0];
        buf(iCoord,1) = detCoords_dp[iCoord][1];
    }

    return result;
}


PYBIND11_MODULE(py_rays, m) {
    m.def(
        "coordsToPixelHit",
        &coordsToPixelHit,
        "Convert xyz world coords to pixel hit coords",
        py::arg("Mesh"),
        py::arg("SetupContainer"),
        py::arg("Coords In")
    );
}