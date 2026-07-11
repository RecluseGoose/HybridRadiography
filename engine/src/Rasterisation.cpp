#include "Rasterisation.h"
#include <iostream>

Edge2d::Edge2d(coord2d &p, coord2d &q){
	set(p, q);
}

void Edge2d::set(coord2d &p, coord2d &q){
	a = p[1] - q[1];
	b = q[0] - p[0];
	c = p[0] * q[1] - q[0] * p[1];
}

double Edge2d::evaluate(int x, int y){
	return a*x + b*y + c;
}

double Edge2d::evaluate(double x, double y){
	return a*x + b*y + c;
}

InsideTriangle::InsideTriangle(coord2d triVerts[3]) {
	if (signedArea(triVerts) > 0) {
		edges[0].set(triVerts[0], triVerts[1]);
		edges[1].set(triVerts[1], triVerts[2]);
		edges[2].set(triVerts[2], triVerts[0]);
	}
	else {
		edges[0].set(triVerts[0], triVerts[2]);
		edges[1].set(triVerts[1], triVerts[0]);
		edges[2].set(triVerts[2], triVerts[1]);
		backwards++;
	}
	for (int i = 0; i < 3; ++i) {
		aVec[i] = edges[i].a;
		bVec[i] = edges[i].b;
	}
}

void InsideTriangle::get_eVec(int x, int y, vm::vector & eVector) {
	for (int i = 0; i < 3; ++i) {
		eVector[i] = edges[i].evaluate(x, y);
	}
}

double InsideTriangle::signedArea(coord2d triVerts[3]){
	double area = 0.0;
	for (int i_vert = 0; i_vert < 3; ++i_vert) {
		double x1 = triVerts[i_vert][0];
		double y1 = triVerts[i_vert][1];
		double x2 = triVerts[(i_vert + 1) % 3][0];
		double y2 = triVerts[(i_vert + 1) % 3][1];
		area += (x1 * y2 - x2 * y1);
	}
	return 0.5*area;
}

bool InsideTriangle::evaluate(int x, int y) {
	vector eVec;
	get_eVec(x, y, eVec);
	return evaluate(eVec);
}

bool InsideTriangle::evaluate(vm::vector &eVector) {
	// CASE 2
	if ((eVector[0] < 0) || (eVector[1] < 0) || (eVector[2] < 0)) {
		return false;
	}
	// CASE 1
	else if ((eVector[0] > 0) && (eVector[1] > 0) && (eVector[2] > 0)) {
		return true;
	}
// cropping as this never comes up... and probably doesn't work anyway
	else {
		//std::cout << "TIE RULE REQUIRED! " << std::endl;
		return false;
	}
/*	// ambiguous... is on edge
	else {
		if (tieRuleNotCalculated) {
			int code = getTieRule();
			tieRuleNotCalculated = false;
			tieRule = (bool)(code % 2);
			std::cout << "Tie rule calculated " << tieRule << " " << code<< std::endl;
		}
		return tieRule;
	}
*/
}

int InsideTriangle::getTieRule() {
	// Check a lt 0s, if any true return false...if((alt0[0] || alt ))
	double a_sum = aVec[0] + aVec[1] + aVec[2];
	if (a_sum < 0) {
		return 4;
	}
	if (a_sum > 0) {
		return 3;
	}
	double b_sum = bVec[0] + bVec[1] + bVec[2];
	if (b_sum >= 0){
		return 5;
	}
	return 6;
}

BoundingBoxRasterer::BoundingBoxRasterer(coord2d triVerts[3], int width, int height, coord2d roi_tl, coord2d roi_br) {
	_bbRasterCreator(triVerts, width, height, roi_tl, roi_br);
}

BoundingBoxRasterer::BoundingBoxRasterer(coord2d triVerts[3], int width, int height) {
	// Set default ROI to full window
	coord2d roi_bl = {0.0};
	coord2d roi_tr = { (double)width - 1.0, (double)height - 1.0 };
	// Create as usual
	_bbRasterCreator(triVerts, width, height, roi_bl, roi_tr);
}

// BoundingBoxRasterer::BoundingBoxRasterer(std::vector<vec2> triVerts, int width, int height)
// {
// 	coord2d triVerts_vm[3];
// 	to_vm(triVerts[0], triVerts_vm[0]);
// 	to_vm(triVerts[1], triVerts_vm[1]);
// 	to_vm(triVerts[2], triVerts_vm[2]);
// 	// Set default ROI to full window
// 	coord2d roi_bl = {0.0};
// 	coord2d roi_tr = { (double)width - 1.0, (double)height - 1.0 };
// 	// Create as usual
// 	_bbRasterCreator(triVerts_vm, width, height, roi_bl, roi_tr);
// }

