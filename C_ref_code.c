#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define SIZE 257

// LoLaP round function

void LoLaP_round(uint* input,
	   uint* output, int r){


  uint* tmp = (uint*)malloc(SIZE*sizeof(uint));
  for(int i=0; i<SIZE; i++){
    tmp[i] = 0;
  }
  
  // bit shuffle layer

  for(int i=0;i<SIZE;i++){
    tmp[i] = input[(i*121) % SIZE];
  }

  // mixing layer
  for(int i=0;i<SIZE;i++){
    output[i] = tmp[i] ^ tmp[(i+3) % SIZE] ^ tmp[(i+10) % SIZE];
  }

  for(int i=0;i<SIZE;i++){
    tmp[i] = output[i];
  }
  
  // iota layer
  if(r == 1 || r == 3 || r == 4 || r == 7 || r == 8){
  	tmp[0] = tmp[0] ^ 1;
  }

  // chi layer
  for(int i=0;i<SIZE;i++){
    output[i] = tmp[i] ^ ((tmp[(i+1) % SIZE] ^ (uint)1) & tmp[(i+2) % SIZE]);
  }

  free(tmp); 
}



// LoLaP Permutation
void LoLaP(unsigned int* input,
	   unsigned int* output,
	   int rounds,
	   FILE *f){
  
  unsigned int* tmp = malloc(sizeof(unsigned int)*SIZE);
  
  unsigned int* tmp_input = malloc(sizeof(unsigned int)*SIZE);
  
  for(int i=0;i<SIZE;i++){
    tmp[i] = input[i];
    tmp_input[i] = input[i];
  }
  
  //apply the 8 round of the permutation
  for(int i=1; i<=rounds; i++){
    
    LoLaP_round(tmp, output,i);
    
    fprintf(f,"\nLola round %d: ",i); 
     for(int j=0; j<SIZE; j++){ 
      fprintf(f,"%d", output[j]); 
     }
     
    for(int j=0; j<SIZE; j++){
      tmp[j] = output[j];
    }
  }
  
  //add the input to the output of the permutation
  for(int i=0;i<SIZE;i++)
    output[i] ^= tmp_input[i];

  free(tmp);
  free(tmp_input);
  
}

// encode the 64-bit input into a 128-bit output
void encode(uint* input,
	    uint* output){

  for(int i=0;i<64;i+=2){
    uint enc = input[i]+(input[i+1]*2);
    output[i] = (enc==0)?1:0;
    output[i+32] = (enc==1)?1:0;
    output[i+64] = (enc==2)?1:0;
    output[i+96] = (enc==3)?1:0;
  }
  
}


// encode the 64-bit input into a 128-bit output
void encode_test(unsigned int* input,
		 unsigned int* output,
		 FILE *f,
		 int squeeze){
  
  
  unsigned int* v0 = (unsigned int*)malloc(32*sizeof(unsigned int));
  for(int i=0; i<32; i++){
    v0[i] = 0;
  }
  
  unsigned int* v1 = (unsigned int*)malloc(32*sizeof(unsigned int));
  for(int i=0; i<32; i++){
    v1[i] = 0;
  }
  
  unsigned int* v2 = (unsigned int*)malloc(32*sizeof(unsigned int));
  for(int i=0; i<32; i++){
    v2[i] = 0;
  }
  
  unsigned int* v3 = (unsigned int*)malloc(32*sizeof(unsigned int));
  for(int i=0; i<32; i++){
    v3[i] = 0;
  }
  for(int i=0;i<32;i+=1){
    //printf("%d", input[2*i]);
    v0[i] = (input[2*i]==0 & input[2*i+1]==0)?1:0; //((!input[2*i])&(!input[2*i+1]));
    v1[i] = (input[2*i]==0 & input[2*i+1]==1)?1:0; //((input[2*i])&(!input[2*i+1])); 
    v2[i] = (input[2*i]==1 & input[2*i+1]==0)?1:0; //((!input[2*i])&(input[2*i+1]));
    v3[i] = (input[2*i]==1 & input[2*i+1]==1)?1:0; //(input[2*i])&(input[2*i+1]));
  }
  
  fprintf(f,"\nOther generated parts of D-0-31 - v0: "); 
  for(int j=0; j<32; j++){ 
    fprintf(f,"%d", v0[j]); 
  }
  fprintf(f,"\nOther generated parts of D-32-63 - v1: "); 
  for(int j=0; j<32; j++){ 
    fprintf(f,"%d", v1[j]); 
  }
  fprintf(f,"\nOther generated parts of D-64-95 -v2: "); 
  for(int j=0; j<32; j++){ 
    fprintf(f,"%d", v2[j]); 
  }
  fprintf(f,"\nOther generated parts of D-96-128 - v3: "); 
  for(int j=0; j<32; j++){ 
    fprintf(f,"%d", v3[j]); 
  }
  
  //unsigned int* encoded_input = (unsigned int*)malloc(SIZE*sizeof(unsigned int));
  for(int i=0; i<32; i++){
    output[i] = v0[i];
  }

  for(int i=0; i<32; i++){
    output[32+i] = v1[i];
  }
  for(int i=0; i<32; i++){
    output[64+i] = v2[i];
  }

  for(int i=0; i<32; i++){
    output[96+i] = v3[i];
  }

  output[256] = squeeze;

  fprintf(f,"\nGeneratedDin\n"); 
  for(int j=0; j<SIZE; j++){ 
    fprintf(f,"%d", output[j]); 
  } 
   
}



