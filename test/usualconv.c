#include "test.h"

int main() {
  // [68] 实现常规算术转换
  // ASSERT((long)-5, -10 + (long)5);
  // ASSERT((long)-15, -10 - (long)5);
  // ASSERT((long)-50, -10 * (long)5);
  // ASSERT((long)-2, -10 / (long)5);

  // ASSERT(1, -2 < (long)-1);
  // ASSERT(1, -2 <= (long)-1);
  // ASSERT(0, -2 > (long)-1);
  // ASSERT(0, -2 >= (long)-1);

  // ASSERT(1, (long)-2 < -1);
  // ASSERT(1, (long)-2 <= -1);
  // ASSERT(0, (long)-2 > -1);
  // ASSERT(0, (long)-2 >= -1);

  // ASSERT(0, 2147483647 + 2147483647 + 2);
  // ASSERT((long)-1, ({ long x; x=-1; x; }));

  ASSERT(1, ({ char x[3]; x[0]=0; x[1]=1; x[2]=2; char *y=x+1; y[0]; }));
  // ASSERT(0, ({ char x[3]; x[0]=0; x[1]=1; x[2]=2; char *y=x+1; y[-1]; }));
  // ASSERT(5, ({ struct t {char a;} x, y; x.a=5; y=x; y.a; }));

  printf("OK\n");
  return 0;
}