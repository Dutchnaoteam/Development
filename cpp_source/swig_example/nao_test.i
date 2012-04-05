%module nao_test

%{
    extern std::string greet();
%}

%typemap(out) std::string {
    $result = PyString_FromString($1.c_str());
}

%include "nao_test.cpp"
