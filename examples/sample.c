#include <stdio.h>

int sum(int n) {
    int i;
    int s = 0;

    for (i = 0; i < n; ++i) {
        s += i;
    }

    return s;
}

int main(void) {
    int n = 5;
    int result = 0;
    int i;

    result = sum(n);

    if (result > 0) {
        printf("Sum up to %d is %d\n", n, result);
    }

    for (i = 0; i < n; ++i) {
        printf("i = %d\n", i);
    }

    return 0;
}

