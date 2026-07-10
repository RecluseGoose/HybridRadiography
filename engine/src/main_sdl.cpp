#include <iostream>
#include <iomanip>
#include "InspecTest.h"

#include <chrono>
#include "STLReader.h"
#include "Mesh.h"
#include "Detector.h"
#include "RenWin.h"
#include <SDL3/SDL_main.h>


const std::string test_file = (std::string)TEST_DATA_DIR + "xyzCube_ascii.stl";

using namespace std;

int main(int argc, char* argv[]) {
#ifdef INCLUDE_SDL
	SDL_SetMainReady();
	// Run tests
	tests::InspecTest();
	// Load
	auto t0 = std::chrono::high_resolution_clock::now();
	geom::Mesh mesh(test_file);

	mesh.flipNorms = false;
	auto t1 = std::chrono::high_resolution_clock::now();
	std::cout << "File load time: " << std::chrono::duration<double>(t1 - t0).count() << std::endl;

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
		if (1) {
			RenWin renwin(xres, yres);
			std::cout << "SDL Init was attempted in main" << std::endl;
			std::cout << renwin.initialised << std::endl;
			renwin.init();
			std::cout << renwin.initialised << std::endl;
			std::cout << "SDL Init was attempted in main" << std::endl;
			std::cout << "renwin.init was attempted in main" << std::endl;
			std::cout << "Testing the quit function:" << std::endl;
			std::cout << renwin.trueUntilQuit() << std::endl;
			std::cout << renwin.trueUntilQuit() << std::endl;
			std::cout << "Quit function:tested" << std::endl;
			std::cout << "testing material path" << std::endl;
			MaterialPath bleugh(xres, yres, 45.,
						it, 0.0, 0.0,
						0.0, 0.0, -300.);
			bleugh.calcLengthBuffer(mesh);
			bleugh.fixColours(0.0, 50.0, bleugh.lBuffer);
			renwin.loadIntoBuffer(bleugh.lBuffer);
			renwin.update();
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
					std::cout << "the buffer sum is " << sum << std::endl;
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

	if (false) {
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
#else
	return 0;
#endif
}