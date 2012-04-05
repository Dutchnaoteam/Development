%module nao_test

%{
    extern std::string greet();
%}

%include "nao_test.cpp"
