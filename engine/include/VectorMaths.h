#pragma once
//#include "glm_compat.h"

namespace vm {
	typedef double vector[3];
	typedef double matrix[3][3];
	void add(vector v1, vector v2, vector out);
		// vec3 applyrotation(vec3 coord, vec3 rotationCentre, const mat3& rotmat)
	void subtract(vector v1, vector v2, vector out);
	void multiply(vector v1, double a, vector out);
	void multiply(vector v1, vector v2, vector out);
	void multiply(matrix mat, double a, matrix out);
	void copyVec(vector v1, vector out);
	void cross(vector v1, vector v2, vector out);
	void negative(vector v1, vector out);
	double dot(double v1[3], double v2[3]);
	double magnitude(vector v1);
	void normalise(vector v1, vector out);
	void toNewCoordSys(vector coord, vector new_origin, matrix rotmat, vector out);
	void applyrotation(vector coord, vector rotationCentre, matrix rotmat, vector out);
	void setToUnity(matrix &matIn);
	int getMaxIndex3(vector v);
	double det(matrix matIn, int dim);
	double trace3(matrix matIn);
	void eigenVals3realSymmetric(matrix matIn, vector eigVals);
	void eigenVec3(matrix A, double eigVal, vector eigVec);
	void invertMatrix(matrix mat, matrix invMat);
	void transpose(matrix mat);
	void cofactor(matrix mat, matrix out);
	void adjoint(matrix mat, matrix out);
	void sort_asc(double* arr_1d);
}