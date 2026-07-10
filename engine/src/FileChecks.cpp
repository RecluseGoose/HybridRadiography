#include "FileChecks.h"
#include <iostream>
#include <fstream>

namespace files {
	bool checkExists(const char * filename) {
		std::ifstream infile;
		infile.open(filename);
		bool isOpenable = infile.is_open();
		infile.close();
		return isOpenable;
	}

	bool isAscii(const char * filename) {
		// TODO: test this with rigour.
		std::ifstream infile(filename);
		unsigned int c = infile.get();
		int iterations = 0;
		const int iter_max = 100; // num of characters to read before deduce is ascii
		while ((c <= 127) && (iterations < iter_max)) {
			c = infile.get();
			iterations++;
		}
		infile.close();
		return (iterations == iter_max);
	}
}