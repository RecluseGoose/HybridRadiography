#include "glm_compat.h"
#include "Detector.h"
#include <iostream>
#include <cmath>
#include "Rasterisation.h"
#include "LengthCalc.h"
#include "Euler.h"
#include "glm_support.h"

double DEG2RAD = 0.0174532925;

DetBase::~DetBase() {}

DetBase::DetBase(uint xres, uint yres, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ)
: lBuffer(xres, yres)
{
	stlUnitToPix_ = xres / (2.0*det_dist_*std::tan(0.5*hfov*DEG2RAD));
	det_xres_ = xres;
	det_yres_ = yres;
	detPixOffsX = 0.5*(xres - 1.0);
	detPixOffsY = 0.5*(yres - 1.0);
	initialised = true;
	
	vm::matrix rotmat_w2d_vm;	// rotation matrix b/w world and det
	vm::matrix rotmat_d2w_vm;	// rotation matrix b/w det and world
	euler_matrix(eulerX, eulerY, eulerZ, sxyz, rotmat_w2d_vm);
	euler_matrix(-eulerZ, -eulerY, -eulerX, szyx, rotmat_d2w_vm);
	rotmat_w2d = to_glm(rotmat_w2d_vm);
	rotmat_d2w = to_glm(rotmat_d2w_vm);

	lBuffer.init(lDefault);
	part_offset[0] = offsetX;
	part_offset[1] = offsetY;
	part_offset[2] = offsetZ;
}

DetBase::DetBase(uint xres, uint yres, double stlUnitToPix, double detDist, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ)
: lBuffer(xres, yres)
{
	det_xres_ = xres;
	det_yres_ = yres;
	stlUnitToPix_ = stlUnitToPix;
	det_dist_ = detDist;
	detPixOffsX = 0.5*(xres - 1.0);
	detPixOffsY = 0.5*(yres - 1.0);
	initialised = true;

	vm::matrix rotmat_w2d_vm;	// rotation matrix b/w world and det
	vm::matrix rotmat_d2w_vm;	// rotation matrix b/w det and world
	euler_matrix(eulerX, eulerY, eulerZ, sxyz, rotmat_w2d_vm);
	euler_matrix(-eulerZ, -eulerY, -eulerX, szyx, rotmat_d2w_vm);
	rotmat_w2d = to_glm(rotmat_w2d_vm);
	rotmat_d2w = to_glm(rotmat_d2w_vm);

	lBuffer.init(lDefault);
	part_offset[0] = offsetX;
	part_offset[1] = offsetY;
	part_offset[2] = offsetZ;
}

int DetBase::getFacetSign(vec3 source, geom::Facet &fac, bool flipNorms) {
	return (flipNorms ^ (getRayFacDotProd(source, fac) > 0)) ? -1 : +1;
}
double DetBase::getRayFacDotProd(vec3 source, geom::Facet &fac) {
	vec3 f_v0 = to_glm(fac.v0);
	vec3 f_n = to_glm(fac.n);
	vec3 worldFacToSource = f_v0 - source;
	worldFacToSource = glm::normalize(worldFacToSource);
	return glm::dot(f_n, worldFacToSource);
}	

void DetBase::fixColours(double lmin, double lmax, Buffer<double> &buffer) {
	double inv_lrange = 1.0 / (lmax - lmin);

	for (unsigned int i = 0; i < buffer.size(); ++i) {
		buffer[i] = (buffer[i] - lmin)*inv_lrange;
	}
	// Clamp to range
	for (unsigned int i = 0; i < buffer.size(); ++i) {
		if (buffer[i] < 0.0) buffer[i] = 0.0;
		if (buffer[i] > 1.0) buffer[i] = 1.0;
	}
}

