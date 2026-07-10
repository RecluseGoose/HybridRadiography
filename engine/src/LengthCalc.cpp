#include "LengthCalc.h"

LengthCalculator::LengthCalculator(geom::Facet &fac, vm::vector &sourceCoord){
	double d_facet = -vm::dot(fac.n, fac.v0);
	D_facet = vm::dot(fac.n, sourceCoord);
	N_facet = D_facet + d_facet;
}

double LengthCalculator::calcLength(vm::vector &normal, vm::vector &detPixCoord, vm::vector &sourceCoord){
	double dot_pixel = vm::dot(normal, detPixCoord);
	double denom = D_facet - dot_pixel;
	double beta = N_facet / denom;
	vm::vector SP;
	vm::subtract(detPixCoord, sourceCoord, SP);
	return vm::magnitude(SP)*beta;
}
