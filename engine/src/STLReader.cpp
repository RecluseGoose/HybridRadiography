#include "STLReader.h"
#include "FileChecks.h"
#include "VectorMaths.h"
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>

namespace geom {

// void STLReader::readFile(const char * stlfile, Mesh &mesh) {
// 	mesh.clear();
// 	if (!files::checkExists(stlfile)) {
// 		std::cout << "File not found: " << stlfile << std::endl;
// 		return;
// 	}
// 	if (files::isAscii(stlfile)) {
// 		asciiRead(stlfile,mesh);
// 	}
// 	else {
// 		binaryRead(stlfile,mesh);
// 	}
// }

void STLReader::readFile(const std::string stlfile, Mesh &mesh) {
	mesh.clear();
	if (!files::checkExists(stlfile.c_str())) {
		std::cout << "File not found: " << stlfile.c_str() << std::endl;
		return;
	}
	if (files::isAscii(stlfile.c_str())) {
		asciiRead(stlfile.c_str(), mesh);
	}
	else {
		binaryRead(stlfile.c_str(), mesh);
	}
}

void STLReader::asciiRead(const char * stlfile, Mesh &mesh) {
	auto t0 = std::chrono::high_resolution_clock::now();
	const ulong facetCount = getFacetNum(stlfile);
	std::ifstream stlin;
	stlin.open(stlfile);
	std::string word;
	std::string NORMAL = "normal";
	std::string VERTEX = "vertex";
	mesh.facetCount = facetCount;
	mesh.facetList = new Facet[facetCount];
	ulong triCount = 0;
	while(stlin) {
		stlin >> word;
		if (word == NORMAL) {
			readVecIn(stlin, mesh.facetList[triCount].n);
			navPast(stlin, VERTEX, word);
			readVecIn(stlin, mesh.facetList[triCount].v0);
			navPast(stlin, VERTEX, word);
			readVecIn(stlin, mesh.facetList[triCount].v1);
			navPast(stlin, VERTEX, word);
			readVecIn(stlin, mesh.facetList[triCount].v2);
			++triCount;
			stlin.ignore(64, '\n');
			stlin.ignore(64, '\n');
		}
	}
	stlin.close();
}

// helper func for asciiRead
void STLReader::readVecIn(std::ifstream & filein, vertex & out) {
	filein >> out[0];
	filein >> out[1];
	filein >> out[2];
}

// helper func for asciiRead
void STLReader::navPast(std::ifstream &filein, std::string &key, std::string &word) {
	filein >> word;
	while ((word != key) && filein) { filein >> word;}
}

inline bool navPastLineStarting(std::ifstream &fin, std::string &search, std::string &line) {
	bool match;
	getline(fin, line);
	for (int i = 0; i < 5; i++) {
		if (line[i] == search[i]) {
			match = true;
		}
		else {
			match = false;
			break;
		}
	}
	return match;
}

// helper func for asciiRead
ulong STLReader::getFacetNum(const char * stlfile) {
	std::ifstream infile;
	infile.open(stlfile,std::ios::in);
	std::string search = "endfacet"; //endfacet
	std::string line;
	const int checklen = 5;
	ulong ctr = 0;
	while (infile) {
		if (navPastLineStarting(infile, search, line)) {
			++ctr;
			for (int skip = 0; skip < 6; infile.ignore(64, '\n'), ++skip);
		}
	}
	infile.close();
	return ctr;
}

void STLReader::binaryRead(const char * stlfile, Mesh &mesh) {
	std::ifstream stlin;
	stlin.open(stlfile, std::ios::binary);
	// first read header & tricount
	char header[80];		// header always 80 bytes
	ulong triCount;
	stlin.read(reinterpret_cast<char *>(&header), sizeof(header));
	stlin.read(reinterpret_cast<char *>(&triCount), sizeof(unsigned int));
	// Iterate through triabgles
	Triangle tri;
	mesh.facetCount = triCount;
	mesh.facetList = new Facet[triCount];
	for (ulong i = 0; i < triCount; i++) {
		stlin.read(reinterpret_cast<char *>(&tri), sizeof(Triangle));
		vm::vector norm = { tri.normal[0], tri.normal[1], tri.normal[2] };
		vertex v0 = { tri.vertex0[0], tri.vertex0[1], tri.vertex0[2] };
		vertex v1 = { tri.vertex1[0], tri.vertex1[1], tri.vertex1[2] };
		vertex v2 = { tri.vertex2[0], tri.vertex2[1], tri.vertex2[2] };
		mesh.facetList[i] = Facet(v0, v1, v2, norm);
	}
	stlin.close();
}
}