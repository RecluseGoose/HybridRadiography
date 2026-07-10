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

/*

#pragma once
#include <vector>
#include <cstddef>   // for size_t if needed

using uint  = unsigned int;
using uchar = unsigned char;

template<typename T>
class Buffer {
public:
    Buffer() = default;
    Buffer(uint width, uint height);

    // Rule of zero - let std::vector handle everything
    ~Buffer() = default;

    void init(T default_value = T{});
    void reset(T value = T{});

    T getMax() const;
    T getMin() const;

    // 2D access - this is the nice part
    T& operator()(uint x, uint y);
    const T& operator()(uint x, uint y) const;

    // Raw access if you need it for speed
    T* data();
    const T* data() const;

    uint width()  const { return m_width; }
    uint height() const { return m_height; }
    uint size()   const { return static_cast<uint>(m_data.size()); }

private:
    std::vector<T> m_data;
    uint m_width = 0;
    uint m_height = 0;
};
*/