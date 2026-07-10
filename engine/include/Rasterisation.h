#pragma once
#include "VectorMaths.h"
#include <iostream>

using namespace vm;
typedef unsigned int uint;
typedef double coord2d[2];

class Edge2d {
public:
	Edge2d() {};
	Edge2d(coord2d &p, coord2d &q);
	double evaluate(int x, int y);
	double evaluate(double x, double y);
	double a = 0;
	double b = 0;
	double c = 0;
	void set(coord2d &p, coord2d &q);
};

class InsideTriangle {
public:
	InsideTriangle() {};
	InsideTriangle(coord2d triVerts[3]);
	bool evaluate(int x, int y);
	bool evaluate(vector &eVector);
	void get_eVec(int x, int y, vector &eVector);
	vector aVec = { 0.0 };
	vector bVec = { 0.0 };
	double sign = 1.0;
	int backwards = 0;
	coord2d A;
	coord2d B;
	coord2d C;
private:
	Edge2d edges[3];
	bool tieRule = false;
	bool tieRuleNotCalculated = true;
	double signedArea(coord2d triVerts[3]);
	int getTieRule();
};

class BoundingBoxRasterer {
public:
	BoundingBoxRasterer(coord2d triVerts[3], int width, int height, coord2d roi_tl, coord2d roi_br);
	BoundingBoxRasterer(coord2d triVerts[3], int width, int height);
	bool iterate();
	bool evaluate();
	int x;
	int y;
private:
	InsideTriangle triCheck;
	uint BUF_WIDTH;
	uint BUF_HEIGHT;
	vector eVec;
	int eVec_xEvalPt;
	int eVec_yEvalPt;
	enum directions {ZERO_EXTENT, LEFT, RIGHT, DOWN_AFTER_LEFT, DOWN_AFTER_RIGHT};
	directions stepDir;
	int xmin, xmax, ymin, ymax;
	coord2d evalWin_bl = { 0.0, 0.0 };
	coord2d evalWin_tr = { 0.0, 0.0 };
private:
	void _bbRasterCreator(coord2d triVerts[3], int width, int height, coord2d roi_tl, coord2d roi_br);
	void setStartCoords(coord2d triVerts[3]);
	void setMin(double z, double &zmin);
	void setMax(double z, double &zmax);
};