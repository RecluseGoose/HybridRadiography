#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <sstream>

namespace py = pybind11;

std::string hello(py::array_t<double> array)
{
    auto values = array.unchecked<1>();

    double array_sum_value = 0.0;

    for (size_t i = 0; i < values.shape(0); ++i)
    {
        array_sum_value += values(i);
    }

    std::ostringstream ss;
    ss << "hello " << array_sum_value;

    return ss.str();
}

PYBIND11_MODULE(my_python_module, m)
{
    m.doc() = "Simple pybind11 example";

    m.def(
        "hello",
        &hello,
        "Return hello plus the sum of a numpy array"
    );
}