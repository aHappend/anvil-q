
#include <stdio.h>
#include <stdlib.h>
#include "oniguruma.h"
int main(int argc, char **argv) {
    OnigEncoding encoding = ONIG_ENCODING_UTF8;
    OnigRegex regex;
    OnigErrorInfo info;
    unsigned char diagnostic[ONIG_MAX_ERROR_MESSAGE_LEN];
    if (argc != 2 || onig_initialize(&encoding, 1) != ONIG_NORMAL) return 2;
    const unsigned char *pattern = (const unsigned char *)"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\\r\\n\\p{L}\\p{N}]?\\p{L}+|\\p{N}| ?[^\\s\\p{L}\\p{N}]+[\\r\\n]*|\\s*[\\r\\n]+|\\s+(?!\\S)|\\s+";
    int result = onig_new(&regex, pattern, pattern + 110,
                         ONIG_OPTION_NONE, encoding, ONIG_SYNTAX_DEFAULT, &info);
    if (result != ONIG_NORMAL) {
        onig_error_code_to_str(diagnostic, result, &info);
        fprintf(stderr, "ONIG_COMPILE %s\n", diagnostic);
        return 3;
    }
    FILE *input = fopen(argv[1], "r");
    if (!input) return 4;
    unsigned cases;
    if (fscanf(input, "%u", &cases) != 1 || cases == 0) return 5;
    OnigRegion *region = onig_region_new();
    for (unsigned item = 0; item < cases; ++item) {
        unsigned length;
        if (fscanf(input, "%u", &length) != 1 || length > 1048576) return 6;
        unsigned char *text = malloc(length + 1);
        if (!text) return 7;
        for (unsigned byte = 0; byte < length; ++byte) {
            unsigned value;
            if (fscanf(input, "%x", &value) != 1 || value > 255) return 8;
            text[byte] = (unsigned char)value;
        }
        int cursor = 0;
        unsigned spans = 0;
        while (cursor < (int)length) {
            result = onig_search(regex, text, text + length, text + cursor,
                                 text + length, region, ONIG_OPTION_NONE);
            if (result != cursor || region->beg[0] != cursor ||
                region->end[0] <= cursor || region->end[0] > (int)length) {
                fprintf(stderr, "ONIG_PROGRESS case=%u cursor=%d result=%d\n", item, cursor, result);
                return 9;
            }
            printf("SPAN %u %d %d\n", item, region->beg[0], region->end[0]);
            cursor = region->end[0];
            ++spans;
        }
        printf("CASE %u %u\n", item, spans);
        free(text);
    }
    char extra;
    if (fscanf(input, " %c", &extra) != EOF) return 10;
    fclose(input);
    onig_region_free(region, 1);
    onig_free(regex);
    onig_end();
    printf("ONIG_CASES %u\n", cases);
    return 0;
}
