#pragma once

namespace tests{
	bool almost_equal(double a, double b, double epsilon = 1e-6);
	void InspecTest();
	bool test_FileChecks();
	bool test_VectorMaths();
	bool test_MeshAndSTLReader();
	bool test_SDL();
	bool test_Buffer();
	bool test_RenWin();
}