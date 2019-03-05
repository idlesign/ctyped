#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>
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


void f_prefix_one_byref_int(int * val) {
    *val = 33;
}


bool f_prefix_one_bool_to_bool(bool val) {
    return !val;
}


float f_prefix_one_float_to_float(float val) {
    return val;
}


typedef int (*callback) (int num);


int f_prefix_one_backcaller(callback hook) {
    return hook(33);
}


uint8_t f_prefix_one_uint8_add(uint8_t val) {
    return val + 1;
}

const char * f_prefix_one_char_p(char* val) {
    char prefix[] = "hereyouare: ";
    char *out = malloc(sizeof(char) * (strlen(prefix) + strlen(val) + 1 ));
    strcpy(out, prefix);
    strcat(out, val);
    return out;
}


const wchar_t * f_prefix_one_wchar_p(wchar_t* val) {
    setlocale(LC_ALL, "en_US.utf8");

    wchar_t prefix[] = L"вот: ";
    wchar_t *out = malloc(sizeof(wchar_t) * (wcslen(prefix) + wcslen(val) + 1 ));

    wcscpy(out, prefix);
    wcscat(out, val);

    return out;
}
