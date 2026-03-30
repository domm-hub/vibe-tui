import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class optional_build_ext(build_ext):
    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except Exception as e:
            print(f"************************************************************")
            print(f"WARNING: Failed to build C++ extension '{ext.name}'.")
            print(f"Error: {e}")
            print(f"Reverting to pure Python implementation.")
            print(f"************************************************************")

fast_join_module = Extension(
    'vibe_tui.managers.opt', 
    sources=['vibe_tui/managers/opt.cpp'], 
    extra_compile_args=['-O3', '-fPIC'], 
)

setup(
    ext_modules=[fast_join_module],
    cmdclass={'build_ext': optional_build_ext},
)