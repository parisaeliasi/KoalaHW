
make: diffusion_exe.c
	gcc -c diffusion_test.c diffusion_test.h
	gcc -o diffusion_koala -fopenmp diffusion_exe.c diffusion_test.o -lm

clean:
	rm -r *.o 
