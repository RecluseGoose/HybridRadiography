#include "Buffer.h"
#include <iostream>

template <class T> Buffer<T>::Buffer(uint w, uint h) {
	wh = w * h;
	this->w = w;
	this->h = h;
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
		for (uint i = 0; i < wh; ++i) {
			buf[i] = val;
		}
	}
}

template <class T> T Buffer<T>::getMax()
{
	T val = (wh > 0) ? buf[0] : NULL;
	
    for (uint i = 0; i < wh; ++i) {
		if (buf[i] > val){
			val = buf[i];
		}
	}
	
	return val;
}

template <class T> T Buffer<T>::getMin()
{
	T val = (wh > 0) ? buf[0] : NULL;
	
    for (uint i = 0; i < wh; ++i) {
		if (buf[i] < val){
			val = buf[i];
		}
	}
	
	return val;
}

// Need to instantiate specific classes for template for compliler...
template struct Buffer<float>;
template struct Buffer<double>;
template struct Buffer<int>;
template struct Buffer<uchar>;
template struct Buffer<uint>;

/*
template<typename T>
Buffer<T>::Buffer(uint width, uint height) 
    : m_width(width)
    , m_height(height)
    , m_data(width * height)
{
}

template<typename T>
void Buffer<T>::init(T default_value) {
    if (m_data.empty()) {
        m_data.resize(m_width * m_height, default_value);
    }
}

template<typename T>
void Buffer<T>::reset(T value) {
    std::fill(m_data.begin(), m_data.end(), value);
}

template<typename T>
T Buffer<T>::getMax() const {
    if (m_data.empty()) return T{};
    return *std::max_element(m_data.begin(), m_data.end());
}

template<typename T>
T Buffer<T>::getMin() const {
    if (m_data.empty()) return T{};
    return *std::min_element(m_data.begin(), m_data.end());
}

// Explicit instantiations
template class Buffer<float>;
template class Buffer<double>;
template class Buffer<int>;
template class Buffer<unsigned char>;
template class Buffer<unsigned int>;
*/