import os
import subprocess
import toml
import shutil
import glob
import stat

from distbuilder.errors import BuildError

_globalConfig: dict = None


def loadGlobalConfig(path: str):
    global _globalConfig
    tomlPath = os.path.abspath(path)
    with open(tomlPath, mode="r", encoding="utf-8") as fp:
        _globalConfig = toml.load(fp)

    # expand/abs path
    def _makeAbs(path):
        path = os.path.expandvars(path)
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.path.dirname(tomlPath), path))
        return path

    _globalConfig["directories"]["build"] = _makeAbs(_globalConfig["directories"]["build"])
    _globalConfig["directories"]["install"] = _makeAbs(_globalConfig["directories"]["install"])

    _globalConfig["directories"]["sources"] \
        = _globalConfig["directories"]\
        .get("sources", list())\
        + [(os.path.join(os.path.dirname(__file__), "../libs"))]

    _globalConfig["directories"]["sources"] = [_makeAbs(p) for p in _globalConfig["directories"]["sources"]]


def getGlobalConfig() -> dict:
    return _globalConfig.copy()


def getSourceDirectories() -> list:
    return _globalConfig["directories"]["sources"].copy()


def getInstallRootDirectory() -> str:
    return _globalConfig["directories"]["install"]


def getBuildRootDirectory() -> str:
    return _globalConfig["directories"]["build"]


def loadLibraryConfig():
    import inspect
    try:
        with open(os.path.join(os.path.dirname(inspect.stack()[1].filename), "config.toml"),
                  mode="r", encoding="utf-8") as fp:
            data = toml.load(fp)
        # (version, variant, config) に展開する
        ret = list()
        for version, variants in data.items():
            for variant, cfg in variants.items():
                ret.append((version, variant, cfg))
        return ret
    except Exception as e:
        raise BuildError(f"Failed to load library config. {e}")


def searchBuildFunctionAndPath(libraryName):
    print(f"getBuildFunction(): libraryName = {libraryName}")
    import importlib.util
    dirs = getSourceDirectories()
    for dirpath in dirs:
        filepath = os.path.join(dirpath, libraryName, "build.py")
        if os.path.exists(filepath):
            print(f"Found library script. {filepath}")
            break
    else:
        raise BuildError(f"Not found {libraryName}")

    spec = importlib.util.spec_from_file_location(libraryName, filepath)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return (builder.build, filepath)


def cleanCache():
    print("!!! Clean Cache !!!")
    if os.path.exists(getBuildRootDirectory()):
        shutil.rmtree(getBuildRootDirectory())
    print("-- OK.")


def recreateDirectory(rootPath: str):
    if os.path.exists(rootPath):
        for root, _, files in os.walk(rootPath):
            for filename in files:
                fullpath = os.path.join(root, filename)
                if not os.access(fullpath, os.W_OK):
                    os.chmod(fullpath, stat.S_IWRITE)
        shutil.rmtree(rootPath)
    os.makedirs(rootPath)


def getOrDownloadSource(url: str, libraryName: str, version: str) -> str:
    import urllib.error
    import urllib.request
    print(f"getOrDownloadSource(), {libraryName}@{version}, {url}")
    libraryBuildDirectory = os.path.join(
        getBuildRootDirectory(), libraryName, version)
    os.makedirs(libraryBuildDirectory, exist_ok=True)

    zipFilepath = os.path.join(libraryBuildDirectory, "src.zip")
    unzipDirpath = os.path.join(libraryBuildDirectory, "src")
    if not os.path.exists(zipFilepath):
        print(f"-- Downloading, destination = {zipFilepath}")
        try:
            urllib.request.urlretrieve(url, zipFilepath)
        except urllib.error.HTTPError as e:
            raise BuildError(f"Failed to download source. {e}")

        print(f"-- Unzipping, destination = {unzipDirpath}")
        recreateDirectory(unzipDirpath)
        shutil.unpack_archive(zipFilepath, unzipDirpath)

    else:
        print("-- Cached.")
    return unzipDirpath


