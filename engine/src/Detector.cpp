#include "Detector.h"
#include <iostream>
#include <cmath>
#include "Rasterisation.h"
#include "LengthCalc.h"
#include "Euler.h"
#include "VectorMaths.h"

double DEG2RAD = 0.0174532925;

DetBase::DetBase() {}

DetBase::~DetBase() {}

DetBase::DetBase(uint RESLN_X, uint RESLN_Y, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ) {
	stlUnitToPix = RESLN_X / (2.0*L*std::tan(0.5*hfov*DEG2RAD));
	init(RESLN_X, RESLN_Y, stlUnitToPix, L, eulerX, eulerY, eulerZ, offsetX, offsetY, offsetZ);
}

DetBase::DetBase(uint RESLN_X, uint RESLN_Y, double stlUnitToPix, double detDist, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ) {
	init(RESLN_X, RESLN_Y, stlUnitToPix, detDist, eulerX, eulerY, eulerZ, offsetX, offsetY, offsetZ);
}

void DetBase::init(uint RESLN_X, uint RESLN_Y, double stlUnitToPix, double detDist, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ) {
	this->RESLN_X = RESLN_X;
	this->RESLN_Y = RESLN_Y;
	this->stlUnitToPix = stlUnitToPix;
	L = detDist;
	detPixOffsX = 0.5*(RESLN_X - 1.0);
	detPixOffsY = 0.5*(RESLN_Y - 1.0);
	initialised = true;
	euler_matrix(eulerX, eulerY, eulerZ, sxyz, rotmat_w2d);
	euler_matrix(-eulerZ, -eulerY, -eulerX, szyx, rotmat_d2w);
	lBuffer = Buffer<double>(RESLN_X, RESLN_Y);
	lBuffer.init(lDefault);
	part_offset[0] = offsetX;
	part_offset[1] = offsetY;
	part_offset[2] = offsetZ;
}

int DetBase::getFacetSign(vm::vector source, geom::Facet &fac, bool flipNorms) {
	return (flipNorms ^ (getRayFacDotProd(source, fac) > 0)) ? -1 : +1;
}

double DetBase::getRayFacDotProd(vm::vector source, geom::Facet &fac) {
	vector worldFacToSource;
	vm::subtract(fac.v0, source, worldFacToSource);
	vm::normalise(worldFacToSource,worldFacToSource);
	return vm::dot(fac.n, worldFacToSource);
}

void DetBase::fixColours(double lmin, double lmax, Buffer<double> &buffer) {
	double actualMin = buffer.buf[RESLN_X];
	double actualMax = buffer.buf[RESLN_X];
	unsigned int els = RESLN_X * RESLN_Y;
	double inv_lrange = 1.0 / (lmax - lmin);
	// Get actuals
	for (unsigned int i = RESLN_X; i < els; ++i) {
		if (buffer.buf[i] < actualMin) actualMin = buffer.buf[i];
		if (buffer.buf[i] > actualMax) actualMax = buffer.buf[i];
	}
	// Scale to range
	for (unsigned int i = 0; i < els; ++i) {
		buffer.buf[i] = (buffer.buf[i] - lmin)*inv_lrange;
	}
	// Clamp to range
	for (unsigned int i = 0; i < els; ++i) {
		if (buffer.buf[i] < 0) buffer.buf[i] = 0.0;
		if (buffer.buf[i] > 1) buffer.buf[i] = 1.0;
	}
}

