#pragma once
#include "_definitions.h"
#include "Mesh.h"
#include "VectorMaths.h"
#include "glm_compat.h"

class LengthCalculator {
public:	
	LengthCalculator(geom::Facet& fac, const vec3& sourceCoord);
	double calcLength(geom::Facet& fac, const vec3& detPixCoord, const vec3& sourceCoord);
private:
	double D_facet;
	double N_facet;
};