#include <boost/python.hpp>
#include "boost/python/detail/wrap_python.hpp"

std::string greet()
{
    return "Hello I am a Nao!";
}

BOOST_PYTHON_MODULE(nao_test)
{
    using namespace boost::python;
    def("greet", greet);
}
