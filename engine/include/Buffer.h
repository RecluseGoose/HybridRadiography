#pragma once
#include <vector>

using uint  = unsigned int;
using uchar = unsigned char;

template<typename T>
class Buffer {
public:
    Buffer() = default;
    Buffer(uint width, uint height);

    void init(T default_value = T{});
    void reset(T value = T{});

    T getMax() const;
    T getMin() const;

    // 1D access using square brackets (your preference)
    T& operator[](uint i) { return m_data[i]; }
    const T& operator[](uint i) const { return m_data[i]; }

    // 2D access using round brackets (still useful)
    T& operator()(uint x, uint y) { return m_data[y * m_width + x]; }
    const T& operator()(uint x, uint y) const { return m_data[y * m_width + x]; }

    T* data() { return m_data.data(); }
    const T* data() const { return m_data.data(); }

    uint width()  const { return m_width; }
    uint height() const { return m_height; }
    uint size()   const { return static_cast<uint>(m_data.size()); }

private:
    std::vector<T> m_data;
    uint m_width = 0;
    uint m_height = 0;
};