import os
from .preference import Preference
from .errors import BuildError


_libraryCache = dict()


def searchBuilderAndPath(libraryName):
    import importlib.util

    cached = _libraryCache.get(libraryName, None)
    if cached is not None:
        return cached

    print(f"[distbuilder] Find library: {libraryName}")
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
                        print(f"[distbuilder] -- Found library script. {p}")
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
                print(f"[distbuilder] -- Found library script. {filepath}")
                break
        else:
            raise BuildError(f"Not found {libraryName}")

    fullLibraryName = os.path.basename(os.path.dirname(filepath))
    spec = importlib.util.spec_from_file_location(fullLibraryName, filepath)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.Builder.__module__ = builder
    ret = (builder.Builder, filepath)
    _libraryCache[fullLibraryName] = ret
    _libraryCache[libraryName] = ret
    return ret
