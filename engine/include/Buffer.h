#pragma once
typedef unsigned int uint;
typedef unsigned char uchar;

template <class T> struct Buffer{
	// Methods
	Buffer();
	Buffer(uint w, uint h);
	~Buffer();
	void init(T val = 0);
	void resetBuffer (T val = 0 );
	T getMax();
	T getMin();
	// Parameters
	uint w = 0;
	uint h = 0;
	uint wh = 0;
	T *buf = nullptr;
private:
	bool bufInitialised = false;
};