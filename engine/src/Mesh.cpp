#include <cmath>
#include <iostream>
#include "Mesh.h"
#include "STLReader.h"
#include "Euler.h"

namespace geom {
Facet::Facet(){}
Facet::Facet(vertex & v0, vertex & v1, vertex & v2, vm::vector & n){
	for (int i = 0; i < 3; ++i) {
		this->v0[i] = v0[i];
		this->v1[i] = v1[i];
		this->v2[i] = v2[i];
		this->n[i] = n[i];
	}
}
double Facet::getFacetArea() {
	vm::vector out10;
	vm::vector out20;
	vm::subtract(v1, v0, out10);
	vm::subtract(v2, v0, out20);
	double magprod = vm::magnitude(out10)*vm::magnitude(out20);
	double theta = std::acos(vm::dot(out10, out20) / magprod);
	double area = 0.5*magprod*std::abs(std::sin(theta));
	return area;
}

void Facet::calcCentre() {
	for (int i = 0; i < 3; ++i) {
		centre[i] = geom::_oneThird * ( v0[i] + v1[i] + v2[i] );
	}	
}

void Facet::calcPlaneConstant() {
	// dot(n, p) + d = 0
	planeConstant = -vm::dot(n,v0);
}

void Facet::calcPredomNormAxis() {
	vm::vector absNorm;
	for (int i = 0; i < 3; ++i) {
		absNorm[i] = n[i] * n[i];
	}
	predomNormAxis = vm::getMaxIndex3(absNorm);
}

Mesh::Mesh(){
}
//Mesh::Mesh(const char * stlfile){
//	this->readin(stlfile);
//}
Mesh::Mesh(const std::string& stlfile){
	this->readin(stlfile);
}

Mesh::Mesh(const std::string& stlfile, bool flipNorms)
: flipNorms(flipNorms){
	this->readin(stlfile);
}

//void Mesh::readin(const char * stlfile){
	// STLReader reader;
	// reader.readFile(stlfile, *this);
	// update();
//}
void Mesh::readin(const std::string stlfile){
	STLReader reader;
	reader.readFile(stlfile, *this);
	update();
}
Mesh::~Mesh(){
	Mesh::clear();
}
void Mesh::clear()	{
	delete[] vertexList;
	delete[] facetList;
	facetCount = 0;
	vertCount = 0;
	vertexList = nullptr;
	facetList = nullptr;
}
void Mesh::update()	{
	updateVertexList();
	updateBoundingBox();
	updateCentre();
	updateLength();
}
void Mesh::updateVertexList()	{
	vertCount = 3 * facetCount;
	delete[] vertexList;
	vertexList = new vertex[vertCount];
	for (ulong i = 0; i < facetCount; ++i) {
		int i3 = 3 * i;
		for (int j = 0; j < 3; ++j) {
			vertexList[i3    ][j] = facetList[i].v0[j];
			vertexList[i3 + 1][j] = facetList[i].v1[j];
			vertexList[i3 + 2][j] = facetList[i].v2[j];
		}
	}
}
void Mesh::updateBoundingBox() {
	for (int i = 0; i < 3; ++i) {
		boundingBox[2 * i] = vertexList[0][i];
		boundingBox[2 * i + 1] = vertexList[0][i];
	}
	for (ulong i = 0; i < vertCount; ++i) {
		for (int j=0; j < 3; j++) {
			double val = vertexList[i][j];
			if (val < boundingBox[2 * j])
				boundingBox[2 * j] = vertexList[i][j];
			if (val > boundingBox[2 * j + 1])
				boundingBox[2 * j + 1] = vertexList[i][j];
		}
	}
}
void Mesh :: updateCentre() {
	for (int i = 0; i < 3; ++i) {
		centre[i] = (boundingBox[2 * i] + boundingBox[2 * i + 1])*0.5;
	}
}
void Mesh::updateLength(){
	vm::vector diag;
	for (int i = 0; i < 3; ++i) {
		diag[i] = boundingBox[2 * i + 1] - boundingBox[2 * i];
	}
	length = vm::magnitude(diag);
}
void Mesh::printFacetTable() {
	int imax = (facetCount > 10) ? 10 : facetCount;
	for (int i = 0; i < imax; i++){
		std::cout << i << " Facet (n,v0,v1,v2)"<< std::endl;
		for (int j = 0; j < 3; j++) {
				std::cout << facetList[i].n[j] << " " << std::flush;
				std::cout << facetList[i].v0[j] << " " << std::flush;
				std::cout << facetList[i].v1[j] << " " << std::flush;
				std::cout << facetList[i].v2[j] << std::endl;
			}
	}
}
void Mesh::facetPreCalcs() {
	// Populates all facet objects with centre, planeConstant and predomNormAxis properties
	calcFacetCentres();
	calcFacetPlaneConstants();
	calcFacetPredomNormAxes();
}
void Mesh::calcFacetPlaneConstants() {
	for (ulong i = 0; i < facetCount; ++i) facetList[i].calcPlaneConstant();
}

void Mesh::calcFacetPredomNormAxes() {
	for (ulong i = 0; i < facetCount; ++i) facetList[i].calcPredomNormAxis();
}

void Mesh::calcFacetCentres() {
	for (ulong i = 0; i < facetCount; ++i) facetList[i].calcCentre();
}

SuperMesh::SuperMesh(int meshCount, std::string* filenames, vm::vector* angles, vm::vector* offsets, vm::vector* scales, double* densities, bool* normFlips) {
	this->setup(meshCount, filenames, angles, offsets, scales, densities, normFlips);
}

void SuperMesh::setup(int meshCount, std::string* filenames, vm::vector* angles, vm::vector* offsets, vm::vector* scales, double* densities, bool* normFlips)
	//vm::vector* angles,
	//bool* normFlips,
	//double* densities )
{
	this->meshCount = meshCount;
	/* Setup dynamic lists
	meshList[meshCount],
	meshLabels[meshCount],
	meshAngs[meshCount],
	meshOffs[meshCount],
	meshDensites[meshCount],
	
	facetList[facetCount],
	vertexList[vertexCount],
	*/
	meshList = new Mesh[meshCount];
	meshAngs = new vm::vector[meshCount];
	meshOffs = new vm::vector[meshCount];
	meshScales = new vm::vector[meshCount];
	meshEndIdx = new int[meshCount];
	meshDensities = new double[meshCount];
	meshFlipNorms = new bool[meshCount];
	// Read in each mesh and accumulate facetNum
	int tempFacCount = 0;
	for (int i=0; i < meshCount; ++i) {
		Mesh *mesh = &meshList[i];
		mesh->readin(filenames[i]);
		tempFacCount += mesh->facetCount;
		meshEndIdx[i] = tempFacCount; // ending index for ith mesh
		meshDensities[i] = densities[i];
		meshFlipNorms[i] = normFlips[i];
		//meshAngs[i][0]
		vm::copyVec(offsets[i], meshOffs[i]);
		vm::copyVec(angles[i], meshAngs[i]);
		vm::copyVec(scales [i], meshScales[i]);
	}
	// Populate facetList
	facetCount = tempFacCount;
	facetList = new Facet[facetCount];
	vertCount = 3 * facetCount;
	int idx = 0;
	for (int i = 0; i < meshCount; ++i) {
		Mesh *mesh = &meshList[i];
		for (ulong iFac = 0; iFac < mesh->facetCount; ++iFac) {
			facetList[idx] = mesh->facetList[iFac];
			++idx;
		}
	}	
	updateVertexList();
	updateLength();
	updateBoundingBox();
	// Set centre to zeros... this should always be the case with SuperMesh
	vm::vector rotCentre = { 0.0, 0.0, 0.0 };
	vm::copyVec(rotCentre, centre);
	/*
	std::cout << "angles" << std::endl;
	for (int iMesh = 0; iMesh < meshCount; ++iMesh) {
		std::cout << angles[iMesh][0] << ", " << angles[iMesh][1] << ", " << angles[iMesh][2] << std::endl;
	}

	std::cout << "offsets" << std::endl;
	for (int iMesh = 0; iMesh < meshCount; ++iMesh) {
		std::cout << offsets[iMesh][0] << ", " << offsets[iMesh][1] << ", " << offsets[iMesh][2] << std::endl;
	}

	std::cout << "scales" << std::endl;
	for (int iMesh = 0; iMesh < meshCount; ++iMesh) {
		std::cout << scales[iMesh][0] << ", " << scales[iMesh][1] << ", " << scales[iMesh][2] << std::endl;
	}
	*/
}

SuperMesh::~SuperMesh() {
	clear();
}

void SuperMesh::clear() {
	meshCount = 0;
	delete[] meshList;
	delete[] meshOffs;
	delete[] meshAngs;
	delete[] meshScales;
	delete[] meshEndIdx;
	delete[] meshDensities;
	delete[] meshFlipNorms;
	meshList = nullptr;
	meshOffs = nullptr;
	meshAngs = nullptr;
	meshScales = nullptr;
	meshEndIdx = nullptr;
	meshDensities = nullptr;
	meshFlipNorms = nullptr;
	this->Mesh::clear();
}

void SuperMesh::updateVertexList() {
	// Setup new vertex list
	delete[] vertexList;
	vertexList = new vertex[vertCount];
	vm::vector rotCentre = { {0.0} };
	int iFac = 0;
	for (int iMesh = 0; iMesh < meshCount; iMesh++) {
		vm::matrix rotmat;
		euler_matrix(meshAngs[iMesh][0], meshAngs[iMesh][1], meshAngs[iMesh][2], sxyz, rotmat);
		for (iFac; iFac < meshEndIdx[iMesh]; ++iFac) {
			// offset so that each vertex of each child mesh sits at the child mesh centre... note this reloads from original meshdata.
			vm::subtract(facetList[iFac].v0, meshList[iMesh].centre, facetList[iFac].v0);
			vm::subtract(facetList[iFac].v1, meshList[iMesh].centre, facetList[iFac].v1);
			vm::subtract(facetList[iFac].v2, meshList[iMesh].centre, facetList[iFac].v2);
			// scale each vertex accordingly
			vm::multiply(facetList[iFac].v0, meshScales[iMesh], facetList[iFac].v0);
			vm::multiply(facetList[iFac].v1, meshScales[iMesh], facetList[iFac].v1);
			vm::multiply(facetList[iFac].v2, meshScales[iMesh], facetList[iFac].v2);
			vm::multiply(facetList[iFac].n, meshScales[iMesh], facetList[iFac].n);
			// rotate each vertex accordingly
			vm::applyrotation(facetList[iFac].v0, rotCentre, rotmat, facetList[iFac].v0);
			vm::applyrotation(facetList[iFac].v1, rotCentre, rotmat, facetList[iFac].v1);
			vm::applyrotation(facetList[iFac].v2, rotCentre, rotmat, facetList[iFac].v2);
			vm::applyrotation(facetList[iFac].n, rotCentre, rotmat, facetList[iFac].n);
			// offset each vertex accordingly
			vm::add(facetList[iFac].v0, meshOffs[iMesh], facetList[iFac].v0);
			vm::add(facetList[iFac].v1, meshOffs[iMesh], facetList[iFac].v1);
			vm::add(facetList[iFac].v2, meshOffs[iMesh], facetList[iFac].v2);
			// update vertex list
			int iFac3 = 3 * iFac;
			for (int j = 0; j < 3; ++j) {
				vertexList[iFac3][j] = facetList[iFac].v0[j];
				vertexList[iFac3 + 1][j] = facetList[iFac].v1[j];
				vertexList[iFac3 + 2][j] = facetList[iFac].v2[j];
			}
		}
	}
}

void OBBTree::createBranches(Facet* facetList) {}

OBB::OBB(Facet* facetList, ulong facetCount) {
	// Get facet centre coords
	ulong vertCount = facetCount * 3;
	vertex *coords = new vertex[vertCount];
	vertex *coordsBar = new vertex[vertCount];
	vertex mu = { {0.0} };	// mean facet centroid
	for (ulong i_fac = 0; i_fac < facetCount; ++i_fac) {
		for (int i_coord = 0; i_coord < 3; ++i_coord) {
			double val = facetList[i_fac].v0[i_coord];	//vertex 0
			coords[i_fac*3][i_coord] = val;
			mu[i_coord] += val;
			val = facetList[i_fac].v1[i_coord];			//vertex 1
			coords[i_fac * 3 + 1][i_coord] = val;
			mu[i_coord] += val;
			val = facetList[i_fac].v2[i_coord];			//vertex 2
			coords[i_fac * 3 + 2][i_coord] = val;
			mu[i_coord] += val;
		}
	}
	// Calc covariance matrix
	vm::matrix cov = { { 0.0 } };
	vm::multiply(mu, 1.0 / vertCount, mu);
	for (ulong i = 0; i < vertCount; ++i) {
		for (int i_coord = 0; i_coord < 3; ++i_coord) {
			coordsBar[i][i_coord] = coords[i][i_coord] - mu[i_coord];
		}
	}
	for (int i = 0; i < 3; ++i) {
		for (int j = 0; j < 3; ++j) {
			for (ulong i_fac = 0; i_fac < vertCount; ++i_fac) {
				cov[i][j] += coordsBar[i_fac][i] * coordsBar[i_fac][j];
			}
			cov[i][j] /= vertCount;
		}
	}
	// Find eigen vectors of cov mat
	vm::vector eigVals;
	vm::vector e0, e1, e2;
	vm::eigenVals3realSymmetric(cov, eigVals);
	vm::eigenVec3(cov, eigVals[0], e0);
	vm::eigenVec3(cov, eigVals[1], e1);
	vm::eigenVec3(cov, eigVals[2], e2);
	// Eigen vectors are columns of transl mat
	vm::matrix transl = { {0.0} };
	for (int i = 0; i < 3; ++i) { 
		transl[i][0] = e0[i];
		transl[i][1] = e1[i];
		transl[i][2] = e2[i];
	}
	// Transform coords
	vertex *transformed = new vertex[vertCount];
	for (ulong i_fac = 0; i_fac < vertCount; ++i_fac) {
		for (int i_coord = 0; i_coord < 3; ++i_coord) {
			transformed[i_fac][i_coord] = (transl[i_coord][0] * coords[i_fac][0])
										+ (transl[i_coord][1] * coords[i_fac][1])
										+ (transl[i_coord][2] * coords[i_fac][2]);
		}
	}
	// Find extents along each direction
	vm::vector maxExtents = { transformed[0][0],transformed[0][1] ,transformed[0][2] };
	vm::vector minExtents = { transformed[0][0],transformed[0][1] ,transformed[0][2] };
	vm::vector extents = { {0.0} };
	for (int i_coord = 0; i_coord < 3; ++i_coord) {
		for (ulong i = 0; i < vertCount; ++i) {
			double val = transformed[i][i_coord];
			if (val > maxExtents[i_coord]) {
				maxExtents[i_coord] = val;
			}
			else if (val < minExtents[i_coord]) {
				minExtents[i_coord] = val;
			}
		}
		extents[i_coord] = maxExtents[i_coord] - minExtents[i_coord];
	}
	// Find principal axis (axis with most extent)
	int principal = 0;
	if (extents[1] > extents[principal]) { principal = 1; }
	if (extents[2] > extents[principal]) { principal = 2; }
	// Calc bounding box
	vm::matrix itransl = { { 0.0 } };
	vm::invertMatrix(transl, itransl);
	for (int i = 0; i < 3; ++i) {
		this->boundingBox[0][i] = (itransl[i][0] * minExtents[0]) + (itransl[i][1] * minExtents[1]) + (itransl[i][2] * minExtents[2]);//x0,y0,z0
		this->boundingBox[1][i] = (itransl[i][0] * minExtents[0]) + (itransl[i][1] * minExtents[1]) + (itransl[i][2] * maxExtents[2]);//x0,y0,z1
		this->boundingBox[2][i] = (itransl[i][0] * minExtents[0]) + (itransl[i][1] * maxExtents[1]) + (itransl[i][2] * minExtents[2]);//x0,y1,z0
		this->boundingBox[3][i] = (itransl[i][0] * minExtents[0]) + (itransl[i][1] * maxExtents[1]) + (itransl[i][2] * maxExtents[2]);//x0,y1,z1		
		this->boundingBox[4][i] = (itransl[i][0] * maxExtents[0]) + (itransl[i][1] * minExtents[1]) + (itransl[i][2] * minExtents[2]);//x1,y0,z0
		this->boundingBox[5][i] = (itransl[i][0] * maxExtents[0]) + (itransl[i][1] * minExtents[1]) + (itransl[i][2] * maxExtents[2]);//x1,y0,z1
		this->boundingBox[6][i] = (itransl[i][0] * maxExtents[0]) + (itransl[i][1] * maxExtents[1]) + (itransl[i][2] * minExtents[2]);//x1,y1,z0
		this->boundingBox[7][i] = (itransl[i][0] * maxExtents[0]) + (itransl[i][1] * maxExtents[1]) + (itransl[i][2] * maxExtents[2]);//x1,y1,z1
	}
	// Find split point along principal axis
	double *principalSort = new double[vertCount];
	for (ulong i = 0; i < vertCount; ++i) { principalSort[i] = transformed[i][principal]; }
	vm::sort_asc(principalSort);
	double splitPoint = principalSort[vertCount/2]; // split in half
	// Split.. splits is true if facet in child0
	bool *splits = new bool[facetCount];
	facCount0 = 0; // facets in child0
	for (ulong i = 0; i < facetCount; ++i) {
		splits[i] = ((transformed[3*i ][principal] < splitPoint) ||
					 (transformed[3*i + 1][principal] < splitPoint) || 
					 (transformed[3*i + 2][principal] < splitPoint));
		facCount0 += (int)splits[i];
	}
	facCount1 = facetCount - facCount0;
	// Populate child facet lists
	childFacetList0 = new Facet [facCount0];
	childFacetList1 = new Facet [facCount1];
	int ctr0 = 0;
	int ctr1 = 0;
	for (ulong i = 0; i < facetCount; ++i) {
		if (splits[i]) {
			childFacetList0[ctr0] = facetList[i];
			ctr0++;
		}
		else {
			childFacetList1[ctr1] = facetList[i];
			ctr1++;
		}
	}
	// Clean up
	delete[] coords;
	delete[] coordsBar;
	delete[] transformed;
	delete[] principalSort;
}

void OBB::makeChildren() {
	children = new OBB[2];
	children[0] = OBB(childFacetList0, facCount0);
	children[1] = OBB(childFacetList1, facCount1);
	hasChildren = true;
}

void OBB::killChildren() {
	if (hasChildren) { delete[] children; }
}



OBB::~OBB() {
	if (facCount0) {	
		std::cout << "fac list cleared" << std::endl;
		delete[] childFacetList0; }
	if (facCount1) {	delete[] childFacetList1; }
	if (hasChildren) { delete[] children; }
}

OBBTree::OBBTree(geom::Mesh mesh, int depth) {
	// number of OBBs is 2^depth


}

void OBBTree::build() {}
}
/*
	obb = root Obb;
	while( obb.has_children() ):
		for i in range(obb.n_children):
			hit = test_hit(obb.child[i])
			if hit:
				set obb = obb.child[i]
				break // break for
	return obb // smallest child hit
*/
/*

OBB::~OBB() {
	if (facCount0) {
		std::cout << "fac list cleared" << std::endl;
		delete[] childFacetList0;
		facCount0 = 0;
	}
	if (facCount1) {
		delete[] childFacetList1;
		facCount1 = 0;
	}
	if (hasChildren) {
		delete[] children;
		hasChildren = false;
	}
}

OBBTree::OBBTree(geom::Mesh mesh, int depth) {
	// number of OBBs is 2^depth
	geom::OBB obb(mesh.facetList, mesh.facetCount);
	obb.makeChildren();
	obb.children[0].makeChildren();
	obb.children[0].children[0].makeChildren();
	obb.children[0].children[0].children[0].makeChildren();

}
*/
