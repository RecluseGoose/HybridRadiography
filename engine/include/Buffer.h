#pragma once
#include <vector>
#include <iostream>

using uint  = unsigned int;
using uchar = unsigned char;

template<typename T>
class Buffer {
public:
    Buffer() = default;
    Buffer(uint width, uint height);
    Buffer(uint width, uint height, T* pre_existing_ptr);

    void init(T default_value = T{});
    void reset(T value = T{});

    T getMax() const;
    T getMin() const;

    int hash();

    // 1D access using square brackets (your preference)
    //T& operator[](uint i) { return m_data[i]; }
    T& operator[](uint i) { return data_[i]; }
    const T& operator[](uint i) const { return data_[i]; }

    // 2D access using round brackets (still useful)
    T& operator()(uint x, uint y) { return data_[y * m_width + x]; }
    const T& operator()(uint x, uint y) const { return data_[y * m_width + x]; }

    T* data() { return data_; }
    const T* data() const { return data_; }

    uint width()  const { return m_width; }
    uint height() const { return m_height; }
    uint size()   const { return m_size;}

private:
    std::vector<T> m_data;
    uint m_width = 0;
    uint m_height = 0;
    uint m_size = 0;

public:
    T* data_; // MUST MUST MUST be declared after m_data (initialised AFTER m_data)
};