void DetBase::projectToDet(unsigned long N, const vec3* coordsIn_w, const vec3& S_w, std::vector<vec2>& detCoords_dp) {	
	vec3 S_d = glm_support::toNewCoordSys(S_w, det_origin, rotmat_w2d); // source coord in detector frame
	vec3 ray_vec_d = glm::normalize(S_d);

	double zs = glm::dot(ray_vec_d, S_d);
	for (geom::ulong i = 0; i < N; i++) {
		vec3 coord_d = glm_support::toNewCoordSys(coordsIn_w[i], det_origin, rotmat_w2d);
		double zf = glm::dot(coord_d, ray_vec_d);
		// sign of alpha assers whether coordinates behind source
		//double alpha = std::abs( zs / (zs - zf) );
		double alpha = zs / (zs - zf);
		if (alpha > 0.0){
			detCoords_dp[i][0] = stlUnitToPix_ * (coord_d[0] - S_d[0])*alpha + detPixOffsX;	// detector coordinates in pixels
			detCoords_dp[i][1] = stlUnitToPix_ * (coord_d[1] - S_d[1])*alpha + detPixOffsY;  // detector coordinates in pixels
		}
		else{
			for (geom::ulong j = 0; j < N; j++) {
				detCoords_dp[j][0] = -1; // is offscreen
				detCoords_dp[j][1] = -1; // is offscreen
			}
			return;
		}
	}
}

void DetBase::projectAllToDet(unsigned long N, const vec3* coordsIn_w, const vec3& meshCentre, std::vector<vec2>& detCoords_dp)
{
	vec3 S = vec3(0.0);
    // Set detector origin
    det_origin = vec3(0.0, 0.0, viewAlongNegativeZ ? -det_dist_ : det_dist_);

    S = meshCentre - part_offset;   
    S = glm_support::applyrotation(S, meshCentre, rotmat_d2w);
	vec3 det_orig = meshCentre - part_offset;
	det_origin = glm_support::applyrotation(det_orig, meshCentre, rotmat_d2w);
    
    // Call the lower level function
    projectToDet(N, coordsIn_w, S, detCoords_dp);   // still passing old type for now
}

void DetBase::projectToDet(geom::Facet& facet, const vec3& S_w, std::vector<vec2>& detCoords_dp) {
	vec3 coordsIn_w[3];
	// 3 coords (facet)
	for (int j = 0; j < 3; ++j) {
		coordsIn_w[0][j] = facet.v0[j];
		coordsIn_w[1][j] = facet.v1[j];
		coordsIn_w[2][j] = facet.v2[j];
	}
	projectToDet(3, coordsIn_w, S_w, detCoords_dp);
}

unsigned int DetBase::coordinateHitImage(unsigned long N, const vec3* coordsIn_w, const vec3& meshCentre) {
	int xmin = 1;	//0; // TODO: we're using minimum of 1 rather than 0, to match edge glitch in rasterer...
	int ymin = 1;	//0;
	int xmax = det_xres_ - 1;
	int ymax = det_yres_ - 1;
	
	// project all coords 
	std::vector<vec2> coordsOut_d(N);
	projectAllToDet(N, coordsIn_w, meshCentre, coordsOut_d);
	// loop through and append do lBuffer
	unsigned int outOfViewCtr = 0;
	for (unsigned long i = 0; i < N; ++i) {
		// round to closest integer
		int x = (int)(coordsOut_d[i][0] + 0.5);
		int y = (int)(coordsOut_d[i][1] + 0.5);
		// append 
		if ((x <= xmax) && (x >= xmin) && (y <= ymax) && (y >= ymin)) {
			++lBuffer[x + det_xres_*y];
		}
		else {
			++outOfViewCtr;
		}
	}

	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
	return outOfViewCtr;
}


vec3 DetBase::detToWorld(vec3 vec) {
	vec3 zeros = { 0,0,0 };
	vec3 intermediate = glm_support::toNewCoordSys(vec, zeros, rotmat_d2w);

	return intermediate + det_origin;
}

void DetBase::flipBufferLR() {
	// Make flipped
	Buffer<double> lBuffer_flipped(det_xres_, det_yres_);
	lBuffer_flipped.init();
	for (uint x = 0; x < det_xres_; ++x) {
		for (uint y = 0; y < det_yres_; ++y) {
			int y_ = y*det_xres_;
			lBuffer_flipped[x + y_] = lBuffer[(det_xres_ - x - 1) + y_];
		}
	}
	// Copy into lBuffer
	for (uint i = 0; i < lBuffer_flipped.size(); ++i) { lBuffer[i] = lBuffer_flipped[i]; }
}

