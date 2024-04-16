#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

//Provide an interface to test for any cipher the diffusion of it limited for 64-bit state


//define the structure for keeping the proba for each output bit proba to flip

//at line i colomne j matrix_proba[i][j] correspond to the proba that:
//if the input bit i flip then the output bit j flip
typedef struct matrix{
  
  double** proba;
  int size;
  
}matrix;

//initialize the structure 
struct matrix* init_matrix(int size, struct matrix* m);

//free the structure
void free_matrix(struct matrix*);

//print the structure
void print_matrix(struct matrix* m);


//for any round function f taking an at moste 64-bit input, compute for the specify nbr of round the matrix for the size_sample number of input for state biger than 64-bit
struct matrix* test_dif_big(int nbr_round,int size,int* f(int*,int), int* input_encode(int*), int size_sample);


//analyze the matrix obtain as result of the test_dif 

//compute the min  avalanche dependence
double min_avalanche_dependence(struct matrix* m,int size_sample);

//compute the min avalanche weight
double min_avalanche_weight(struct matrix* m,int size_sample);

//compute the min avalanche entropy
double min_avalanche_entropy(struct matrix* m,int size_sample);

