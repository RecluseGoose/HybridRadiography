#include "Rasterisation.h"
#include "Mesh.h"
#include "VectorMaths.h"

/*
I want to be able to give the intersect caster a facet from my source mesh,
and I want it to find nearest intersection on the target mesh. Failing that,
just return a value of the closest point.
*/

class IntersectCaster {
public:
	//geom::Mesh * TargetPtr;
	void getClosestTargetPoint(geom::Facet sourceFac, geom::Mesh * targetMesh, geom::vertex closestPt);
	double getIntersectionDist(vm::vector startPoint, vm::vector rayVector, geom::Facet fac);
	bool pointIsInsideFacet(geom::Facet fac, vm::vector intersectPoint);
	double t_max = 20.0;
	IntersectCaster(){};
private:
	double casterLength = 10.0;

};