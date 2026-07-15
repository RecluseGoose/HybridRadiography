#pragma once
#include "VectorMaths.h"
#include <string>

namespace geom {
typedef vm::vector vertex;
typedef unsigned long ulong;
		
static const double _oneThird = 1.0 / 3.0;

struct Facet {
	vertex v0;
	vertex v1;
	vertex v2;
	vm::vector n;
	Facet();
	Facet(vertex & v0, vertex & v1, vertex & v2, vm::vector & n);
	double planeConstant; // value of dot product with vector to point on plane
	int predomNormAxis;	  // predomenant normal axis for icp calculations
	vertex centre;
	double getFacetArea();
	void calcCentre();
	void calcPlaneConstant();
	void calcPredomNormAxis();
};

class Mesh {
public:
	Mesh();
	//Mesh(const char * stlfile);
	Mesh(const std::string stlfile);
	Mesh(const std::string stlfile, bool flipNorms);
	void readin(const char * stlfile);
	void readin(const std::string stlfile);
	~Mesh();
	void clear();			// Forces clearing, ensures against mem leaks
	void update();
	void facetPreCalcs();	// perform facet pre calcs for ICP ray casting
public:
	ulong vertCount = 0;
	vertex* vertexList = nullptr;
	ulong facetCount = 0;
	Facet* facetList = nullptr;
	double boundingBox[6] = { 0.0 }; // xmin xmax ymin ymax zmin zmax // aligned with axes, thus 6 coords
	vm::vector centre = {0.0};
	double length = 0.0;
	void printFacetTable();
	bool flipNorms = false;
protected:
	void updateBoundingBox();
	void updateLength();
	// ICP facet precalc functions
	void calcFacetCentres();
	void calcFacetPlaneConstants();
	void calcFacetPredomNormAxes();
private:
	void updateCentre();
	void updateVertexList();
};

class SuperMesh : public Mesh {
public:
	SuperMesh(int meshCount, std::string* filenames, vm::vector* angles, vm::vector* offsets, vm::vector* scales, double* densities, bool* normFlips);
	void setup(int meshCount, std::string* filenames, vm::vector* angles, vm::vector* offsets, vm::vector* scales, double* densities, bool* normFlips);
	~SuperMesh();
	void clear();
//private:
public:
	int meshCount = 0;
	Mesh* meshList = nullptr;
	vm::vector* meshOffs = nullptr;
	vm::vector* meshAngs = nullptr;
	vm::vector* meshScales = nullptr;
	int* meshEndIdx = nullptr;
	double* meshDensities = nullptr;
	bool* meshFlipNorms = nullptr;
	/*const vm::vector centre = { {0.0}};*/
private:
	void updateVertexList();
};

class OBB {
public:
	Facet* childFacetList0 = nullptr;
	Facet* childFacetList1 = nullptr;
	int facCount0 = 0;
	int facCount1 = 0;
	vertex boundingBox[8] = { {0.0} };
	OBB* children = nullptr;
	OBB() {};
	OBB(Facet* facetList, ulong facetCount);
	~OBB();
	void makeChildren();
	void killChildren();
	bool hasChildren = false;
};

class OBBTree {
public:
	OBBTree(geom::Mesh mesh, int depth);
	void createBranches(Facet* facetList);
	void build();
};
}