void DetBase::flipBufferUD() {
	// Make flipped
	Buffer<double> lBuffer_flipped(det_xres_, det_yres_);
	lBuffer_flipped.init();
	for (uint x = 0; x < det_xres_; ++x) {
		for (uint y = 0; y < det_yres_; ++y) {
			lBuffer_flipped[x + det_xres_*y] = lBuffer[x + det_xres_*(det_yres_ - y - 1)];
		}
	}
	// Copy into lBuffer
	for (uint i = 0; i < lBuffer_flipped.size(); ++i) { lBuffer[i] = lBuffer_flipped[i]; }
}

void MaterialPath::calcLengthBuffer(const geom::Mesh &mesh) {
	vec3 S = { 0.0, 0.0, 0.0 };
	det_origin = vec3(0.0, 0.0, viewAlongNegativeZ ? -det_dist_ : det_dist_);
	
	vec3 meshCentre_glm = to_glm(mesh.centre);

	S = S + meshCentre_glm;
	S = S - part_offset;
	S = glm_support::applyrotation(S, meshCentre_glm, rotmat_d2w);
	det_origin = det_origin + meshCentre_glm - part_offset;
	det_origin = glm_support::applyrotation(det_origin, meshCentre_glm, rotmat_d2w);


	std::vector<vec2> detCoords_d(3);
	double invScaling = 1.0 / stlUnitToPix_;

	// run for every facet
	for (geom::ulong i_fac = 0; i_fac < mesh.facetCount; ++i_fac) {
		geom::Facet fac = mesh.facetList[i_fac];
		// get facet sign by dot product of facet normal with with ray vector
		
		int facetSign = getFacetSign(S, fac, mesh.flipNorms);
		projectToDet(fac, S, detCoords_d);
		
		vm::coord2d detCoords_d_vm[3];
		to_vm(detCoords_d, detCoords_d_vm, 3);

		// BBraster and length calculator... required within loop
		BoundingBoxRasterer raster(detCoords_d_vm, det_xres_, det_yres_);
		LengthCalculator lengthCalc(fac, S);
		// iterate through raster
		while (raster.iterate()) {
			if (raster.evaluate()) {
				// convert coord of pixel in det frame to pix coord in world frame
				vec3 detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
				vec3 worldCoord = detToWorld(detVec);
				// append length buffer
				double l = lengthCalc.calcLength(fac, worldCoord, S);
				lBuffer[raster.x + raster.y*det_xres_] -= l*facetSign;
			}
		}
	}
	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
}

// void MaterialPath::calcLengthBuffer(geom::SuperMesh &superMesh) {
// 	// Set default ROI to full window
// 	vm::coord2d roi_bl = { 0.0, 0.0 };
// 	vm::coord2d roi_tr = { (double)det_xres_ - 1.0, (double)det_yres_ - 1.0 };
// 	calcLengthBuffer(superMesh, roi_bl, roi_tr);
// }

// void MaterialPath::calcLengthBuffer(geom::SuperMesh &superMesh, vm::coord2d roi_bl, vm::coord2d roi_tr){
// 	// Slight modification of calcLengthBuffer (geom::Mesh) to use different density and flipNorm parameters for each mesh
// 	vm::vector S = { 0.0, 0.0, 0.0 };
// 	det_origin[0] = 0.0;
// 	det_origin[1] = 0.0;
// 	det_origin[2] = viewAlongNegativeZ ? -det_dist_ : det_dist_;
// 	vm::add(S, superMesh.centre, S);
// 	vm::subtract(S, part_offset, S);
// 	vm::applyrotation(S, superMesh.centre, rotmat_d2w, S);
// 	vm::add(det_origin, superMesh.centre, det_origin);
// 	vm::subtract(det_origin, part_offset, det_origin);
// 	vm::applyrotation(det_origin, superMesh.centre, rotmat_d2w, det_origin);
// 	vm::vector worldCoord;
// 	vm::coord2d detCoords_d[3];
// 	double invScaling = 1.0 / stlUnitToPix_;
// 	// run for every facet
// 	geom::ulong iFac = 0;
// 	for (int iMesh = 0; iMesh < superMesh.meshCount; ++iMesh) {
// 		int iFacLim = superMesh.meshEndIdx[iMesh];
// 		for (iFac; iFac < iFacLim; ++iFac) {
// 			geom::Facet fac = superMesh.facetList[iFac];
// 			// get facet sign by dot product of facet normal with with ray vector
// 			double densityAndFacetSign = superMesh.meshDensities[iMesh]*getFacetSign(S, fac, superMesh.meshFlipNorms[iMesh]);
// 			projectToDet(fac, S, detCoords_d);
// 			// BBraster and length calculator... required within loop
// 			BoundingBoxRasterer raster(detCoords_d, det_xres_, det_yres_ , roi_bl, roi_tr);
// 			LengthCalculator lengthCalc(fac, S);
// 			// iterate through raster
// 			while (raster.iterate()) {
// 				if (raster.evaluate()) {
// 					// convert coord of pixel in det frame to pix coord in world frame
// 					vm::vector detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
// 					detToWorld(detVec, worldCoord);
// 					// append length buffer
// 					double l = lengthCalc.calcLength(fac.n, worldCoord, S);
// 					lBuffer[raster.x + raster.y*det_xres_] -= l * densityAndFacetSign;
// 				}
// 			}
// 		}
// 	}
// 	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
// }

