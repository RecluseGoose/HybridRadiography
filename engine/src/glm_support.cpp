// glm_vm.cpp

#include "glm_support.h"

namespace glm_support
{

vec3 applyrotation(const vec3& coord, const vec3& centre, const mat3& rotmat){
    return rotmat * (coord - centre) + centre;
}

vec3 toNewCoordSys(const vec3& coord, const vec3& centre, const mat3& rotmat){
    // diff = coord - centre
    // out = rotmat * diff    
    return rotmat * (coord - centre);
}


}