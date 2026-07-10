#pragma once
#include "Mesh.h"
#include "VectorMaths.h"

class LengthCalculator {
public:
	LengthCalculator(geom::Facet &fac, vm::vector &sourceCoord);
	double calcLength(vm::vector &normal, vm::vector &detPixCoord, vm::vector &sourceCoord);
private:
	double D_facet;
	double N_facet;
};