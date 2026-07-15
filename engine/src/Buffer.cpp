#include "Buffer.h"
#include <algorithm>

template<typename T>
Buffer<T>::Buffer(uint width, uint height)
    : m_width(width)
    , m_height(height)
    , m_size(width * height)
    , m_data(width * height)
    , data_(m_data.data())
{
    // std::cout
    // << "this=" << this
    // << " data_=" << static_cast<void*>(data_)
    // << " m_data=" << static_cast<void*>(m_data.data())
    // << '\n';
}

template<typename T>
Buffer<T>::Buffer(uint width, uint height, T* pre_existing_ptr)
    : m_width(width)
    , m_height(height)
    , m_size(width * height)
    , data_(pre_existing_ptr)
{
}

template<typename T>
void Buffer<T>::init(T default_value)
{
    // if (m_data.empty() && m_width > 0 && m_height > 0) {
    //     m_data.resize(m_width * m_height, default_value);
    // }
    for (int i=0; i<m_size; ++i){data_[i] = default_value;}
}

template<typename T>
void Buffer<T>::reset(T value)
{
    for (int i=0; i<m_size; ++i){data_[i] = value;}
}

template<typename T>
T Buffer<T>::getMax() const
{
    // if (m_data.empty()) return T{};
    // return *std::max_element(m_data.begin(), m_data.end());
    if (m_size == 0){return 0;}
    T max = data_[0];
    for (int i=1; i<m_size; ++i){
        if (data_[i] > max){max = data_[i];}
    }
    return max;
}

template<typename T>
T Buffer<T>::getMin() const
{
    // if (m_data.empty()) return T{};
    // return *std::min_element(m_data.begin(), m_data.end());
    if (m_size == 0){return 0;}
    T min = data_[0];
    for (int i=1; i<m_size; ++i){
        if (data_[i] < min){min = data_[i];}
    }
    return min;
}

template <typename T>
int Buffer<T>::hash()
{
    int h = 0;
    int i_max = size();

    for (int i=0; i<i_max; ++i){
        float f = (i + 21476000)*data_[i];
        h += (int) f;
    }

    return h;
}

// Explicit template instantiations
template class Buffer<float>;
template class Buffer<double>;
template class Buffer<int>;
template class Buffer<unsigned char>;
template class Buffer<unsigned int>;