void BoundingBoxRasterer::_bbRasterCreator(coord2d triVerts[3], int width, int height, coord2d roi_bl, coord2d roi_tr) {
	triCheck = InsideTriangle(triVerts);
	BUF_HEIGHT = height;
	BUF_WIDTH = width;
	// set evaluation window
	evalWin_bl[0] = roi_bl[0];
	evalWin_bl[1] = roi_bl[1];
	evalWin_tr[0] = roi_tr[0];
	evalWin_tr[1] = roi_tr[1];
	// TODO!! Intelligently set starting x,y
	//y will step into y on starting y on first iteration
	setStartCoords(triVerts);
	y = ymin;
	x = xmin;
	y--;
	// TODO! This will screw up for sub-zero pixels, but for that I need to solve robustness issue.
	if ((xmax > xmin) && (ymax > ymin)) {
		stepDir = DOWN_AFTER_LEFT;
	}
	else {
		stepDir = ZERO_EXTENT;
	}
	// Evaluate initial eVec
	eVec_xEvalPt = x;
	eVec_yEvalPt = y;
	triCheck.get_eVec(eVec_xEvalPt, eVec_yEvalPt, eVec);
}

bool BoundingBoxRasterer::iterate() {
	switch (stepDir) {
	case(LEFT):
		--x;
		vm::subtract(eVec, triCheck.aVec, eVec);
		if (x == xmin) {
			stepDir = DOWN_AFTER_LEFT;
		}
		return true;
	case(RIGHT):
		++x;
		vm::add(eVec, triCheck.aVec, eVec);
		if (x == xmax) {
			stepDir = DOWN_AFTER_RIGHT;
		}
		return true;
	case(DOWN_AFTER_LEFT):
		++y;
		vm::add(eVec, triCheck.bVec, eVec);
		stepDir = RIGHT;
		return (!(y > ymax));
	case(DOWN_AFTER_RIGHT):
		++y;
		vm::add(eVec, triCheck.bVec, eVec);
		stepDir = LEFT;
		return (!(y > ymax));
	case (ZERO_EXTENT):
		return false;
	}
	return false;
}

bool BoundingBoxRasterer::evaluate() {
	return triCheck.evaluate(eVec);
}

void BoundingBoxRasterer::setStartCoords(coord2d triVerts[3]) {
	double ax = triVerts[0][0];
	double ay = triVerts[0][1];
	double bx = triVerts[1][0];
	double by = triVerts[1][1];
	double cx = triVerts[2][0];
	double cy = triVerts[2][1];
	// xmin
	double xmin_d = (double)(BUF_WIDTH - 1);
	setMin(ax, xmin_d);
	setMin(bx, xmin_d);
	setMin(cx, xmin_d);
	//setMax(0.0, xmin_d);
	setMax(evalWin_bl[0], xmin_d);
	xmin = (int)xmin_d;
	// ymin
	double ymin_d = (double)(BUF_HEIGHT - 1);
	setMin(ay, ymin_d);
	setMin(by, ymin_d);
	setMin(cy, ymin_d);
	//setMax(0.0, ymin_d);
	setMax(evalWin_bl[1], ymin_d);
	ymin = (int)ymin_d;
	// xmax
	double xmax_d = 0.0;
	setMax(ax, xmax_d);
	setMax(bx, xmax_d);
	setMax(cx, xmax_d);
	//setMin((double)(BUF_WIDTH - 1), xmax_d);
	setMin(evalWin_tr[0], xmax_d);
	xmax = (int)xmax_d;
	// ymax
	double ymax_d = 0.0;
	setMax(ay, ymax_d);
	setMax(by, ymax_d);
	setMax(cy, ymax_d);
	//setMin((double)(BUF_HEIGHT - 1), ymax_d);
	setMin(evalWin_tr[1], ymax_d);
	ymax = (int)ymax_d;
}

void BoundingBoxRasterer::setMin(double z,double &zmin) {
	if (z < zmin) {
		zmin = z;
	}
}

void BoundingBoxRasterer::setMax(double z, double &zmax) {
	if (z > zmax) {
		zmax = z;
	}
}