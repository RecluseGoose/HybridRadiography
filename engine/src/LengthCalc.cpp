#include "LengthCalc.h"

LengthCalculator::LengthCalculator(geom::Facet &fac, const vec3 &sourceCoord){
	double d_facet = -vm::dot(fac.n, fac.v0);
	vec3 f_n = to_glm(fac.n);

	D_facet = glm::dot(f_n, sourceCoord);
	N_facet = D_facet + d_facet;
}

double LengthCalculator::calcLength(geom::Facet &fac, const vec3& detPixCoord, const vec3& sourceCoord){
	vec3 f_n = to_glm(fac.n);
	double dot_pixel = glm::dot(f_n, detPixCoord);
	double denom = D_facet - dot_pixel;
	double beta = N_facet / denom;
	vec3 SP = detPixCoord - sourceCoord;
	return glm::length(SP)*beta;
}

