#pragma once
#include "_definitions.h"
#include "VectorMaths.h"   // your old vm stuff
#include "Rasterisation.h"

// ====================== Conversion Helpers ======================

// glm::dvec3 -> vm::vector
inline void to_vm(const vec3& g, vm::vector& out) {
    out[0] = g.x;
    out[1] = g.y;
    out[2] = g.z;
}

inline void to_vm(const vec2& g, vm::coord2d out) {
    out[0] = g.x;
    out[1] = g.y;
}

// GLM Matrices... column index comes first?
inline mat3 to_glm(const vm::matrix& m) {
    return mat3(
         m[0][0], m[1][0], m[2][0],  // column 0
         m[0][1], m[1][1], m[2][1],  // column 1
         m[0][2], m[1][2], m[2][2]   // column 2
    );
}

inline mat3 to_glm(vm::matrix& m) {
    return mat3(
         m[0][0], m[1][0], m[2][0],  // column 0
         m[0][1], m[1][1], m[2][1],  // column 1
         m[0][2], m[1][2], m[2][2]   // column 2
    );
}

inline vec3 to_glm(const double* v)
{
    return vec3(v[0], v[1], v[2]);
}


// inline mat3 to_glm(const vm::matrix& m)
// {
//     return mat3(
//         m[0][0], m[1][0], m[2][0],  // column 0
//         m[0][1], m[1][1], m[2][1],  // column 1
//         m[0][2], m[1][2], m[2][2]   // column 2
//     );
// }

        // m[0][0], m[0][1], m[0][2],
        // m[1][0], m[1][1], m[1][2],
        // m[2][0], m[2][1], m[2][2]