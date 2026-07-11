#include <cmath>
#include "VectorMaths.h"
#include <iostream>

namespace vm {
	void add(vector v1, vector v2, vector out) {
		out[0] = v1[0] + v2[0];
		out[1] = v1[1] + v2[1];
		out[2] = v1[2] + v2[2];
	}
	void subtract(vector v1, vector v2, vector out) {
		out[0] = v1[0] - v2[0];
		out[1] = v1[1] - v2[1];
		out[2] = v1[2] - v2[2];
	}
	void multiply(vector v1, double a, vector out) {
		out[0] = v1[0] * a;
		out[1] = v1[1] * a;
		out[2] = v1[2] * a;
	}
	void multiply(vector v1, vector v2, vector out) {
		out[0] = v1[0] * v2[0];
		out[1] = v1[1] * v2[1];
		out[2] = v1[2] * v2[2];
	}
	void multiply(matrix mat, double a, matrix out) {
		for (int i = 0; i < 3; ++i) {
			multiply(mat[i], a, out[i]);
		}
	}
	void copyVec(vector v1, vector out) {
		multiply(v1, 1.0, out);
	}
	void cross(vector v1, vector v2, vector out) {
		out[0] = v1[1] * v2[2] - v1[2] * v2[1];
		out[1] = v1[2] * v2[0] - v1[0] * v2[2];
		out[2] = v1[0] * v2[1] - v1[1] * v2[0];
	}
	void negative(vector v1, vector out) {
		out[0] = -v1[0];
		out[1] = -v1[1];
		out[2] = -v1[2];
	}
	double dot(double v1[3], double v2[3]) {
		return (v1[0] * v2[0]) + (v1[1] * v2[1]) + (v1[2] * v2[2]);
	}
	double magnitude(vector v1) {
		return sqrt((v1[0] * v1[0]) + (v1[1] * v1[1]) + (v1[2] * v1[2]));
	}
	void normalise(vector v1, vector out) {
		double invmag = 1.0 / magnitude(v1);
		multiply(v1, invmag, out);
	}
	// From old coord ystem to new... rotmat defines old to new
	void toNewCoordSys(vector coord, vector new_origin, matrix rotmat, vector out) {
		double diff[3];
		subtract(coord, new_origin, diff);
		out[0] = dot(rotmat[0], diff);
		out[1] = dot(rotmat[1], diff);
		out[2] = dot(rotmat[2], diff);
	}

	void applyrotation(vector coord, vector rotationCentre, matrix rotmat, vector out) {
		double diff[3];
		subtract(coord, rotationCentre, diff);
		out[0] = dot(rotmat[0], diff);
		out[1] = dot(rotmat[1], diff);
		out[2] = dot(rotmat[2], diff);
		add(coord, rotationCentre, out);
	}

	// vec3 applyrotation(vec3 coord, vec3 rotationCentre, const mat3& rotmat)
	// {
    // 	return rotmat * (coord - rotationCentre) + rotationCentre;
	// }

	void setToUnity(matrix & matIn) {
		for (int i = 0; i < 3; ++i) {
			for (int j = 0; j < 3; ++j) {
				matIn[i][j] = (double)(i == j);
			}
		}
	}
	int getMaxIndex3(vector v) {
		// returns index of maximum value
		if (v[1] >= v[0]) {
			if (v[2] >= v[1]) {
				return 2;
			}
			else {
				return 1;
			}
		}
		else if (v[2] >= v[0]) {
			return 2;
		}
		else {
			return 0;
		}
	}
	double det(matrix matIn, int dim) {
		double det = 0.0;
		for (int i = 0; i < dim; i++)
		{
			double a = 1.0, b = 1.0;
			for (int row = 0; row < dim; row++)
			{
				a *= matIn[row][(i + row) % dim];
				b *= matIn[row][(dim - 1) - (i + row) % dim];
			}
			det += a - b;
		}
		return det;
	}
	double trace3(matrix matIn) {
		return matIn[0][0] + matIn[1][1] + matIn[2][2];
	}
	void eigenVals3realSymmetric(matrix matIn, vector eigVals) {
		//	algo pulled from https://en.wikipedia.org/wiki/Eigenvalue_algorithm
		double p1 = matIn[0][1] * matIn[0][1] + matIn[0][2] * matIn[0][2] + matIn[1][2] * matIn[1][2];
		double eig0, eig1, eig2;
		if (p1 == 0) {
			// matrix is diagonal
			eig0 = matIn[0][0];
			eig1 = matIn[1][1];
			eig2 = matIn[2][2];
		}
		else {
			matrix I;
			setToUnity(I);
			double q = trace3(matIn) / 3.0;
			double p2 = (matIn[0][0] - q) * (matIn[0][0] - q)
				+ (matIn[1][1] - q) * (matIn[1][1] - q)
				+ (matIn[2][2] - q) * (matIn[2][2] - q) + 2 * p1;
			double p = sqrt(p2 / 6.0);
			matrix B;
			for (int i = 0; i < 3; ++i) {
				for (int j = 0; j < 3; ++j) {
					B[i][j] = (matIn[i][j] - q * I[i][j]) / p;
				}
			}
			double r = 0.5*det(B, 3);
			double phi;
			double pi = atan(1)*4.0;
			if (r <= -1) {
				phi = pi / 3.0;
			}
			else if (r >= 1) {
				phi = 0.0;
			}
			else {
				phi = acos(r) / 3.0;
			}
			// the eigenvalues satisfy eig2 <= eig1 <= eig0
			eig0 = q + 2 * p * cos(phi);
			eig2 = q + 2 * p * cos(phi + (2.0 * pi / 3.0));
			eig1 = 3 * q - eig0 - eig2; // since trace(A;) = eig1 + eig2 + eig3

		}
				
		eigVals[0] = eig0;
		eigVals[1] = eig1;
		eigVals[2] = eig2;
	}

