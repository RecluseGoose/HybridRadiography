// glm_vm.cpp

#include "glm_vm.h"

namespace glm_vm
{

vec3 applyrotation(vec3 coord, vec3 centre, const mat3& rotmat){
    return rotmat * (coord - centre) + centre;
}

vec3 toNewCoordSys(vec3 coord, vec3 centre, const mat3& rotmat){
    // diff = coord - centre
    // out = rotmat * diff    
    return rotmat * (coord - centre);
}


}