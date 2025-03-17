import os
from .preference import Preference
from .errors import BuildError


def searchBuilderAndPath(libraryName):
    import importlib.util

    filepath = None
    if "." not in libraryName:
        filepaths = list()
        for dirpath in Preference.get().sourceDirectories:
            for dirname in os.listdir(dirpath):
                if dirname.startswith("_"):
                    continue
                if dirname.split(".", 1)[1] == libraryName:
                    p = os.path.join(dirpath, dirname, "build.py")
                    if os.path.exists(p):
                        print(f"-- Found library script. {p}")
                        filepaths.append(p)
        if len(filepaths) == 0:
            raise BuildError(f"Not found {libraryName}")
        elif len(filepaths) >= 2:
            raise BuildError("library name conflict.")
        filepath = filepaths[0]
    else:
        for dirpath in Preference.get().sourceDirectories:
            filepath = os.path.join(dirpath, libraryName, "build.py")
            if os.path.exists(filepath):
                print(f"Found library script. {filepath}")
                break
        else:
            raise BuildError(f"Not found {libraryName}")

    libraryName = os.path.basename(os.path.dirname(filepath))
    print(f"library directory is found. {libraryName}, {filepath}")
    spec = importlib.util.spec_from_file_location(libraryName, filepath)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return (builder.Builder, filepath)
