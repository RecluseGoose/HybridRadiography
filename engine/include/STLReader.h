#pragma once
#include "Mesh.h"
#include <string>

namespace geom {
	class STLReader {
	public:
	//void readFile(const char * stlfile, Mesh &mesh);
	void readFile(const std::string stlfile, Mesh &mesh);
	private:
		// Functions for binary reading
		void binaryRead(const char * stlfile, Mesh &mesh);
		// Functions for ascii reading
		void asciiRead(const char * stlfile, Mesh &mesh);
		inline void navPast(std::ifstream &filein, std::string &key, std::string &word);
		inline void readVecIn(std::ifstream &filein, vertex &out);
		inline unsigned long getFacetNum(const char * stlfile);
	private:
		// Triangle struct for binary reading
		#pragma pack(push,1)
		struct Triangle {
			float normal[3];		//REAL32[3]
			float vertex0[3];		//REAL32[3]
			float vertex1[3];		//REAL32[3]
			float vertex2[3];		//REAL32[3]
			unsigned short attr;	//UINT16
		};
		#pragma pack(pop)
	};
}