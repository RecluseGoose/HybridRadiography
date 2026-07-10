#include <iostream>
#include <iomanip>
#include "InspecTest.h"

#include <chrono>
#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"
#include "RenWin.h"

using namespace std;

//int main() {
int main(int argc, char* argv[]) {
	// Run tests
	tests::InspecTest();
	// Load
	auto t0 = std::chrono::high_resolution_clock::now();
	geom::Mesh mesh("F:/testdata/fork.stl");
	//geom::Mesh mesh("testdata/test.stl");
	/*geom::STLReader reader;
	reader.readFile("testdata/test.stl", mesh);*/
	mesh.flipNorms = false;
	auto t1 = std::chrono::high_resolution_clock::now();
	std::cout << "File load time: " << std::chrono::duration<double>(t1 - t0).count() << std::endl;
	// Calc lengths
	int xres = 1200;
	int yres = 1000;
	
	t0 = std::chrono::high_resolution_clock::now();
	int N = 10;
	for (int i = 0; i < N; ++i) {
		MaterialPath d(xres, yres, 30., 0.0, 90.0, 0.0, 0.0, 0.0, 300.);
		d.calcLengthBuffer(mesh);
	}
	t1 = std::chrono::high_resolution_clock::now();
	std::cout << "Projected " << mesh.facetCount << " facets, averaged over " << N << " shots in average time of " << std::chrono::duration<double>(t1 - t0).count()*1e3 / N << " ms" << std::endl;
	// Render
	if (true) {
		double it = 0.0;
		if (0) {
			RenWin renwin(xres, yres);
			renwin.init();
			while (renwin.trueUntilQuit()) {
				for (double angle = 0.0; angle < 360.0; angle += 5.0) {
					MaterialPath d(xres, yres, 45.,
						it, 0.0, 0.0,
						0.0, 0.0, -300.);
					d.calcLengthBuffer(mesh);
					d.fixColours(0.0, 30.0, d.lBuffer);
					renwin.loadIntoBuffer(d.lBuffer);
					renwin.update();
					it += 1;
					double sum = 0;
					for (uint i = 0; i < d.lBuffer.wh; ++i) {
						sum += d.lBuffer.buf[i];
					}
					std::cout << sum << std::endl;
				}
			}
		}
		else if (0){

			RenWin renwin(xres, yres);
			renwin.init();
			while (renwin.trueUntilQuit()) {
				//for (double angle = 0.0; angle < 360.0; angle += 5.0){
				MaterialPath d(xres, yres, 45.,
					it, 0.0, 0.0,
					0.0, 0.0, -500.);
				vm::vector coordsIn[1];
				coordsIn[0][0] = mesh.centre[0];
				coordsIn[0][1] = mesh.centre[1];
				coordsIn[0][2] = mesh.centre[2];
				d.coordinateHitImage(1, coordsIn, mesh.centre);
				d.fixColours(0.0, 1.0, d.lBuffer);
				renwin.loadIntoBuffer(d.lBuffer);
				renwin.update();
			}
		}
	}
	else {
		
	}

	if (1) {
		std::string filenames[] = { "D:/testdata/tile.stl", "D:/testdata/cube1.stl" };
		vm::vector offsets[] = { { 0,0,0 } ,{ -3.5,-6,-10.0 } };
		vm::vector angles[] = { { 0.0,0.0,0.0 } ,{ .0,0.0,0.0 } };
		vm::vector scales[] = { { 1.0, 1.0, 1.0 } ,{ 0.1, 0.1, 0.1 } };
		double densities[] = { 1.0, -1.0 };
		bool normFlips[] = { false, false };
		geom::SuperMesh supermesh(2, filenames, angles, offsets, scales, densities, normFlips);
		bool render = true;
		RenWin renwin(xres, yres);
		renwin.init();
		double time = 0.0;
		int N = 50;
		coord2d roi_bl = { 200.0, 200.0 };
		coord2d roi_tr = { 700.0, 600.0 };
		while (true){
			for (int it = 0; it < N; ++it) {

				auto t0 = std::chrono::high_resolution_clock::now();
				MaterialPath d(xres, yres, 30.,
					0.0, it, 0.0,
					3*std::sin(it/50.0), 3*std::cos(it / 40.0), -100.
				);
				d.calcLengthBuffer(supermesh, roi_bl, roi_tr);
				if (render){
					d.fixColours(0.0, 15.0, d.lBuffer);
					renwin.loadIntoBuffer(d.lBuffer);
					renwin.update();
				}
				auto t1 = std::chrono::high_resolution_clock::now();
				time += std::chrono::duration<double>(t1 - t0).count();
				std::cout <<it << " "<< time << std::endl;
			}
			std::cout << "Average tiem: " << time*1000.0/N << " ms" << std::endl;
			break;
		}
	}

	mesh.clear();
	return 0;
}