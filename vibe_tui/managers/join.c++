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