// for list of coords N_coords long
void DetBase::projectToDet(unsigned long N, vm::vector coordsIn_w[], vm::vector S_w, coord2d detCoords_dp[]) {
	vm::vector coord_d;
	vm::vector S_d; // source coord in detector frame
	vm::vector ray_vec_d;
	vm::toNewCoordSys(S_w, det_origin, rotmat_w2d, S_d);
	vm::normalise(S_d, ray_vec_d);	// ray_vec_d is a normalised vector perpendicular to detector, pointing directly at source
	double zs = vm::dot(ray_vec_d, S_d);
	for (geom::ulong i = 0; i < N; i++) {
		vm::toNewCoordSys(coordsIn_w[i], det_origin, rotmat_w2d, coord_d);
		double zf = vm::dot(coord_d, ray_vec_d);
		// sign of alpha assers whether coordinates behind source
		//double alpha = std::abs( zs / (zs - zf) );
		double alpha = zs / (zs - zf);
		if (alpha > 0.0){
			detCoords_dp[i][0] = stlUnitToPix * (coord_d[0] - S_d[0])*alpha + detPixOffsX;	// detector coordinates in pixels
			detCoords_dp[i][1] = stlUnitToPix * (coord_d[1] - S_d[1])*alpha + detPixOffsY;  // detector coordinates in pixels
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

void DetBase::projectToDet(geom::Facet & facet, vm::vector S_w, coord2d detCoords_dp[3]) {
	vm::vector coordsIn_w[3];
	// 3 coords (facet)
	for (int j = 0; j < 3; ++j) {
		coordsIn_w[0][j] = facet.v0[j];
		coordsIn_w[1][j] = facet.v1[j];
		coordsIn_w[2][j] = facet.v2[j];
	}
	projectToDet(3, coordsIn_w, S_w, detCoords_dp);
}

void DetBase::projectAllToDet(unsigned long N, vm::vector coordsIn_w[], vm::vector meshCentre, coord2d coordsOut_d[]) {
	vm::vector S = { 0.0, 0.0, 0.0 };
	det_origin[0] = 0.0;
	det_origin[1] = 0.0;
	det_origin[2] = viewAlongNegativeZ ? -L : L;
	vm::add(S, meshCentre, S);
	vm::subtract(S, part_offset, S);
	vm::applyrotation(S, meshCentre, rotmat_d2w, S);
	vm::add(det_origin, meshCentre, det_origin);
	vm::subtract(det_origin, part_offset, det_origin);
	vm::applyrotation(det_origin, meshCentre, rotmat_d2w, det_origin);
	projectToDet(N, coordsIn_w, S, coordsOut_d);
}

unsigned int DetBase::coordinateHitImage(unsigned long N, vm::vector coordsIn_w[], vm::vector meshCentre) {
	int xmin = 1;	//0; // TODO: we're using minimum of 1 rather than 0, to match edge glitch in rasterer...
	int ymin = 1;	//0;
	int xmax = RESLN_X - 1;
	int ymax = RESLN_Y - 1;
	// project all coords 
	coord2d *coordsOut_d;
	coordsOut_d = new coord2d[N];
	projectAllToDet(N, coordsIn_w, meshCentre, coordsOut_d);
	// loop through and append do lBuffer
	unsigned int outOfViewCtr = 0;
	for (unsigned long i = 0; i < N; ++i) {
		// round to closest integer
		int x = (int)(coordsOut_d[i][0] + 0.5);
		int y = (int)(coordsOut_d[i][1] + 0.5);
		// append 
		if ((x <= xmax) && (x >= xmin) && (y <= ymax) && (y >= ymin)) {
			++lBuffer.buf[x + RESLN_X*y];
		}
		else {
			++outOfViewCtr;
		}
	}
	delete[] coordsOut_d;
	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
	return outOfViewCtr;
}

void DetBase::detToWorld(vm::vector vec_in, vm::vector vec_out) {
	vm::vector zeros = { 0,0,0 };
	vm::vector intermediate;
	vm::toNewCoordSys(vec_in, zeros, rotmat_d2w, intermediate);
	vm::add(intermediate, det_origin, vec_out);
}

void DetBase::flipBufferLR() {
	// Make flipped
	Buffer<double> lBuffer_flipped(RESLN_X, RESLN_Y);
	lBuffer_flipped.init();
	for (uint x = 0; x < RESLN_X; ++x) {
		for (uint y = 0; y < RESLN_Y; ++y) {
			int y_ = y*RESLN_X;
			lBuffer_flipped.buf[x + y_] = lBuffer.buf[(RESLN_X - x - 1) + y_];
		}
	}
	// Copy into lBuffer
	for (uint i = 0; i < lBuffer_flipped.wh; ++i) { lBuffer.buf[i] = lBuffer_flipped.buf[i]; }
}

void DetBase::flipBufferUD() {
	// Make flipped
	Buffer<double> lBuffer_flipped(RESLN_X, RESLN_Y);
	lBuffer_flipped.init();
	for (uint x = 0; x < RESLN_X; ++x) {
		for (uint y = 0; y < RESLN_Y; ++y) {
			lBuffer_flipped.buf[x + RESLN_X*y] = lBuffer.buf[x + RESLN_X*(RESLN_Y - y - 1)];
		}
	}
	// Copy into lBuffer
	for (uint i = 0; i < lBuffer_flipped.wh; ++i) { lBuffer.buf[i] = lBuffer_flipped.buf[i]; }
}

void MaterialPath::calcLengthBuffer(geom::Mesh &mesh) {
	vm::vector S = { 0.0, 0.0, 0.0 };
	det_origin[0] = 0.0;
	det_origin[1] = 0.0;
	det_origin[2] = viewAlongNegativeZ ? -L : L;
	vm::add(S, mesh.centre, S);
	vm::subtract(S, part_offset, S);
	vm::applyrotation(S, mesh.centre, rotmat_d2w, S);
	vm::add(det_origin, mesh.centre, det_origin);
	vm::subtract(det_origin, part_offset, det_origin);
	vm::applyrotation(det_origin, mesh.centre, rotmat_d2w, det_origin);
	vm::vector worldCoord;
	coord2d detCoords_d[3];
	double invScaling = 1.0 / stlUnitToPix;
	// run for every facet
	for (geom::ulong i_fac = 0; i_fac < mesh.facetCount; ++i_fac) {
		geom::Facet fac = mesh.facetList[i_fac];
		// get facet sign by dot product of facet normal with with ray vector
		int facetSign = getFacetSign(S, fac, mesh.flipNorms);
		projectToDet(fac, S, detCoords_d);
		// BBraster and length calculator... required within loop
		BoundingBoxRasterer raster(detCoords_d, RESLN_X, RESLN_Y);
		LengthCalculator lengthCalc(fac, S);
		// iterate through raster
		while (raster.iterate()) {
			if (raster.evaluate()) {
				// convert coord of pixel in det frame to pix coord in world frame
				vm::vector detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
				detToWorld(detVec, worldCoord);
				// append length buffer
				double l = lengthCalc.calcLength(fac.n, worldCoord, S);
				lBuffer.buf[raster.x + raster.y*RESLN_X] -= l*facetSign;
			}
		}
	}
	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
}

void MaterialPath::calcLengthBuffer(geom::SuperMesh &superMesh) {
	// Set default ROI to full window
	coord2d roi_bl = { 0.0, 0.0 };
	coord2d roi_tr = { (double)RESLN_X - 1.0, (double)RESLN_Y - 1.0 };
	calcLengthBuffer(superMesh, roi_bl, roi_tr);
}

void MaterialPath::calcLengthBuffer(geom::SuperMesh &superMesh, coord2d roi_bl, coord2d roi_tr){
	// Slight modification of calcLengthBuffer (geom::Mesh) to use different density and flipNorm parameters for each mesh
	vm::vector S = { 0.0, 0.0, 0.0 };
	det_origin[0] = 0.0;
	det_origin[1] = 0.0;
	det_origin[2] = viewAlongNegativeZ ? -L : L;
	vm::add(S, superMesh.centre, S);
	vm::subtract(S, part_offset, S);
	vm::applyrotation(S, superMesh.centre, rotmat_d2w, S);
	vm::add(det_origin, superMesh.centre, det_origin);
	vm::subtract(det_origin, part_offset, det_origin);
	vm::applyrotation(det_origin, superMesh.centre, rotmat_d2w, det_origin);
	vm::vector worldCoord;
	coord2d detCoords_d[3];
	double invScaling = 1.0 / stlUnitToPix;
	// run for every facet
	geom::ulong iFac = 0;
	for (int iMesh = 0; iMesh < superMesh.meshCount; ++iMesh) {
		int iFacLim = superMesh.meshEndIdx[iMesh];
		for (iFac; iFac < iFacLim; ++iFac) {
			geom::Facet fac = superMesh.facetList[iFac];
			// get facet sign by dot product of facet normal with with ray vector
			double densityAndFacetSign = superMesh.meshDensities[iMesh]*getFacetSign(S, fac, superMesh.meshFlipNorms[iMesh]);
			projectToDet(fac, S, detCoords_d);
			// BBraster and length calculator... required within loop
			BoundingBoxRasterer raster(detCoords_d, RESLN_X, RESLN_Y , roi_bl, roi_tr);
			LengthCalculator lengthCalc(fac, S);
			// iterate through raster
			while (raster.iterate()) {
				if (raster.evaluate()) {
					// convert coord of pixel in det frame to pix coord in world frame
					vm::vector detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
					detToWorld(detVec, worldCoord);
					// append length buffer
					double l = lengthCalc.calcLength(fac.n, worldCoord, S);
					lBuffer.buf[raster.x + raster.y*RESLN_X] -= l * densityAndFacetSign;
				}
			}
		}
	}
	if (viewAlongNegativeZ && doFilpCorrection) { flipBufferUD(); }
}

MaterialPath::MaterialPath(uint RESLN_X, uint RESLN_Y, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ) {
	stlUnitToPix = RESLN_X / (2.0*L*std::tan(0.5*hfov*DEG2RAD));
	init(RESLN_X, RESLN_Y, stlUnitToPix, L, eulerX, eulerY, eulerZ, offsetX, offsetY, offsetZ);
}

LineOfSight::LineOfSight(uint RESLN_X, uint RESLN_Y, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ){
	stlUnitToPix = RESLN_X / (2.0*L*std::tan(0.5*hfov*DEG2RAD));
	init(RESLN_X, RESLN_Y, stlUnitToPix, L, eulerX, eulerY, eulerZ, offsetX, offsetY, offsetZ);
	cBuffer = Buffer<int>(RESLN_X, RESLN_Y);
	cBuffer.init(notSeenVal);
}

void LineOfSight::calcVisible(geom::Mesh &mesh) {
	visVec = new bool[mesh.facetCount];
	dpVec = new double[mesh.facetCount];		// dot product vec
	for (uint i = 0; i < mesh.facetCount; ++i) {
		visVec[i] = false;
	}
	vm::vector S = { 0.0, 0.0, 0.0 };
	det_origin[0] = 0.0;
	det_origin[1] = 0.0;
	det_origin[2] = viewAlongNegativeZ ? -L : L;
	vm::add(S, mesh.centre, S);
	vm::subtract(S, part_offset, S);
	vm::applyrotation(S, mesh.centre, rotmat_d2w, S);
	vm::add(det_origin, mesh.centre, det_origin);
	vm::subtract(det_origin, part_offset, det_origin);
	vm::applyrotation(det_origin, mesh.centre, rotmat_d2w, det_origin);
	vm::vector worldCoord;
	coord2d detCoords_d[3];
	double invScaling = 1.0 / stlUnitToPix;
	// set lBuffer to far away
	for (uint i = 0; i < lBuffer.wh; ++i) {
		lBuffer.buf[i] = lDefault;
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
			BoundingBoxRasterer raster(detCoords_d, RESLN_X, RESLN_Y);
			LengthCalculator lengthCalc(fac, S);
			// iterate through raster
			while (raster.iterate()) {
				if (raster.evaluate()) {
					// convert coord of pixel in det frame to pix coord in world frame
					vm::vector detVec = { (raster.x - detPixOffsX) * invScaling,(raster.y - detPixOffsY) * invScaling, 0.0 };
					detToWorld(detVec, worldCoord);
					// append length buffer
					double l = lengthCalc.calcLength(fac.n, worldCoord, S);
					if (lBuffer.buf[raster.x + raster.y*RESLN_X] > l*facetSign) {
						lBuffer.buf[raster.x + raster.y*RESLN_X] = l*facetSign;
						cBuffer.buf[raster.x + raster.y*RESLN_X] = (int)i_fac;
					}
				}
			}
		}
	}
	for (uint i = 0; i < cBuffer.wh; ++i) {
		int idx = cBuffer.buf[i];
		if (!(idx < 0)){
			visVec[idx] = true;
		}
	}
}

LineOfSight::~LineOfSight(){
	delete[] visVec;
	delete[] dpVec;
}