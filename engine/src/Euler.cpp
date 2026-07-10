#include "Euler.h"
#include <cmath>

int NEXT_AXIS[4] = { 1, 2, 0, 1 };

// inner axis, parity, repetition, frame
int rotSpecToOptions[][4] = {
	{0, 0, 0, 0}, {0, 0, 1, 0}, {0, 1, 0, 0},
	{0, 1, 1, 0}, {1, 0, 0, 0}, {1, 0, 1, 0},
	{1, 1, 0, 0}, {1, 1, 1, 0}, {2, 0, 0, 0},
	{2, 0, 1, 0}, {2, 1, 0, 0}, {2, 1, 1, 0},
	{0, 0, 0, 1}, {0, 0, 1, 1}, {0, 1, 0, 1},
	{0, 1, 1, 1}, {1, 0, 0, 1}, {1, 0, 1, 1},
	{1, 1, 0, 1}, {1, 1, 1, 1}, {2, 0, 0, 1},
	{2, 0, 1, 1}, {2, 1, 0, 1}, {2, 1, 1, 1}
};

void euler_matrix(double ai, double aj, double ak, rotSpec axes, double rotmat[3][3]) {
	bool deg = true;
	if (deg) {
		double degToRad = std::atan(1.0) / 45.0;
		ai = ai * degToRad;
		aj = aj * degToRad;
		ak = ak * degToRad;
	}
	
	int firstaxis = rotSpecToOptions[axes][0];
	bool parity = rotSpecToOptions[axes][1];
	bool repetition = rotSpecToOptions[axes][2];
	bool frame = rotSpecToOptions[axes][3];

	int	i = firstaxis;
	int	j = NEXT_AXIS[i + parity];
	int k = NEXT_AXIS[i - parity + 1];

	if (frame) {
		double tmp = ai;
		ai = ak;
		ak = tmp;
	}
	if (parity) {
		ai = -ai;
		aj = -aj;
		ak = -ak;
	}

	double si = std::sin(ai);
	double sj = std::sin(aj);
	double sk = std::sin(ak);
	double ci = std::cos(ai);
	double cj = std::cos(aj);
	double ck = std::cos(ak);
	double cc = ci * ck;
	double cs = ci * sk;
	double sc = si * ck;
	double ss = si * sk;

	if (repetition) {
		rotmat[i][i] = cj;
		rotmat[i][j] = sj * si;
		rotmat[i][k] = sj * ci;
		rotmat[j][i] = sj * sk;
		rotmat[j][j] = -cj * ss + cc;
		rotmat[j][k] = -cj * cs - sc;
		rotmat[k][i] = -sj * ck;
		rotmat[k][j] = cj * sc + cs;
		rotmat[k][k] = cj * cc - ss;
	}
	else {
		rotmat[i][i] = cj * ck;
		rotmat[i][j] = sj * sc - cs;
		rotmat[i][k] = sj * cc + ss;
		rotmat[j][i] = cj * sk;
		rotmat[j][j] = sj * ss + cc;
		rotmat[j][k] = sj * cs - sc;
		rotmat[k][i] = -sj;
		rotmat[k][j] = cj * si;
		rotmat[k][k] = cj * ci;
	}
}