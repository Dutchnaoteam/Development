#include <iostream>
#include <boost/python.hpp>
#include <Python.h>

std::string greet(std::string name)
{
    std::stringstream sstream;
    sstream << "Hello " << name << "!" << std::endl;
    return sstream.str();
}

BOOST_PYTHON_MODULE(testing)
{
    using namespace boost::python;
    def("greet", greet);
}
