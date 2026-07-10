#include "ICPIntersectCaster.h"

void IntersectCaster::getClosestTargetPoint(geom::Facet sourceFac, geom::Mesh * target, geom::vertex closestPt) {
	/*	Function projects source facet normal and finds closest target mesh intersection point at
	dist t where -tMax < t < tMax. If No mesh intersect found, uses closest target facet centre.
	*/

	//vm::vector * sourceFacCentre = &sourceFac.centre;	// ray cast start point
	//vm::vector * sourceRayVec = &sourceFac.n;			// ray vector
	//double t_min = t_max;
	//double t_maxsq = t_max * t_max;
	//double t_minsq = t_min * t_min;
	//bool intersectionNotFound = true;
	//int facHit = 0;
	//// search all facets for best intersection
	//for (geom::ulong i_fac = 0; i_fac < target->facetCount; ++i_fac) {
	//	geom::Facet * targetFac = & target->facetList[i_fac];
	//	double t = getIntersectionDist(*sourceFacCentre, *sourceRayVec, *targetFac);
	//	// check plane intersection is in front of source, and in distance less than t_max
	//	double tsq = t * t;
	//	//if ((t < t_max) && (t >= 0)) {
	//	if (tsq < t_maxsq) {
	//		// calculate intersection point using intersection distance
	//		vm::vector intersectPoint;
	//		for (int i = 0; i < 3; ++i) {
	//			intersectPoint[i] = t * (*sourceRayVec)[i] + *sourceFacCentre[i];
	//		}
	//		// check intersection within facet...
	//		if (pointIsInsideFacet(* targetFac, intersectPoint)) {
	//			// if closest facet so far, register hit
	//			//if (t < t_min) {
	//			if (tsq < t_minsq) {
	//				intersectionNotFound = false;
	//				t_min = t;
	//				t_minsq = tsq;
	//				facHit = i_fac;
	//				vm::multiply(intersectPoint, 1.0, closestPt); // copy best
	//			}
	//		}
	//	}
	//}
	//if (intersectionNotFound) {
	//	// chose closest point on target

	//	vm::vector diff;
	//	vm::subtract(*sourceFacCentre, target->facetList[0].centre, diff);
	//	t_min = vm::magnitude(diff);
	//	for (geom::ulong i_fac = 1; i_fac < target->facetCount; ++i_fac) {
	//		vm::subtract(*sourceFacCentre, target->facetList[i_fac].centre, diff);
	//		double t = vm::magnitude(diff);
	//		//std::cout << target->facetList[i_fac].centre[0] << std::endl;
	//		if (t < t_min) {
	//			t_min = t;
	//			vm::multiply(target->facetList[i_fac].centre, 1.0, closestPt); // copy best
	//			facHit = i_fac;
	//		}
	//	}
	//}
	//std::cout << "Intersection not found? " << intersectionNotFound << " at dist " << t_min << std::endl;
	//std::cout << "facet hit: " << facHit;

	vm::vector * sourceFacCentre = &(sourceFac.centre);	// ray cast start point
	vm::vector * sourceRayVec = &sourceFac.n;			// ray vector
	double t_min = t_max;
	double t_maxsq = t_max * t_max;
	double t_minsq = t_min * t_min;
	bool intersectionNotFound = true;
	int facHit = 0;

	// search all facets for best intersection
	for (geom::ulong i_fac = 0; i_fac < target->facetCount; ++i_fac) {
		geom::Facet * targetFac = &target->facetList[i_fac];
		double t = getIntersectionDist(sourceFac.centre, sourceFac.n, *targetFac);
		// check plane intersection is in front of source, and in distance less than t_max
		double tsq = t * t;
		//if ((t < t_max) && (t >= 0)) {
		if (tsq < t_maxsq) {
			// calculate intersection point using intersection distance
			vm::vector intersectPoint;
			for (int i = 0; i < 3; ++i) {
				intersectPoint[i] = t * sourceFac.n[i] + sourceFac.centre[i];
			}
			// check intersection within facet...
			if (pointIsInsideFacet(*targetFac, intersectPoint)) {
				// if closest facet so far, register hit
				//if (t < t_min) {
				if (tsq < t_minsq) {
					intersectionNotFound = false;
					t_min = t;
					t_minsq = tsq;
					facHit = i_fac;
					vm::multiply(intersectPoint, 1.0, closestPt); // copy best
				}
			}
		}
	}
	if (intersectionNotFound) {
		// chose closest point on target
		vm::vector diff;
		vm::subtract(sourceFac.centre, target->facetList[0].centre, diff);
		t_min = vm::magnitude(diff);
		for (geom::ulong i_fac = 1; i_fac < target->facetCount; ++i_fac) {
			vm::subtract(sourceFac.centre, target->facetList[i_fac].centre, diff);
			double t = vm::magnitude(diff);
			//std::cout << target->facetList[i_fac].centre[0] << std::endl;
			if (t < t_min) {
				t_min = t;
				vm::multiply(target->facetList[i_fac].centre, 1.0, closestPt); // copy best
				facHit = i_fac;
			}
		}
	}

//	std::cout << "Intersection not found? " << intersectionNotFound << " at dist " << t_min << std::endl;
//	std::cout << "facet hit: " << facHit;
}


double IntersectCaster::getIntersectionDist(vm::vector rayOrigin, vm::vector rayVector, geom::Facet fac) {
	// 6 float mult, 5 float adds, 1 float div
	return -(fac.planeConstant + vm::dot(fac.n, rayOrigin)) / vm::dot(fac.n, rayVector);
}

bool IntersectCaster::pointIsInsideFacet(geom::Facet fac, vm::vector intersectPoint) {
	/*

	*/
	double alpha, beta;
	double u0, u1, u2, v0, v1, v2;
	// Get index convention.. i0 is predom normal axis, i1,i2 are remaining axes
	int i0 = fac.predomNormAxis;
	int i1, i2;
	switch (i0){
	case 0:
		i1 = 1;
		i2 = 2;
		break;
	case 1:
		i1 = 0;
		i2 = 2;
		break;
	case 2:
		i1 = 0;
		i2 = 1;
		break;
	}
	
	// calc u and v values
	u0 = intersectPoint[i1] - fac.v0[i1];
	v0 = intersectPoint[i2] - fac.v0[i2];
	u1 = fac.v1[i1] - fac.v0[i1];
	v1 = fac.v1[i2] - fac.v0[i2];
	u2 = fac.v2[i1] - fac.v0[i1];
	v2 = fac.v2[i2] - fac.v0[i2];

	// calc alpha and beta
	beta = (u1*v0 - u0*v1) / (u1*v2 - u2*v1);
	alpha = (v0 - beta*v2) / v1;
	return ((alpha >= 0) && (beta >= 0) && ((alpha + beta) <= 1));
}