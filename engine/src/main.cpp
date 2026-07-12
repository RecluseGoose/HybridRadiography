#include <iostream>
#include <iomanip>
#include "InspecTest.h"

#include <chrono>
#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"

using namespace std;

const std::string test_file = (std::string)TEST_DATA_DIR + "xyzCube_ascii.stl";

//int main() {
int main(int argc, char* argv[]) {
	// Run tests
	tests::InspecTest();
	// Load
	auto t0 = std::chrono::high_resolution_clock::now();
	geom::Mesh mesh(test_file);
	mesh.flipNorms = false;
	auto t1 = std::chrono::high_resolution_clock::now();
	std::cout << "File load time: " << std::chrono::duration<double>(t1 - t0).count() << std::endl;
	// Calc lengths
	int xres = 400;
	int yres = 471;	
	
	t0 = std::chrono::high_resolution_clock::now();
	int N = 50;
	for (int i = 0; i < N; ++i) {
		MaterialPath d(xres, yres, 30., 0.0, 90.0, 0.0, 0.0, 0.0, -300.);		
		d.calcLengthBuffer(mesh);
	}

	t1 = std::chrono::high_resolution_clock::now();
	std::cout << "Projected " << mesh.facetCount << " facets, averaged over " << N << " shots in average time of " << std::chrono::duration<double>(t1 - t0).count()*1e3 / N << " ms" << std::endl;

	mesh.clear();
	return 0;
}