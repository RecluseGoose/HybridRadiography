// simplified from http ://www.lfd.uci.edu/~gohlke/code/transformations.py.html
#pragma once

enum rotSpec {
	sxyz, sxyx, sxzy,
	sxzx, syzx, syzy,
	syxz, syxy, szxy,
	szxz, szyx, szyz,
	rzyx, rxyx, ryzx,
	rxzx, rxzy, ryzy,
	rzxy, ryxy, ryxz,
	rzxz, rxyz, rzyz
};

void euler_matrix(double ai, double aj, double ak, rotSpec axes, double rotmat[3][3]);