def extractSource(zipFilepath: str, libraryName: str, version: str) -> str:
    print(f"extractSource(), {libraryName}@{version}, {zipFilepath}")
    libraryBuildDirectory = os.path.join(
        getBuildRootDirectory(), libraryName, version)
    os.makedirs(libraryBuildDirectory, exist_ok=True)

    unzipDirpath = os.path.join(libraryBuildDirectory, "src")
    if not os.path.exists(zipFilepath):
        raise BuildError(f"Source zip file is not existing. {zipFilepath}")

    print(f"-- Unzipping, destination = {unzipDirpath}")
    recreateDirectory(unzipDirpath)
    shutil.unpack_archive(zipFilepath, unzipDirpath)
    return unzipDirpath


def getBuildDirectory(libraryName: str, version: str, variant: str, buildConfig: str):
    print(f"getBuildDirectory(), {libraryName}@{version}/{variant}/{buildConfig}")
    buildDirectory = os.path.join(
        getBuildRootDirectory(), libraryName, version, "build", variant)
    if buildConfig:
        buildDirectory = os.path.join(buildDirectory, buildConfig)
    recreateDirectory(buildDirectory)
    os.makedirs(buildDirectory, exist_ok=True)
    print(f"-- build directory: {buildDirectory}")
    return buildDirectory


def _cmake(*args):
    args = [_globalConfig["cmake"]["path"]] + list(args)
    print("> {}".format(" ".join(args)))
    if subprocess.run(args).returncode != 0:
        raise BuildError("Failed to cmake.")


def cmakeConfigure(src: str, build: str, *args):
    """ Configure cmake.

    Args:
        src (str): Path to source.
        build (str): Path to build.
    """
    generator = _globalConfig["cmake"].get("generator")
    arch = _globalConfig["cmake"]["arch"]
    pargs = ["-A", arch]
    if generator is not None:
        pargs += ["-G", generator]
    pargs += list(args)
    pargs += ["-S", src, "-B", build]
    _cmake(*pargs)


def cmakeBuildAndInstall(build: str, config: str, install: str):
    """ Build by cmake.

    Args:
        build (str): Path to build.
        config (str): Release or Debug.
        install (str): Install path.
    """
    _cmake("--build", build, "--config", config)
    _cmake("--install", build, "--config", config, "--prefix", install)


def getInstallDirectory(libraryName: str, version: str, variant: str, buildConfig: str):
    print(f"getInstallDirectory(), {libraryName}@{version}/{variant}/{buildConfig}")
    installDirectory = os.path.join(getInstallRootDirectory(), libraryName, version, variant)
    if buildConfig:
        installDirectory = os.path.join(installDirectory, buildConfig)
    recreateDirectory(installDirectory)
    print(f"-- install directory: {installDirectory}")
    return installDirectory


# deprecated...
def searchLibrary(config: dict, libraryName: str, buildConfig: str):
    version, variant = config.get("deps", dict())[libraryName].split("/", 1)
    print(f"searchPackage(), {libraryName}@{version}/{variant}/{buildConfig}")
    installDirectory = os.path.join(getInstallRootDirectory(), libraryName, version, variant)
    if buildConfig:
        installDirectory = os.path.join(installDirectory, buildConfig)
    if not os.path.exists(installDirectory):
        raise BuildError(f"Library '{libraryName}' is not found.")
    # cmake を探す
    candidates = glob.glob(os.path.join(installDirectory, "**/*.cmake"), recursive=True)
    candidates = [(fp, os.path.basename(fp).lower()) for fp in candidates]
    for fp, fn in candidates:
        print(f"-- search: {fp}")
        if fn.endswith("config.cmake") and fn.startswith(libraryName.lower()):
            print(f"Library '{libraryName}' is found. {os.path.dirname(fp)}")
            return os.path.dirname(fp)
    raise BuildError(f"Library '{libraryName}' cmake file is not found.")


def insertCMakeExportCommands(libraryName: str, cmakeFilepath: str, *targetNames: str):
    lines = f"""
    install(TARGETS {' '.join(targetNames)} EXPORT {libraryName}-export)
    install(EXPORT {libraryName}-export FILE {libraryName}-config.cmake
        DESTINATION lib/cmake/{libraryName} NAMESPACE {libraryName}::)
    """

    with open(cmakeFilepath, mode="r", encoding="utf-8") as fp:
        content = fp.read()
    content += lines
    with open(cmakeFilepath, mode="w", encoding="utf-8") as fp:
        fp.write(content)


def applyPatch(patchFile: str, workingDirectory: str):
    import patch
    patchset = patch.fromfile(patchFile)
    patchset.apply(root=workingDirectory)
    print("Patch applied!")
