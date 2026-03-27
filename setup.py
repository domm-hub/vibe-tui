from setuptools import setup, Extension

# Define the C++ extension
fast_join_module = Extension(
    'vibe_tui.managers.join', 
    # Match the filename in your tree: join.c++
    sources=['vibe_tui/managers/join.c++'], 
    extra_compile_args=['-O3', '-fPIC'], 
)

setup(
    ext_modules=[fast_join_module],
)