# Instrinsics
Compilers for C and C++, of Microsoft, Intel, and the GNU Compiler Collection (GCC) implement intrinsics that map directly to the x86 single instruction, multiple data (SIMD) instructions (MMX, Streaming SIMD Extensions (SSE), SSE2, SSE3, SSSE3, SSE4, AVX, AVX2, AVX512, FMA, ...). 

## Examples:

### Memory Geometry Processing

#### Motivation and Introduction
A motivating example is given in a [StackOverflow](https://stackoverflow.com/questions/44984724/whats-the-fastest-stride-3-gather-instruction-sequence) thread where in the original poster wants to go from a 3 stride array of structures ([AOS](https://en.wikipedia.org/wiki/AoS_and_SoA#Array_of_structures)) to a structure of arrays ([SOA](https://en.wikipedia.org/wiki/AoS_and_SoA#Structure_of_arrays)). Specifically, we want to go from:

$$ \text{vi32_t *SRC} = [R_{0}, G_{0}, B_{0}, R_{1}, G_{1}, B_{1}, ..., R_{n-1}, G_{n-1}, B_{n-1}]  $$

And want to obtain:

$$
\begin{align}
\text{YMM0} &= [R_0, R_1, R_2, R_3, R_4, R_5, R_6, R_7] \\
\text{YMM1} &= [G_0, G_1, G_2, G_3, G_4, G_5, G_6, G_7] \\
\text{YMM2} &= [B_0, B_1, B_2, B_3, B_4, B_5, B_6, B_7]
\end{align}
$$

or in memory as:

$$
\text{vi32_t SRC'}= [R_0, ..., R_n{n-1}, G_0, ...,G_{n-1}, B_0, ..., B_{n-1}]
$$

Stated another way, we want to do a $SxN$ transpose where the stride $S = 3$ and the SIMD width `N = 8`. Visually, in memory we perform the following operation.

```
+---------------+-------------+
|    Address    |    Memory   |
+---------------+-------------+      +----------------+---------------------------------+
| SRC + (0 * S) | R_0 G_0 B_0 |      |     Address    |              Memory             |
| SRC + (1 * S) | R_1 G_1 B_1 |      +----------------+---------------------------------+
| SRC + (2 * S) | R_2 G_2 B_2 |      | SRC` + (0 * N) | R_0 R_1 R_2 R_3 R_4 R_5 R_6 R_7 |
| SRC + (3 * S) | R_3 G_3 B_3 |---\  | SRC` + (1 * N) | G_0 G_1 G_2 G_3 G_4 G_5 G_6 G_7 |
| SRC + (4 * S) | R_4 G_4 B_4 |---/  | SRC` + (2 * N) | B_0 B_1 B_2 B_3 B_4 B_5 B_6 B_7 |
| SRC + (5 * S) | R_5 G_5 B_5 |      +----------------+---------------------------------+
| SRC + (6 * S) | R_6 G_6 B_6 |
| SRC + (7 * S) | R_7 G_7 B_7 |
+---------------+-------------+

```

#### *AOS and SOA: A digression*
It is easy to see why `SRC` is an array of structure with the following C code:

```
struct aos {
  int32_t R;
  int32_t G;
  int32_t B;
} aos_t;

aos_t *SRC[n];
```
While $SRC`$ would be give as
```
struct s_type {
  int32_t R[n];
  int32_t G[n];
  int32_t B[n];
} soa_t;

soa_t SRC`;
```

#### First Solution

The first solution linked to from the stack. Its taken from an Intel paper called [3D Vector Normalization Using 256-bit Intel Advanced Vector Extensions](https://www.intel.com/content/dam/develop/external/us/en/documents/normvec-181650.pdf). It is only 8 pages and worth a read. The solution presented there is as follows:

```
float *p;  // address of first vector
__m128 *m = (__m128*) p;
__m256 m03;
__m256 m14; 
__m256 m25; 
m03  = _mm256_castps128_ps256(m[0]); // load lower halves
m14  = _mm256_castps128_ps256(m[1]);
m25  = _mm256_castps128_ps256(m[2]);
m03  = _mm256_insertf128_ps(m03 ,m[3],1);  // load upper halves
m14  = _mm256_insertf128_ps(m14 ,m[4],1);
m25  = _mm256_insertf128_ps(m25 ,m[5],1);

__m256 xy = _mm256_shuffle_ps(m14, m25, _MM_SHUFFLE( 2,1,3,2)); // upper x's and y's 
__m256 yz = _mm256_shuffle_ps(m03, m14, _MM_SHUFFLE( 1,0,2,1)); // lower y's and z's
__m256 x  = _mm256_shuffle_ps(m03, xy , _MM_SHUFFLE( 2,0,3,0)); 
__m256 y  = _mm256_shuffle_ps(yz , xy , _MM_SHUFFLE( 3,1,2,0)); 
__m256 z  = _mm256_shuffle_ps(yz , m25, _MM_SHUFFLE( 3,0,3,1)); 
```
The first half is just packing the values into three `__mm256` vector registers. Another thing to point out is that the `_MM_SHUFFLE(args)` takes the arguments and and packs them into an 8 bit immediate value. Thus first call to `_MM_SHUFFLE(2,1,3,2);` yields `2<<6 | 1<<4 | 3<<2 | 2<<0 -->  0b10011110`.

First, lets just consider the layout of `m03, m14, & m25`

```
| Register | 255:224      | 223:192     | 191:160     | 159:128    | 127:96       | 95:64       | 63:32       | 31:0       |
|----------|--------------|-------------|-------------|------------|--------------|-------------|-------------|------------|
| m03      | m[3][127:96] | m[3][95:64] | m[3][63:32] | m[3][31:0] | m[0][127:96] | m[0][95:64] | m[0][63:32] | m[0][31:0] |
| m14      | m[4][127:96] | m[4][95:64] | m[4][63:32] | m[4][31:0] | m[1][127:96] | m[1][95:64] | m[1][63:32] | m[1][31:0] |
| m25      | m[5][127:96] | m[5][95:64] | m[5][63:32] | m[5][31:0] | m[2][127:96] | m[2][95:64] | m[2][63:32] | m[2][31:0] |
```
Where `m[i]` is 128 bits of data. With that in mind lets look at the shuffle instructions. We have five `_mm_shuffle_ps` instructions.

```
__m256 xy = _mm256_shuffle_ps(m14, m25, 0b10011110); // upper x's and y's 
__m256 yz = _mm256_shuffle_ps(m03, m14, 0b01001001); // lower y's and z's
__m256 x  = _mm256_shuffle_ps(m03, xy , 0b10001100); 
__m256 y  = _mm256_shuffle_ps(yz , xy , 0b11011000); 
__m256 z  = _mm256_shuffle_ps(yz , m25, 0b11001101); 
```
The description from the Intel Instrinsics Guide is: Shuffle single-precision (32-bit) floating-point elements in a using the control in imm8, and store the results in dst. In practive this means, for each 32bit word of the destination is populated by the word of source indicated by the 2bit value in the `imm8`. Lets step through them.

```
//------------- General form: type x = shuffle(a, b, imm8) := [ b_hi[imm8[7:6]] | b_hi[imm8[5:4]] | a_hi[imm8[3:2]] | a_hi[imm8[1:0] |  b_lo[imm8[7:6]] | b_lo[imm8[5:4]] | a_lo[imm8[3:2]] | a_lo[imm8[1:0]] ]
//                                              Bit ranges := [    255:224      |     223:192     |     191:160     |    159:128     |      127:96      |      95:64      |     63:32       |      31:0       ]
//                                           imm8 selector := [       3         |        2        |        1        |       0        |         3        |        2        |       1         |        0        ]
//                                                            [-----------------|-----------------|-----------------|----------------|------------------|-----------------|-----------------|-----------------]
__m256 xy = _mm256_shuffle_ps(m14, m25, 0b10011110); // xy := [  m25[223:192]   |  m25[191:160]   |  m14[255:224]   |  m14[223:192]  |    m25[ 95:64]   |   m25[ 63:32]    |   m14[127:96]   |   m14[95:64]   ]
__m256 yz = _mm256_shuffle_ps(m03, m14, 0b01001001); // yz := [  m14[191:160]   |  m14[159:128]   |  m03[223:192]   |  m03[191:160]  |    m14[ 63:32]   |   m14[ 31: 0]    |   m03[ 95:64]   |   m03[63:32]   ]
__m256 x  = _mm256_shuffle_ps(m03, xy , 0b10001100); // x  := [   xy[223:192]   |   xy[159:128]   |  m03[255:224]   |  m03[159:128]  |     xy[ 95:64]   |    xy[ 31: 0]    |   m03[127:96]   |   m03[31: 0]   ]
                                                     //     = [  m25[191:160]   |  m14[223:192]   |  m03[255:224]   |  m03[159:128]  |    m25[ 63:32]   |   m14[ 63:32]    |   m03[127:96]   |   m03[31: 0]   ]
__m256 y  = _mm256_shuffle_ps(yz , xy , 0b11011000); // y  := [   xy[255:224]   |   xy[191:128]   |   yz[223:192]   |   yz[159:128]  |     xy[127:96]   |    xy[ 63:32]    |    yz[ 95:64]   |    yz[31: 0]   ]
                                                     //     = [  m25[223:192]   |  m14[255:224]   |  m14[159:128]   |  m03[191:160]  |    m25[ 95:64]   |   m14[127:96]    |   m14[ 31: 0]   |   m03[63:32]   ]
__m256 z  = _mm256_shuffle_ps(yz , m25, 0b11001101); // z  := [  m25[255:224]   |  m25[159:128]   |   yz[255:224]   |   yz[191:160]  |    m25[127:96]   |   m25[ 31: 0]    |    yz[127:96]   |    yz[63:32]   ]
                                                     //     = [  m25[255:224]   |  m25[159:128]   |  m14[191:160]   |  m03[223:192]  |    m25[127:96]   |   m25[ 31: 0]    |   m14[63:32]    |   m03[ 95:64]  ] 
//------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------/
```

So we have the following 256 bit registers:
```
// x = [ m25[191:160] | m14[223:192] | m03[255:224] | m03[159:128] | m25[ 63:32] | m14[ 63:32] | m03[127:96] | m03[31: 0] ]
// y = [ m25[223:192] | m14[255:224] | m14[159:128] | m03[191:160] | m25[ 95:64] | m14[127:96] | m14[ 31: 0] | m03[63:32] ]
// z = [ m25[255:224] | m25[159:128] | m14[191:160] | m03[223:192] | m25[127:96] | m25[ 31: 0] | m14[ 63:32] | m03[95:64] ]
```

And doing substitution as in the inline comments we get:

```
x =  [5][ 63:32  | [4][95:64]  | [3][127:96] | [3][31: 0]  | [2][ 63:32] | [1][63:32] | [0][127:96] | [0][31: 0]
y =  [5][ 95:64] | [4][127:96] | [4][ 31:0]  | [3][63:32]  | [2][ 95:64] | [1]127:96] | [1][ 31:0]  | [0][63:32]
y =  [5][127:96] | [5][ 31:0]  | [4][ 63:32] | [3][95:64]  | [2][127:96] | [2][ 31:0] | [1][ 63:32] | [0][95:64]
```

If all went well, we align the original source and destination memory maps we can see the following desired transformation took place:
```
m:= [0][127:96] [0][95:64] [0][63:32] [0][31:0]
    [1][127:96] [1][95:64] [1][63:32] [1][31:0]
    [2][127:96] [2][95:64] [2][63:32] [2][31:0]
    [3][127:96] [3][95:64] [3][63:32] [3][31:0]
    [4][127:96] [4][95:64] [4][63:32] [4][31:0]
    [5][127:96] [5][95:64] [5][63:32] [5][31:0]
                                       
m03 := [3][127:96] [3][ 95:64] [3][ 63:32] [3][31: 0] [0][127:96] [0][95:64] [0][ 63:32] [0][31:0]
m14 := [4][127:96] [4][ 95:64] [4][ 63:32] [4][31: 0] [1][127:96] [1][95:64] [1][ 63:32] [1][31:0]
m25 := [5][127:96] [5][ 95:64] [5][ 63:32] [5][31: 0] [2][127:96] [2][95:64] [2][ 63:32] [2][31:0]

x := [5][ 63:32] [4][95:64]  [3][127:96] [3][31: 0] [2][ 63:32] [1][63:32] [0][127:96] [0][31: 0]
y := [5][ 95:64] [4][127:96] [4][ 31: 0] [3][63:32] [2][ 95:64] [1]127:96] [1][ 31: 0] [0][63:32]
z := [5][127:96] [5][ 31:0]  [4][ 63:32] [3][95:64] [2][127:96] [2][ 31:0] [1][ 63:32] [0][95:64]

```

But, unfortunately that is not quite correct. While doing the above by hand, I swapped around the indices for the original `m[i]` array. This lead to a reversed representation. The transformation is still the one we expect. However, the layout presented above is not how it would reside in memory. Using the code in the next subsection, we can see the correct representation as well as the one given above.

```
// Correct representation and layout in memory
m[0] := 00000000 00001111 00002222 00003333 
m[1] := 11110000 11111111 11112222 11113333 
m[2] := 22220000 22221111 22222222 22223333 
m[3] := 33330000 33331111 33332222 33333333 
m[4] := 44440000 44441111 44442222 44443333 
m[5] := 55550000 55551111 55552222 55553333 

m03  := 00000000 00001111 00002222 00003333 33330000 33331111 33332222 33333333 
m14  := 11110000 11111111 11112222 11113333 44440000 44441111 44442222 44443333 
m25  := 22220000 22221111 22222222 22223333 55550000 55551111 55552222 55553333 

x    := 00000000 00003333 11112222 22221111 33330000 33333333 44442222 55551111 
y    := 00001111 11110000 11113333 22222222 33331111 44440000 44443333 55552222 
z    := 00002222 11111111 22220000 22223333 33332222 44441111 55550000 55553333

// Reversed represenation and not the layout in memory
m[0] := 00003333 00002222 00001111 00000000
m[1] := 11113333 11112222 11111111 11110000
m[2] := 22223333 22222222 22221111 22220000
m[3] := 33333333 33332222 33331111 33330000
m[4] := 44443333 44442222 44441111 44440000
m[5] := 55553333 55552222 55551111 55550000

m03  := 33333333 33332222 33331111 33330000 00003333 00002222 00001111 00000000
m14  := 44443333 44442222 44441111 44440000 11113333 11112222 11111111 11110000
m25  := 55553333 55552222 55551111 55550000 22223333 22222222 22221111 22220000

x    := 55551111 44442222 33333333 33330000 22221111 11112222 00003333 00000000
y    := 55552222 44443333 44440000 33331111 22222222 11113333 11110000 00001111
z    := 55553333 55550000 44441111 33332222 22223333 22220000 11111111 00002222
```



##### Code

The following code can be used to demonstrate the above transformation.

```
// To compile on AMD Eypc
// gcc -march=core-avx2 -Wall shuffle.c -o shuffle

#include <stdio.h>
#include <immintrin.h>
#include <x86intrin.h>
#include <string.h>
#include <stdint.h>

void print_256b(__m256 var) 
{
      int64_t v64_val[4];
          memcpy(v64_val, &var, sizeof(v64_val));
              printf("%.16lx %.16lx %.16lx %.16lx\n",
                  v64_val[3],
                  v64_val[2],
                  v64_val[1],
                  v64_val[0]);
}

void print_128b(__m128 var) 
{
      int64_t v64_val[2];
          memcpy(v64_val, &var, sizeof(v64_val));
              printf("%.16lx %.16lx\n",
                  v64_val[1],
                  v64_val[0]);
}

int main(int argc, char ** argv) {

  // Set up initial values
  const int32_t m0[4]  = 
      { 0x00000000, 0x00001111, 0x00002222, 0x00003333};
  const int32_t m1[4]  = 
      { 0x11110000, 0x11111111, 0x11112222, 0x11113333 };
  const int32_t m2[4]  = 
      { 0x22220000, 0x22221111, 0x22222222, 0x22223333 };
  const int32_t m3[4]  = 
      { 0x33330000, 0x33331111, 0x33332222, 0x33333333 };
  const int32_t m4[4]  = 
      { 0x44440000, 0x44441111, 0x44442222, 0x44443333 };
  const int32_t m5[4]  = 
      { 0x55550000, 0x55551111, 0x55552222, 0x55553333 };

  // Store them in the soure array
  __m128 m[5] = { 0 };
  m[0] = (__m128) _mm_set_epi32(m0[3],m0[2],m0[1],m0[0]);
  m[1] = (__m128) _mm_set_epi32(m1[3],m1[2],m1[1],m1[0]);
  m[2] = (__m128) _mm_set_epi32(m2[3],m2[2],m2[1],m2[0]);
  m[3] = (__m128) _mm_set_epi32(m3[3],m3[2],m3[1],m3[0]);
  m[4] = (__m128) _mm_set_epi32(m4[3],m4[2],m4[1],m4[0]);
  m[5] = (__m128) _mm_set_epi32(m5[3],m5[2],m5[1],m5[0]);
  

  // Populate the shuffle registers
  __m256 m03;
  __m256 m14; 
  __m256 m25; 
  m03  = _mm256_castps128_ps256(m[0]); // load lower halves
  m14  = _mm256_castps128_ps256(m[1]);
  m25  = _mm256_castps128_ps256(m[2]);
  m03  = _mm256_insertf128_ps(m03 ,m[3],1);  // load upper halves
  m14  = _mm256_insertf128_ps(m14 ,m[4],1);
  m25  = _mm256_insertf128_ps(m25 ,m[5],1);
  
  // Shuffle
  __m256 xy = _mm256_shuffle_ps(m14, m25, _MM_SHUFFLE( 2,1,3,2)); // upper x's and y's 
  __m256 yz = _mm256_shuffle_ps(m03, m14, _MM_SHUFFLE( 1,0,2,1)); // lower y's and z's
  __m256 x  = _mm256_shuffle_ps(m03, xy , _MM_SHUFFLE( 2,0,3,0)); 
  __m256 y  = _mm256_shuffle_ps(yz , xy , _MM_SHUFFLE( 3,1,2,0)); 
  __m256 z  = _mm256_shuffle_ps(yz , m25, _MM_SHUFFLE( 3,0,3,1));
  
  //Print

  // This will print out little endian representation
  uint32_t *p;
  for (int i=0; i < 6; ++i) {
    p = &m[i]; printf("m[%d] := ", i);
    for (int j=0; j < 4; ++j ) { printf("%.8x ",p[j]); } printf("\n");
  } printf("\n");

  p = (uint32_t *) &m03[0]; printf("m03  := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");

  p = (uint32_t *) &m14[0]; printf("m14  := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");

  p = (uint32_t *) &m25[0]; printf("m25  := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");
  printf("\n");

  p = (uint32_t *) &x[0]; printf("x    := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");

  p = (uint32_t *) &y[0]; printf("y    := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");

  p = (uint32_t *) &z[0]; printf("z    := ");
  for(int i=0; i<8; ++i) { printf("%.8x ", p[i]); } printf("\n");

  // This will print out big endian representation
  for (int i=0; i < 6; i++) {
    print_128b(m[i]);
  } printf("\n");

  print_256b(m03);
  print_256b(m14);
  print_256b(m25);
  printf("\n");

  print_256b(x);
  print_256b(y);
  print_256b(z);
  printf("\n");
}

```




















## Resources
- [Intel Intrisics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=554,1474,511,502,529&cats=Swizzle)
- [x86 Instrinsics Cheatsheet](https://db.in.tum.de/~finis/x86-intrin-cheatsheet-v2.2.pdf?lang=en)
- -
