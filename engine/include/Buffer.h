#pragma once
typedef unsigned int uint;
typedef unsigned char uchar;

template <class T> struct Buffer{
	// Methods
	Buffer(uint w, uint h);
	~Buffer();
	void init(T val = 0);
	void resetBuffer (T val = 0 );
	T getMax();
	T getMin();
	// Parameters
	uint w;
	uint h;
	uint wh;
	T *buf = nullptr;
private:
	bool bufInitialised = false;
};


/*
#pragma once
#include <cstddef>
#include <algorithm>
#include <vector>
#include <limits>

using uint  = unsigned int;
using uchar = unsigned char;

template<typename T>
class Buffer {
public:
    Buffer() = default;
    Buffer(uint width, uint height);

    // Rule of 5
    ~Buffer() = default;
    Buffer(const Buffer&) = default;
    Buffer(Buffer&&) noexcept = default;
    Buffer& operator=(const Buffer&) = default;
    Buffer& operator=(Buffer&&) noexcept = default;

    void init(T default_value = T{});
    void reset(T value = T{});

    T getMax() const;
    T getMin() const;

    // Accessors
    T* data() { return m_data.data(); }
    const T* data() const { return m_data.data(); }

    uint width()  const { return m_width; }
    uint height() const { return m_height; }
    uint size()   const { return m_data.size(); }   // total elements

    T& operator()(uint x, uint y) { 
        return m_data[y * m_width + x]; 
    }
    
    const T& operator()(uint x, uint y) const { 
        return m_data[y * m_width + x]; 
    }

private:
    std::vector<T> m_data;
    uint m_width = 0;
    uint m_height = 0;
};

*/