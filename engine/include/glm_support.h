#pragma once
#include "_definitions.h"
#include <glm/glm.hpp>
#include "VectorMaths.h"

namespace glm_support
{
    vec3 applyrotation(const vec3& coord, const vec3& centre, const mat3& rotmat);
    vec3 toNewCoordSys(const vec3& coord, const vec3& centre, const mat3& rotmat);
}