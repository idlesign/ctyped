#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>


int buggy1() {
    return 777;
}


int buggy2() {
    return 888;
}


int with_errno() {
    errno = ENOENT;
    return 333;
}


int f_noprefix_1() {
    return -10;
}


int f_prefix_one_func_1() {
    return 1;
}


int f_prefix_one_func_2() {
    return 2;
}


int f_prefix_one_prefix_two_func_3() {
    return 3;
}


int f_prefix_one_get_prober() {
    srand(time(NULL));
    return rand();
}


int f_prefix_one_probe_add_one(int val) {
    return val + 1;
}


int f_prefix_one_probe_add_two(int val) {
    return val + 2;
}

const char * f_prefix_one_char_p(char* val) {
    char prefix[] = "hereyouare: ";
    char *out = malloc(sizeof(char) * (strlen(prefix) + strlen(val) + 1 ) );
    strcpy(out, prefix);
    strcat(out, val);
    return out;
}