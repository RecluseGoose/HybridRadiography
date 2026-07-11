#pragma once

#include <glm/glm.hpp>
#include "VectorMaths.h"

using vec3 = glm::dvec3;
using mat3 = glm::dmat3;

namespace glm_support
{
    vec3 applyrotation(vec3 coord, vec3 centre, const mat3& rotmat);

    vec3 toNewCoordSys(vec3 coord, vec3 centre, const mat3& rotmat);
}