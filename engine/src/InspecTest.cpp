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
	const std::string asc_file = std::string(TEST_DATA_DIR) + "xyzCube_ascii.stl";
	const std::string bin_file = std::string(TEST_DATA_DIR) + "xyzCube_binary.stl";

    // Helper for floating point comparison
    bool almost_equal(double a, double b, double epsilon) {
        return std::abs(a - b) <= epsilon;
    }

    void InspecTest() {
        std::cout << "=== Starting Tests ===\n";
        
		int fail_count = 0;
        if(!test_FileChecks()) fail_count++;
        if(!test_VectorMaths()) fail_count++;
		if(!test_MeshAndSTLReader()) fail_count++;
		if(!test_Buffer()) fail_count++;
		if(!test_SDL()) fail_count++;
		if(!test_RenWin()) fail_count++;            

		if (fail_count > 0){
			std::cout << std::to_string(fail_count) + " tests failed\n";
		}
		
        std::cout << "=== Tests Finished ===\n";
    }

    bool test_FileChecks() {
        int failures = 0;

        if (files::checkExists(asc_file.c_str()) != 1) failures++;
        if (files::checkExists(bin_file.c_str()) != 1) failures++;
        if (files::checkExists("nonexistent_file_12345.stl") != 0) failures++;

        if (files::isAscii(asc_file.c_str()) != true) failures++;
        if (files::isAscii(bin_file.c_str()) != false) failures++;

        if (failures) std::cout << "FileChecks FAILED (" + std::to_string(failures) + " issues)\n";

		return failures == 0;
    }


	bool test_VectorMaths() {
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
		
		return code == 0;
	}

	bool test_MeshAndSTLReader() {
        int failures = 0;
        
		geom::STLReader reader;
        geom::Mesh mesh;

		reader.readFile(bin_file, mesh);
		if (mesh.facetCount != 160){
			failures++;
			std::cout << "Facet count for bin file " << mesh.facetCount << std::endl;
		}
        reader.readFile(asc_file, mesh);
        if (mesh.facetCount != 160){
			failures++;
			std::cout << "Facet count for ascii file " << mesh.facetCount << std::endl;
		}

        mesh.update();
		if (!almost_equal(mesh.length, 69.282, 1e-3)){
 			failures++;
			std::cout << "Length (*1e6) " << mesh.length*1e6 << std::endl;
		}
		if (!almost_equal(mesh.boundingBox[0], -20.0)){
			failures++;
			std::cout << "Bounding box " << mesh.boundingBox[0] << std::endl;
		}
		if (!almost_equal(mesh.centre[0], -1e-6)){
			failures++;
			std::cout << "Centre0 (*1e6) " << mesh.centre[0]*1e6 << std::endl;
		}
		if (!almost_equal(mesh.centre[1], 0.0, 1e-5)){
			failures++;
			std::cout << "Centre1 (*1e6) " << mesh.centre[1]*1e6 << std::endl;
		}
		if (mesh.vertCount != 480){
			failures++;
			std::cout << "Vert Count " << mesh.vertCount << std::endl;
		}

		if (failures) std::cout << "MeshAndSTLReader FAILED (" + std::to_string(failures) + " issues)\n";
		return failures == 0;
    }
	
	bool test_SDL()	{
		#ifdef INCLUDE_SDL	
		int failures = 0;
		if (!(SDL_Init(SDL_INIT_EVERYTHING)) == 0) {
			failures++;
			std::cout << "SDL didn't init properly" << std::endl;
		}
		SDL_Quit();
		if (code) {
			failures++;
			std::cout << "Error initialising SDL" << std::endl;
		}

		if (failures) std::cout << "SDL FAILED (" + std::to_string(failures) + " issues)\n";
		return failures == 0;

		#else
		std::cout << "SDL skipped\n";
		return true;
		#endif
	}

	bool test_Buffer(){
		int failures = 0;
		Buffer <double> buffer(11,11);
		buffer.init();
		double sum = 0.0;
		buffer[23] = 12.3;

		for (unsigned int i = 0; i < buffer.size(); ++i) {
			sum += buffer[i];
		}
		if (sum != 12.3) {
			failures ++;
		}
		buffer.reset();
		sum = 0.0;
		for (unsigned int i = 0; i < buffer.size(); ++i) {
			sum += buffer[i];
		}
		if (sum != 0.0) {
			failures ++;
		}
		
		if (failures) std::cout << "Buffer FAILED (" + std::to_string(failures) + " issues)\n";
		return failures == 0;
	}

	bool test_RenWin() {

		#ifdef INCLUDE_SDL
		RenWin renWin(120, 120);
		renWin.init();
		// no tests really?
		#else
		std::cout << "Renwin skipped\n";
		#endif
		
		return true;
	}
}