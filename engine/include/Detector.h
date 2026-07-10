#pragma once
#include "_definitions.h"
#include "VectorMaths.h"
#include "Buffer.h"
#include "Mesh.h"

typedef unsigned int uint;
typedef double coord2d[2];

class DetBase {
	double DEFAULT_FOV_CALC_DISTANCE = 100.0;

public:
	DetBase(uint RESLN_X, uint RESLN_Y, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ);
	DetBase(uint RESLN_X, uint RESLN_Y, double stlUnitToPix, double detDist, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ);
	~DetBase();
	void projectAllToDet(unsigned long N, vm::vector coordsIn_w[], vm::vector meshCentre, coord2d coordsOut_d[]);
	unsigned int coordinateHitImage(unsigned long N, vm::vector coordsIn_w[], vm::vector meshCentre);
    void fixColours(double lmin, double lmax, Buffer<double> &buffer);
    // Physical parameters
public:
	double stlUnitToPix_ = 100.0;		// units of [pixel]/[stl unit] ... bigger is more zoom
	uint det_xres_ = 1200;						// x-resolution (pixels)
	uint det_yres_ = 1000;					// y-resolution (pixels)
	vm::vector det_origin;		// centre of coord sys
	vm::matrix rotmat_w2d;	// rotation matrix b/w world and det
	vm::matrix rotmat_d2w;	// rotation matrix b/w det and world
	vm::vector part_offset;
	Buffer<double> lBuffer;			// length buffer
	bool doFilpCorrection = true;	// not required if (a) viewAlongNegativeZ = false or (b) not interested in the correction
	bool viewAlongNegativeZ = true;
protected:
	int getFacetSign(vm::vector S, geom::Facet &fac, bool flipNorms);
	double getRayFacDotProd(vm::vector source, geom::Facet &fac);
	void projectToDet(unsigned long N, vm::vector coordsIn_w[], vm::vector S_w, coord2d detCoords_dp[]);
	void projectToDet(geom::Facet & facet, vm::vector S_w, coord2d detCoords_dp[3]);
	void detToWorld(vm::vector vec_in, vm::vector vec_out);
	//void init(uint RESLN_X, uint RESLN_Y, double stlUnitToPix, double detDist, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ);
	void flipBufferLR();
	void flipBufferUD();
protected:
	double det_dist_ = DEFAULT_FOV_CALC_DISTANCE;
	bool initialised = false;
	double detPixOffsX;
	double detPixOffsY;
protected:
	double lDefault = 0.0;
};

class MaterialPath : public DetBase {
public:
	using DetBase::DetBase;
	void calcLengthBuffer(geom::Mesh &mesh);
	void calcLengthBuffer(geom::SuperMesh &superMesh);
	void calcLengthBuffer(geom::SuperMesh &superMesh, coord2d roi_bl, coord2d roi_tr);
};

class LineOfSight : public DetBase {
public:
	LineOfSight(uint RESLN_X, uint RESLN_Y, double hfov, double eulerX, double eulerY, double eulerZ, double offsetX, double offsetY, double offsetZ);
	void calcVisible(geom::Mesh &mesh);
	Buffer<int> cBuffer;			// colour buffer
	bool *visVec;
	double *dpVec;
	~LineOfSight();
protected:
	double lDefault = 0xFFFFFFFF; // something very far away
	int notSeenVal = -1; 	// default cBuffer value... negative for sign check
};