// On round construction
void Constr(uint* state,
	    uint* D,
	    uint* Key,
	    int init,
	    int squeeze,
	    uint* output,
	    FILE *f){

  //temporary input use to start the value of the state in case the state should not be update after processing the data
  uint* input = (uint*)malloc(SIZE*sizeof(uint));

  for(int i=0; i<SIZE; i++)
    input[i] = state[i];
  
  // if init then initialize the state with the key and then apply the permutation with an empty diversifyer
  if(init == 1){
    for(int i=0; i<SIZE; i++){
      input[i] = Key[i];
    }

    //otherwise apply the permutation with the diversifyer encoded
  }else{

    uint* encoded_input = (uint*)malloc(SIZE*sizeof(uint));
    
    for(int i=0; i<SIZE; i++)
      encoded_input[i] = 0;
        
    encode_test(D, encoded_input,f,squeeze);
    
    for(int i=0; i<SIZE; i++){
      input[i] = input[i] ^ encoded_input[i];
    }

    free(encoded_input);
  }
  
  //if squeeze==1 then apply the permutation and output the result without updating the state
  if(squeeze == 1){
    LoLaP(input, output, 8,f);
  }
  //otherwise apply the permutation and update the state
  else{
    LoLaP(input, state, 8,f);
  }
}

int main(){

  //initialize the random seed
  //srand(time(NULL));

  //generate some test vectors for testing
  uint* state = (uint*)malloc(SIZE*sizeof(uint));
  uint* D0 = (uint*)malloc(64*sizeof(uint));
  uint* D1 = (uint*)malloc(64*sizeof(uint));
  uint* D2 = (uint*)malloc(64*sizeof(uint));
  uint* D3 = (uint*)malloc(64*sizeof(uint));
  uint* Key = (uint*)malloc(SIZE*sizeof(uint));
  uint* output = (uint*)malloc(SIZE*sizeof(uint));

  uint* input = (uint*)malloc(SIZE*sizeof(uint));
  
  int nbr_of_tests = 1;

  //generate random test vectors

  //open file for writing
  FILE *f = fopen("test_vectors.txt", "w");
  if (f == NULL)
    {
      printf("Error opening file!\n");
      exit(1);
    }

  for(int j=0;j<nbr_of_tests;j++){
    
    for(int i=0; i<SIZE; i++){
      state[i] = 0;
      Key[i] = rand() % 2;
      input[i] = 0;
    }

    for(int i=0; i<64; i++){
      D0[i] = rand() % 2;
      D1[i] = rand() % 2;
      D2[i] = rand() % 2;
      D3[i] = rand() % 2;
    }


    fprintf(f,"test vector nbr %d\n",j);
    //write the Key in binary
    fprintf(f,"Key: ");
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", Key[i]);
    }
    fprintf(f, "\n");

    //write the diversifyer in binary
    fprintf(f,"D0: ");
    for(int i=0; i<64; i++){
      fprintf(f, "%d", D0[i]);
    }
    fprintf(f, "\n");
    fprintf(f,"D1: ");
    for(int i=0; i<64; i++){
      fprintf(f, "%d", D1[i]);
    }
    fprintf(f, "\n");
    fprintf(f,"D2: ");
    for(int i=0; i<64; i++){
      fprintf(f, "%d", D2[i]);
    }
    fprintf(f, "\n");
    fprintf(f,"D3: ");
    for(int i=0; i<64; i++){
      fprintf(f, "%d", D3[i]);
    }
    fprintf(f, "\n");

    
    //initialization of the state with the key
    Constr(state, NULL, Key, 1, 0, NULL,f);
    
    fprintf(f,"\nState after initialization: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", state[i]); 
    }
    fprintf(f, "\n");
    //absorbing phase

    Constr(state, D0, NULL, 0, 0, NULL,f);

    fprintf(f,"\nState after processing D0: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", state[i]); 
    }
    fprintf(f, "\n");

    Constr(state, D1, NULL, 0, 0, NULL,f);

    fprintf(f,"\nState after processing D1: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", state[i]); 
    }
    fprintf(f, "\n");
    
    //squezzing phase


    Constr(state, D2, NULL, 0, 1, output,f);
    fprintf(f,"\nState after processing D2: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", state[i]); 
    }
    fprintf(f, "\n");
    
    fprintf(f,"output after processing D2: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", output[i]); 
    }
    fprintf(f, "\n");


    Constr(state, D3, NULL, 0, 1, output,f);

    fprintf(f,"\nState after processing D3: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", state[i]); 
    }
    fprintf(f, "\n");
    fprintf(f,"output after processing D3: "); 
    for(int i=0; i<SIZE; i++){
      fprintf(f, "%d", output[i]); 
    }
    fprintf(f, "\n");
    
  }

  fclose(f);
  free(state);
  free(D0);
  free(D1);
  free(D2);
  free(D3);
  free(Key);
  free(output);
  free(input);
}