LineOfSight::LineOfSight(uint xres, uint yres, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ)
: DetBase(xres, yres, stlUnitToPix_, det_dist_, eulerX, eulerY, eulerZ, offsetX, offsetY, offsetZ), cBuffer(xres, yres)
{
	cBuffer.init(notSeenVal);
}

void LineOfSight::calcVisible(geom::Mesh &mesh) {
	visVec = new bool[mesh.facetCount];
	dpVec = new double[mesh.facetCount];		// dot product vec
	for (uint i = 0; i < mesh.facetCount; ++i) {
		visVec[i] = false;
	}
	vec3 S = { 0.0, 0.0, 0.0 };
	vec3 meshCentre = to_glm(mesh.centre);

	det_origin = {0.0, 0.0, viewAlongNegativeZ ? -det_dist_ : det_dist_};

	S = meshCentre - part_offset;
	S = glm_support::applyrotation(S, meshCentre, rotmat_d2w);

	det_origin = det_origin + meshCentre - part_offset;
	det_origin = glm_support::applyrotation(det_origin, meshCentre, rotmat_d2w);

	vm::vector worldCoord;
	std::vector<vec2> detCoords_d(3);
	double invScaling = 1.0 / stlUnitToPix_;
	// set lBuffer to far away
	for (uint i = 0; i < lBuffer.size(); ++i) {
		lBuffer[i] = lDefault;
	}
	// run for every facet
	for (uint i_fac = 0; i_fac < mesh.facetCount; ++i_fac) {
		geom::Facet fac = mesh.facetList[i_fac];
		// get facet sign by dot product of facet normal with with ray vector
	
		double dp = getRayFacDotProd(S, fac);
		dpVec[i_fac] = dp;
		int facetSign = (mesh.flipNorms ^ (dp > 0))? -1 : +1;	// +1 designates opposite-facicng 
		if (facetSign > 0) { // face cull

			projectToDet(fac, S, detCoords_d);
			// BBraster and length calculator... required within loop
			
			vm::coord2d detCoords_d_vm[3];
			to_vm(detCoords_d, detCoords_d_vm, 3);

			BoundingBoxRasterer raster(detCoords_d_vm, det_xres_, det_yres_);
			LengthCalculator lengthCalc(fac, S);
			// iterate through raster
			while (raster.iterate()) {
				if (raster.evaluate()) {
					// convert coord of pixel in det frame to pix coord in world frame
					vec3 detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
					vec3 worldCoord = detToWorld(detVec);

					// append length buffer
					double l = lengthCalc.calcLength(fac, worldCoord, S);
					if (lBuffer[raster.x + raster.y*det_xres_] > l*facetSign) {
						lBuffer[raster.x + raster.y*det_xres_] = l*facetSign;
						cBuffer[raster.x + raster.y*det_xres_] = (int)i_fac;
					}
				}
			}
		}
	}
	for (uint i = 0; i < cBuffer.size(); ++i) {
		int idx = cBuffer[i];
		if (!(idx < 0)){
			visVec[idx] = true;
		}
	}
}

LineOfSight::~LineOfSight(){
	delete[] visVec;
	delete[] dpVec;
}