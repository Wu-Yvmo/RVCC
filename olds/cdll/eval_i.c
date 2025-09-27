#include <stdio.h>

void hello() {
    printf("hello world\n");
}

long eval_hex_i64(const char *content) {
    // 跳过0x
    content += 2;
    long v = 0;
    // 如何判断这个值可以被32位存储呢？
    while (content[0] != '\0') {
        printf("operate\n");
        // 对16进制数进行解析
        if (content[0] >= '0' && content[0] <= '9') {
            v = v * 16 + content[0] - '0';
        } else if (content[0] >= 'a' && content[0] <= 'f') {
            v = v * 16 + content[0] - 'a' + 10;
        } else if (content[0] >= 'A' && content[0] <= 'F') {
            v = v * 16 + content[0] - 'A' + 10;
        }
        content += 1;
    }
    // 判断我们解析出来的值可以被32位存储：
    if (v >> 32) {
        // 值不能被32位存储
        return v>>32;
    }
    // 值可以被32位存储 把高位的32位截断
    return (v<<32)>>32;
}