	void eigenVec3(matrix A, double eigVal, vector eigVec) {
		// pulled from https://www.geometrictools.com/Documentation/RobustEigenSymmetric3x3.pdf
		vector row0 = { A[0][0] - eigVal, A[0][1], A[0][2] };
		vector row1 = { A[1][0], A[1][1] - eigVal, A[1][2] };
		vector row2 = { A[2][0], A[2][1], A[2][2] - eigVal };
		vector r0xr1;
		cross(row0, row1, r0xr1);
		vector r0xr2;
		cross(row0, row2, r0xr2);
		vector r1xr2;
		cross(row1, row2, r1xr2);
		vector ds;
		ds[0] = magnitude(r0xr1);
		ds[1] = magnitude(r0xr2);
		ds[2] = magnitude(r1xr2);
		int imax = getMaxIndex3(ds);
		switch(imax) {
		case(0):
			 multiply(r0xr1, 1.0 / ds[0], eigVec);
			break;
		case(1):
			multiply(r0xr2, 1.0 / ds[1], eigVec);
			break;
		case(2):
			multiply(r1xr2, 1.0 / ds[2], eigVec);
			break;
		}
	}

	void invertMatrix(matrix mat, matrix out) {
		double detVal = det(mat, 3);
		adjoint(mat, out);
		multiply(out, 1.0 / detVal, out);
	}

	void transpose(matrix mat) {
		matrix matCopy;
		multiply(mat, 1.0 ,matCopy);
		for (int i = 0; i < 3; ++i) {
			for (int j = 0; j < 3; ++j) {
				mat[i][j] = matCopy[j][i];
			}
		}
	}

	void cofactor(matrix mat, matrix out) {
		out[0][0] = mat[1][1] * mat[2][2] - mat[1][2] * mat[2][1];
		out[0][1] = mat[1][2] * mat[2][0] - mat[1][0] * mat[2][2];
		out[0][2] = mat[1][0] * mat[2][1] - mat[1][1] * mat[2][0];
		out[1][0] = mat[0][2] * mat[2][1] - mat[0][1] * mat[2][2];
		out[1][1] = mat[0][0] * mat[2][2] - mat[0][2] * mat[2][0];
		out[1][2] = mat[0][1] * mat[2][0] - mat[0][0] * mat[2][1];
		out[2][0] = mat[0][1] * mat[1][2] - mat[0][2] * mat[1][1];
		out[2][1] = mat[0][2] * mat[1][0] - mat[0][0] * mat[1][2];
		out[2][2] = mat[0][0] * mat[1][1] - mat[0][1] * mat[1][0];
	}
	
	void adjoint(matrix mat, matrix out) {
		cofactor(mat, out);
		transpose(out);
	}


	int _asc_search(const void * p1, const void * p2)
	{	// for qsort function. Returns -1 if p1 shoule be before p2, +1 for p2 before p1 and 0 if equal
		double d1 = *(double*)p1;
		double d2 = *(double*)p2;
		if (d1 < d2) {
			return -1;
		}
		if (p1 > p2) {
			return 1;
		}
		else {
			return 0;
		}
	}

	void sort_asc(double * values) {
		// sorts array
		int length = sizeof(values) / sizeof(double);
		qsort(values, length, sizeof(double), _asc_search);
	}


//http://www.mathcentre.ac.uk/resources/uploaded/sigma-matrices11-2009-1.pdf
//https://www.varsitytutors.com/hotmath/hotmath_help/topics/adjoint-of-a-matrix
}