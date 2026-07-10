#pragma once
#include <iostream>
#include <cmath>
#include "InspecTest.h"
#include "FileChecks.h"
#include "VectorMaths.h"
#include "Mesh.h"
#include "STLReader.h"
#include "Buffer.h"
#ifdef INCLUDE_SDL
#include "RenWin.h"
#include <SDL.h>
#endif

namespace tests {
	// TEST_DATA_DIR from cmake compile definitions
	const std::string asc_file = (std::string)TEST_DATA_DIR + "xyzCube_ascii.stl";
	const std::string bin_file = (std::string)TEST_DATA_DIR + "xyzCube_binary.stl";

	void InspecTest() {
		std::cout << "Tests start." << std::endl;
		test_FileChecks();
		test_VectorMaths();
		test_MeshAndSTLReader();
		test_SDL();
		test_Buffer();
		test_RenWin();
		std::cout << "Tests finished." << std::endl;
	}
	
	void test_FileChecks() {
		// files::checkExists
		int code =0 ;
		std::cout<< "looking for " << asc_file << std::endl;
		if (!(files::checkExists(asc_file.c_str()) == 1)) { code = 1; }
		if (!(files::checkExists(bin_file.c_str()) == 1)) { code = 2; }
		if (!(files::checkExists("") == 0)) { code = 3; }
		// files::isAscii
		if (!files::isAscii(asc_file.c_str())) { code = 4; }
		if (files::isAscii(bin_file.c_str())) { code = 5; }
		if (code) {
			std::cout << "Test FileChecks.h failed with code " << code << std::endl;
		}

	}
	void test_VectorMaths() {
		int code = 0;
		vm::vector v1 = { 1.2, 4.2, 5.0 };
		vm::vector v2 = { 4.8, 2.4,-4.2 };
		vm::vector out;
		double d;
		vm::matrix rotmat = { {0.0} };
		rotmat[0][0] = -1.0;
		rotmat[1][1] = 1.0;
		rotmat[2][2] = -1.0;;
		// vm::add
		vm::add(v1, v2, out);
		if (!((out[0] == 1.2 + 4.8) && (out[1] == 4.2 + 2.4) && (out[2] == 5.0 - 4.2))) { code = 1;	}
		// vm::subtract
		vm::subtract(v1, v2, out);
		if (!((out[0] == 1.2 - 4.8) && (out[1] == 4.2 - 2.4) && (out[2] == 5.0 + 4.2))) { code = 2;	}
		// vm::multiply
		vm::multiply(v1, 1.5, out);
		if (!((out[0] == 1.2 * 1.5) && (out[1] == 4.2 * 1.5) && (out[2] == 5.0 * 1.5))) { code = 3;	}
		// vm::negative
		vm::negative(v2, out);
		if (!((out[0] == - 4.8) && (out[1] == - 2.4) && (out[2] == 4.2))) { code = 4; }
		// vm::dot
		d = vm::dot(v1, v2);
		if (!(d == 1.2*4.8 + 4.2*2.4 - 5.0*4.2)) { code = 5; }
		// vm::magnitude
		d = vm::magnitude(v1);
		if (!(d * d == 1.2*1.2 + 4.2*4.2 + 5.0*5.0)) { code = 6; }
		// vm::normalise
		vm::normalise(v1, out);
		if (!((std::round(out[0]*1e6) == std::round(1e6*1.2/d)) &&
			  (std::round(out[1]*1e6) == std::round(1e6*4.2/d)) &&
			  (std::round(out[2]*1e6) == std::round(1e6*5.0/d)))) {
			code = 7; }
		//vm::toNewCoordSys
		vm::toNewCoordSys(v1, v2, rotmat, out);
		if (!((out[0] == 4.8-1.2) && (out[1] == 4.2-2.4) && (out[2] == -5.0-4.2))) { code = 8; }
		if (code) {
			std::cout << "Test VectorMaths.h failed with code " << code << std::endl;
		}
	}
	void test_MeshAndSTLReader() {
		int code = 0;
		geom::STLReader reader = geom::STLReader();
		geom::Mesh mesh;
		//repeat these tests multiple times to check for floating references
		//geom::STLReader::binaryRead
		for (int attempts = 0; attempts < 20; attempts++) {
			reader.readFile(bin_file, mesh);
			if (!(mesh.facetCount == 92)) {
				code = 1;
			}
			//geom::STLReader::asciiRead
			reader.readFile(asc_file, mesh);
			if (!(mesh.facetCount == 92)) {
				code = 2;
			}
			mesh.update();
			//geom::Mesh::updateLength
			if (!(std::round(mesh.length*1e5))) { code = 3; };
			//geom::Mesh::updateBoundingBox
			if (!(std::round(mesh.boundingBox[0] * 1e6) == -951058)) { code = 4; };
			//geom::Mesh::updateCentre
			if (!(std::round(mesh.centre[0] * 1e6) == 0)) { code = 5; };
			//geom::Mesh::updateVertexList
			if (!(mesh.vertCount == 276)) { code = 6; };
		}
		if (code) {
			std::cout << "Test Mesh.h and STLReader.h failed with code " << code << std::endl;
		}
	}
	void test_SDL()	{
		#ifdef INCLUDE_SDL	
		int code = 0;
		if (!(SDL_Init(SDL_INIT_EVERYTHING)) == 0) {
			code = 1;
		}
		SDL_Quit();
		if (code) {
			std::cout << "Error initialising SDL" << std::endl;
		}
		#endif
	}
	void test_Buffer(){
		int code = 0;
		Buffer <double> buffer(11,11);
		buffer.init();
		double sum = 0.0;
		buffer[23] = 12.3;
		for (unsigned int i = 0; i < buffer.getLength(); ++i) {
			sum += buffer[i];
		}
		if (sum != 12.3) {
			code = 1;
		}
		buffer.reset();
		sum = 0.0;
		for (unsigned int i = 0; i < buffer.getLength(); ++i) {
			sum += buffer[i];
		}
		if (sum != 0.0) {
			code = 2;
		}
		if (code) {
			std::cout << "Error with Buffer " << code << std::endl;
		}
	}
	void test_RenWin() {

		#ifdef INCLUDE_SDL
		int code = 0;
		RenWin renWin(120, 120);
		renWin.init();
		if (code) {
			std::cout << "Error with RenWin " << code << std::endl;
		}
		#endif
	}
}