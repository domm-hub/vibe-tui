from setuptools import setup, Extension


fast_join_module = Extension(
    'vibe_tui.managers.join', 
    sources=['vibe_tui/managers/opt.cpp'], 
    extra_compile_args=['-O3', '-fPIC'], 
)

setup(
    ext_modules=[fast_join_module],
)