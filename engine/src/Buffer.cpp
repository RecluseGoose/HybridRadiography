#include "Buffer.h"
#include <algorithm>

template<typename T>
Buffer<T>::Buffer(uint width, uint height)
    : m_width(width)
    , m_height(height)
    , m_data(width * height)
{
}

template<typename T>
void Buffer<T>::init(T default_value)
{
    if (m_data.empty() && m_width > 0 && m_height > 0) {
        m_data.resize(m_width * m_height, default_value);
    }
}

template<typename T>
void Buffer<T>::reset(T value)
{
    std::fill(m_data.begin(), m_data.end(), value);
}

template<typename T>
uint Buffer<T>::getLength() const
{
    return static_cast<uint>(m_data.size());
}

template<typename T>
T Buffer<T>::getMax() const
{
    if (m_data.empty()) return T{};
    return *std::max_element(m_data.begin(), m_data.end());
}

template<typename T>
T Buffer<T>::getMin() const
{
    if (m_data.empty()) return T{};
    return *std::min_element(m_data.begin(), m_data.end());
}

// Explicit template instantiations
template class Buffer<float>;
template class Buffer<double>;
template class Buffer<int>;
template class Buffer<unsigned char>;
template class Buffer<unsigned int>;