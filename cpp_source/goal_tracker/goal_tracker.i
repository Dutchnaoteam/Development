%module nao_test

%{
    extern int main(int argc, const char* argv[]);
%}

%include "nao_test.cpp"
%include "nao_test.h"
