#include "test.h"

/*
 * This is a block comment.
 */

int main() {
  // // [15] 支持if语句
  // ASSERT(3, ({ int x; if (0) x=2; else x=3; x; }));
  // ASSERT(3, ({ int x; if (1-1) x=2; else x=3; x; }));
  // ASSERT(2, ({ int x; if (1) x=2; else x=3; x; }));
  // ASSERT(2, ({ int x; if (2-1) x=2; else x=3; x; }));

  // // [16] 支持for语句
  // ASSERT(55, ({ int i=0; int j=0; for (i=0; i<=10; i=i+1) j=i+j; j; }));

  // // [17] 支持while语句
  // ASSERT(10, ({ int i=0; while(i<10) i=i+1; i; }));

  // // [13] 支持{...}
  // ASSERT(3, ({ 1; {2;} 3; }));
  // // [14] 支持空语句
  // ASSERT(5, ({ ;;; 5; }));

  // ASSERT(10, ({ int i=0; while(i<10) i=i+1; i; }));
  // ASSERT(55, ({ int i=0; int j=0; while(i<=10) {j=i+j; i=i+1;} j; }));
  
  // // [48] 支持 , 运算符
  // ASSERT(3, (1,2,3));
  // ASSERT(5, ({ int i=2, j=3; (i=5,j)=6; i; }));
  // ASSERT(6, ({ int i=2, j=3; (i=5,j)=6; j; }));

  // // [76] 支持循环域内定义局部变量
  // ASSERT(55, ({ int j=0; for (int i=0; i<=10; i=i+1) j=j+i; j; }));
  // ASSERT(3, ({ int i=3; int j=0; for (int i=0; i<=10; i=i+1) j=j+i; i; }));
  
  // // [85] 支持 &&和 ||
  // ASSERT(1, 0||1);
  // ASSERT(1, 0||(2-2)||5);
  // ASSERT(0, 0||0);
  // ASSERT(0, 0||(2-2));

  // ASSERT(0, 0&&1);
  // ASSERT(0, (2-2)&&5);
  // ASSERT(1, 1&&5);

  // // [89] 支持goto和标签语句
  // ASSERT(3, ({ int i=0; goto a; a: i++; b: i++; c: i++; i; }));
  // ASSERT(2, ({ int i=0; goto e; d: i++; e: i++; f: i++; i; }));
  // ASSERT(1, ({ int i=0; goto i; g: i++; h: i++; i: i++; i; }));

  // // [90] 解决typedef和标签之间的冲突
  // ASSERT(1, ({ typedef int foo; goto foo; foo:; 1; }));

  // // [91] 支持break语句
  // ASSERT(3, ({ int i=0; for(;i<10;i++) { if (i == 3) break; } i; }));
  // ASSERT(4, ({ int i=0; while (1) { if (i++ == 3) break; } i; }));
  // ASSERT(3, ({ int i=0; for(;i<10;i++) { for (;;) break; if (i == 3) break; } i; }));
  // ASSERT(4, ({ int i=0; while (1) { while(1) break; if (i++ == 3) break; } i; }));

  // // [92] 支持continue语句
  // ASSERT(10, ({ int i=0; int j=0; for (;i<10;i++) { if (i>5) continue; j++; } i; }));
  // ASSERT(6, ({ int i=0; int j=0; for (;i<10;i++) { if (i>5) continue; j++; } j; }));
  // ASSERT(10, ({ int i=0; int j=0; for(;!i;) { for (;j!=10;j++) continue; break; } j; }));
  // ASSERT(11, ({ int i=0; int j=0; while (i++<10) { if (i>5) continue; j++; } i; }));
  // ASSERT(5, ({ int i=0; int j=0; while (i++<10) { if (i>5) continue; j++; } j; }));
  // ASSERT(11, ({ int i=0; int j=0; while(!i) { while (j++!=10) continue; break; } j; }));

  // // [93] 支持switch和case
  // ASSERT(5, ({ int i=0; switch(0) { case 0:i=5;break; case 1:i=6;break; case 2:i=7;break; } i; }));
  // ASSERT(6, ({ int i=0; switch(1) { case 0:i=5;break; case 1:i=6;break; case 2:i=7;break; } i; }));
  // ASSERT(7, ({ int i=0; switch(2) { case 0:i=5;break; case 1:i=6;break; case 2:i=7;break; } i; }));
  // ASSERT(0, ({ int i=0; switch(3) { case 0:i=5;break; case 1:i=6;break; case 2:i=7;break; } i; }));
  // ASSERT(5, ({ int i=0; switch(0) { case 0:i=5;break; default:i=7; } i; }));
  // ASSERT(7, ({ int i=0; switch(1) { case 0:i=5;break; default:i=7; } i; }));
  // ASSERT(2, ({ int i=0; switch(1) { case 0: 0; case 1: 0; case 2: 0; i=2; } i; }));
  // ASSERT(0, ({ int i=0; switch(3) { case 0: 0; case 1: 0; case 2: 0; i=2; } i; }));

  //  这个测试有问题16个f能通过测试，但是8个f通不过测试
  ASSERT(3, ({ int i=0; switch(-1) { case 0xffffffff: i=3; break; } i; }));

  printf("OK\n");
  return 0;
}