#include <iostream>
#include <string>
#include <vector>

extern "C" {
    // This function takes a list of strings (rows) and joins them 
    // into one giant buffer in raw C++ speed.
    const char* fast_join_rows(const char** rows, int height) {
        static std::string buffer;
        buffer.clear();
        // We reserve memory up front to avoid "Re-allocation" lag
        buffer.reserve(height * 2000); 

        for (int i = 0; i < height; ++i) {
            buffer += rows[i];
        }
        return buffer.c_str();
    }
}

// opt.cpp
#include <vector>
#include <cstring>

extern "C" {

// Merge static_lines + ui_lines into prev_rows (in-place update)
// Only update rows that actually changed
// static_lines, ui_lines, prev_rows: arrays of C strings
// count: number of rows
void merge_rows(const char** static_lines, const char** ui_lines, char** prev_rows, int count) {
    for (int i = 0; i < count; ++i) {
        const char* s = static_lines[i];
        const char* u = ui_lines[i];

        const char* target = (!u || u[0] == '\0') ? s : u;

        if (!prev_rows[i] || strcmp(prev_rows[i], target) != 0) {
            size_t len = strlen(target);
            if (!prev_rows[i]) prev_rows[i] = new char[len + 1];
            else prev_rows[i] = (char*)realloc(prev_rows[i], len + 1);
            strcpy(prev_rows[i], target);
        }
    }
}

} // extern "C"