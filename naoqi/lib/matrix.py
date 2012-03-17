import random
import math
from time import *

 
def zero(m,n):
    # Create zero matrix
    new_matrix = [[0 for row in range(n)] for col in range(m)]
    return new_matrix
 
def rand(m,n):
    # Create random matrix
    new_matrix = [[random.random() for row in range(n)] for col in range(m)]
    return new_matrix
 
def show(matrix):
    # Print out matrix
    for col in matrix:
        print col 

def transpose(matrix):
    new_matrix = zero(len(matrix[0]), len(matrix))
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            new_matrix[j][i] = matrix[i][j]
    return new_matrix

def inverse3D(matrix):
    if len(matrix) != 3 or len(matrix[0]) != 3:
        print 'Matrix must be 3x3 for this inverse function'
    else:
        new_matrix = zero(3,3)
        a= matrix[0][0]
        b= matrix[0][1]
        c= matrix[0][2]

        d= matrix[1][0]
        e= matrix[1][1]
        f= matrix[1][2]

        g= matrix[2][0]
        h= matrix[2][1]
        k= matrix[2][2]
        try:
            det = 1.0/ (a * (e*k-f*h) + b* (f*g-k*d) + c * (d*h-e*g))

            A = (e*k - f*h )* det
            B = (f*g - d*k )* det
            C = (d*h - e*g )* det
            D = (c*h - b*k )* det
            E = (a*k - c*g )* det
            F = (g*b - a*h )* det
            G = (b*f - c*e )* det
            H = (c*d - a*f )* det
            K = (a*e - b*d )* det

            new_matrix = [[A,D,G],[B,E,H],[C,F,K]]

            return new_matrix            
        except:
            print 'Matrix can not be inverted.'
            
def inverse2D(matrix):
    if len(matrix) != 2 or len(matrix[0]) != 2:
        print 'Matrix must be 2x2 for this inverse function'
    else:
        new_matrix = zero(2,2)
        a= matrix[0][0]
        b= matrix[0][1]
        c= matrix[1][0]
        d= matrix[1][1]
        if b == 0:
            b = 0.0000001
        if c == 0:
            c = 0.0000001
        try:
            det = 1.0 / (a*d - b*c)

            new_matrix[0][0] = det * d 
            new_matrix[0][1] = det * -b
            new_matrix[1][0] = det * -c
            new_matrix[1][1] = det * a
            return new_matrix
        except:
            print 'Matrix can not be inverted\n', matrix

 
def Cholesky(A, ztol= 1.0e-5):
    # Forward step for symmetric triangular t.
    nrows = len(A)
    t = zero(nrows, nrows)
    for i in range(nrows):
        S = sum([( t[k][i] )**2 for k in range(i)])
        d = A[i][i] -S
        if abs(d) < ztol:
           t[i][i] = 0.0
        else: 
           if d < 0.0:
              print A
              raise ValueError, "Matrix not positive-definite"
           t[i][i] = math.sqrt(d)
        for j in range(i+1, nrows):
           S = sum([t[k][i] * t[k][j] for k in range(i)])
           if abs(S) < ztol:
              S = 0.0
           t[i][j] = (A[i][j] - S)/t[i][i]
    return(t)


        
def subtract(matrix1,matrix2):
    if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
        print 'Matrices must be of same size for subtraction'
        print matrix1,matrix2
        raise ValueError
    else:
        new_matrix = zero(len(matrix1), len(matrix1[0]))
        for i in range(len(matrix1)):
            for j in range(len(matrix1[0])):
                new_matrix[i][j] = matrix1[i][j] - matrix2[i][j]
        return new_matrix

def plus(matrix1,matrix2):
    if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
        print 'Matrices must be of same size for addition'
        print matrix1,matrix2
        raise ValueError
    else:
        new_matrix = zero(len(matrix1), len(matrix1[0]))
        for i in range(len(matrix1)):
            for j in range(len(matrix1[0])):
                new_matrix[i][j] = matrix1[i][j] + matrix2[i][j]
        return new_matrix
    
def mult(matrix1,matrix2):
    # Matrix multiplication
    if len(matrix1[0]) != len(matrix2):
        # Check matrix dimensions
        print 'Matrices must be m*n and n*p to multiply!'
    else:
        # Multiply if correct dimensions
        new_matrix = zero(len(matrix1),len(matrix2[0]))
        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                for k in range(len(matrix2)):
                    new_matrix[i][j] += matrix1[i][k]*matrix2[k][j]
        return new_matrix
 
def time_mult(matrix1,matrix2):
    # Clock the time matrix multiplication takes
    start = clock()
    new_matrix = mult(matrix1,matrix2)
    end = clock()
    print 'Multiplication took ',end-start,' seconds'
 
