from cx_Freeze import setup, Executable

base = None

executables = [Executable("app.py", base=base, target_name="app.exe")]

setup(
    name="MyApp",
    version="0.1",
    description="My PyQt6 Application",
    executables=executables
)
