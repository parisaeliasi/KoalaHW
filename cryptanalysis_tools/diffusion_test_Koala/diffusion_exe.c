#include "diffusion_test.h"
#include "usefull/function_binary.h"
#include <omp.h>

#define one(x,i) ((x>>i)&1)

#define SIZE 257
#define THREADS_NBR 16

typedef uint64_t (*round_function)(uint64_t);

//cycling shift modulo size : state<<shift modulo size
uint64_t shifted(uint64_t state,
	    int shift,
	    int size){

  uint64_t mask = ((uint64_t)1<<size-shift) - 1;
  uint64_t output = (state<<size-shift) | ((state>>(shift)) & mask);
  
  return output & (((uint64_t)1<<size)-1);
}


int* identity(int* input){
  return input;
}


//performe the input encoding from 64 to 128 with a degree 2 function
int* input_encoding(int* input){
  
  int* output = malloc(sizeof(int)*SIZE);

  for(int i=0;i<SIZE;i++)
    output[i] = 0;
  
  for(int i = 0; i < 32; i++){
    output[i] = (input[2*i] ^ 1) & (input[(2*i)+1] ^ 1);
    output[i+32] = (input[2*i] ^ 1) & input[(2*i)+1];
    output[i+64] = input[2*i] & (input[(2*i)+1] ^ 1);
    output[i+96] = input[2*i] & input[(2*i)+1];
  }

  free(input);
  
  return output;
}

//round function of Koala
int* enc(int* input,
	 int round_nbr){
  
  int* output = malloc(sizeof(int)*SIZE);

  for(int i=0;i<SIZE;i++)
    output[i] = 0;
  
  
  for(int i = 0; i < SIZE; i++)
    output[i] = input[(i*121)%257];
  
  for(int i = 0; i < SIZE; i++)
    input[i] = output[i] ^ output[(257+i-3)%257] ^ output[(257+i-10)%257];

  if(round_nbr==1 || round_nbr==3 || round_nbr==4 || round_nbr==7)
    input[0] ^= 1;
    
  for(int i = 0; i < SIZE; i++)
    output[i] = input[i] ^ input[(i+2)%257] ^ (input[(i+2)%257] & input[(i+1)%257]);

  free(input);
  
  return output;
}

//round function for Subterranean
int* enc_Sub(int* input,
	     int round_nbr){
  
  int* output = malloc(sizeof(int)*SIZE);

  for(int i=0;i<SIZE;i++)
    output[i] = 0;

  for(int i = 0; i < SIZE; i++)
    output[i] = input[i] ^ input[(i+2)%257] ^ (input[(i+2)%257] & input[(i+1)%257]);

  output[0] ^= 1;
  
  for(int i = 0; i < SIZE; i++)
    input[i] = output[i] ^ output[(257+i-3)%257] ^ output[(257+i-8)%257];

  for(int i = 0; i < SIZE; i++)
    output[i] = input[(i*12)%257];
  
    
  free(input);
  
  return output;
}
	
//test diffusion for a specific number of round of Koala
void test_diffusion_Koala(int nbr_round,
		    int size_sample){
  
  
  struct matrix* m = test_dif_big(nbr_round,
				  SIZE,
				  enc,
				  input_encoding,
				  size_sample);
	      
  double cur_dep = min_avalanche_dependence(m,size_sample);
  double cur_weight = min_avalanche_weight(m,size_sample);
  double cur_ent = min_avalanche_entropy(m,size_sample);

  printf("the min avalanche dependence is %f, the min avalanche weight is %f, the min avalanche entropy is %f for %d round \n",cur_dep,cur_weight,cur_ent,nbr_round);

  free_matrix(m);

}

//test diffusion for a specific number of round of Subterranean
void test_diffusion_Sub(int nbr_round,
		    int size_sample){
  
  
  struct matrix* m = test_dif_big(nbr_round,
				  SIZE,
				  enc_Sub,
				  identity,
				  size_sample);
	      
  double cur_dep = min_avalanche_dependence(m,size_sample);
  double cur_weight = min_avalanche_weight(m,size_sample);
  double cur_ent = min_avalanche_entropy(m,size_sample);

  printf("the min avalanche dependence is %f, the min avalanche weight is %f, the min avalanche entropy is %f for %d round \n",cur_dep,cur_weight,cur_ent,nbr_round);

  free_matrix(m);

}

//test for a set of number of round start from nbr_round_start to nbr_round_end the rotation value for Koala 
void test_full_round_Koala(int size_sample,
		     int nbr_round_start,
		     int nbr_round_end){

  for(int i=nbr_round_start;i<nbr_round_end;i++)
    test_diffusion_Koala(i,size_sample);

}


//test for a set of number of round start from nbr_round_start to nbr_round_end the rotation value for Subterranean 
void test_full_round_Sub(int size_sample,
		     int nbr_round_start,
		     int nbr_round_end){

  for(int i=nbr_round_start;i<nbr_round_end;i++)
    test_diffusion_Sub(i,size_sample);

}

int main(){

  int nbr_round = 8;
  
  int nbr_sample = 1000000;

  printf("test for size %d, for %d round\n",SIZE,nbr_round);

  test_full_round_Koala(nbr_sample,1,nbr_round);
  
  return 1;
}
