#include "Buffer.h"
#include <iostream>

template<class T> Buffer<T>::Buffer(){}

template <class T> Buffer<T>::Buffer(uint w, uint h) {
	wh = w * h;
	resetBuffer();
}

template <class T> Buffer<T>::~Buffer() {
	if (bufInitialised) {
		delete[] buf;
	}	
	buf = nullptr;
}

template<class T>void Buffer<T>::init(T val){
	if (!bufInitialised) {
		buf = new T[wh];
		bufInitialised = true;
		resetBuffer(val);
	}
}

template <class T> void Buffer<T>::resetBuffer(T val){
	if (bufInitialised) {
		/*if (val == 0) {
			//std::memset(buf, 0, wh * sizeof(T));
		}
		else {*/
			for (uint i = 0; i < wh; ++i) {
				buf[i] = val;
			//}
		}
	}
}

// Need to instantiate specific classes for template for compliler...
template struct Buffer<float>;
template struct Buffer<double>;
template struct Buffer<int>;
template struct Buffer<uchar>;
template struct Buffer<uint>;