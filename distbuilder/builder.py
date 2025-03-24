import os
import shutil
import re
import subprocess
import hashlib
from typing import List, Union
from .errors import BuildError
from .preference import Preference
from .version import Version
from .option import Option
from .dependency import Dependency
from .global_options import GlobalOptions


_replaceRule = re.compile("[a-z0-9]([A-Z])")


def _toLabel(name: str):
    matchs = [m for m in _replaceRule.finditer(name)]
    for m in reversed(matchs):
        name = name[:m.span(1)[0]] + " " + name[m.span(1)[0]:]
    name = name[0].upper() + name[1:]
    return name


def _logTask(func):
    def wrapper(self, *args, **kwargs):
        self.log(f"{_toLabel(func.__name__)}")
        self._logIndent += 1
        ret = func(self, *args, **kwargs)
        self._logIndent -= 1
        return ret
    return wrapper


# , version: str, options: dict, globalOptions: dict


class BuilderBase:
    def __init__(self, version: Union[Version, str], depsConfValue: dict, globalOptions: GlobalOptions):
        self._libraryName = self.__class__.__module__
        self._logIndent = 0

        if isinstance(version, Version):
            self._version = version
        else:
            self._version = self.generateVersion(version)
        self._globalOptions = globalOptions

        self._depsConfValue = depsConfValue

        optionValues = depsConfValue.get(self._libraryName, dict(options={}))["options"]

        # オプション
        self._options = list()
        self._dependencies = list()
        for member in dir(self.__class__):
            if member.startswith("option_"):
                m = getattr(self.__class__, member)
                if isinstance(m, Option):
                    m._key = member[7:]
                    opt = m.copy()
                    if m._key in optionValues:
                        opt.setValue(optionValues[m._key])
                    setattr(self, member, opt)
                    self._options.append(opt)
            if member.startswith("dep_"):
                m = getattr(self.__class__, member)
                if isinstance(m, Dependency):
                    setattr(self, member, m)
                    self._dependencies.append(m)
        self._options.sort(key=lambda v: v.key)
        self._dependencies.sort(key=lambda v: v.libraryName)

        # hash
        self._hashOk = True
        hashStr = f"ln={self._libraryName}\n"
        hashStr += f"v={self._version}\n"
        hashStr += f"recipe={self.__class__.recipeVersion}\n"
        for opt in self._options:
            hashStr += f"o:{opt.key}={opt}\n"

        # hash dependencies
        for dep in self._dependencies:
            if not dep.isRequired(self):
                hashStr += f"dep:{dep.libraryName}=\n"
                continue

            if dep.libraryName not in depsConfValue:
                # 依存が決定していない
                self._hashOk = False
                hashStr += f"dep:{dep.libraryName}=<UNRESOLVED>\n"
            else:
                depConf = depsConfValue[dep.libraryName]
                depBuilderCls, depAvailableVersions, overrideOptions = dep.resolve(self)
                depReqVersion = depBuilderCls.generateVersion(depConf["version"])
                if depReqVersion not in depAvailableVersions:
                    raise BuildError("Version error.")
                for ovrdOptKey, ovrdOptValue in overrideOptions.items():
                    if depConf.get(ovrdOptKey, ovrdOptValue) != ovrdOptValue:
                        raise BuildError("Dependency Option Error")
                depBuilder = depBuilderCls(depReqVersion, depsConfValue, globalOptions)
                hashStr += f"dep:{dep.libraryName}={depBuilder.hash}\n"

        hashStr = hashStr.strip()
        self._hash = hashlib.md5(hashStr.encode()).hexdigest()
        self.log(f"-- Hash (Str): {hashStr}")
        self.log(f"-- HashOK? {self._hashOk}")
        if self._hashOk:
            self.log(f"-- Hash:{self._hash}")

    def prepare(self):
        # ディレクトリ作る
        if self._globalOptions.createDirectory:
            if self._globalOptions.cleanBuild:
                shutil.rmtree(self.buildDir)
            os.makedirs(self.buildDir, exist_ok=True)

            if os.path.exists(self.installDir):
                shutil.rmtree(self.installDir)
            os.makedirs(self.installDir, exist_ok=True)

    @property
    def libraryName(self) -> str:
        return self._libraryName

    @property
    def version(self) -> Version:
        return self._version

    @property
    def globalOptions(self) -> GlobalOptions:
        return self._globalOptions

    @property
    def depsConfValue(self) -> dict:
        return self._depsConfValue

    @property
    def options(self) -> list:
        return self._options

    @property
    def dependencies(self) -> List[Dependency]:
        return self._dependencies

    @property
    def hash(self) -> str:
        if self._hashOk is False:
            raise BuildError("Hash is invalid.")
        return self._hash

    @property
    def buildDir(self) -> str:
        if self._hashOk is False:
            raise BuildError("Hash is invalid.")
        return os.path.join(Preference.get().buildRootDirectory, self.libraryName, self._hash).replace("\\", "/")

    @property
    def installDir(self) -> str:
        if self._hashOk is False:
            raise BuildError("Hash is invalid.")
        return os.path.join(Preference.get().installRootDirectory, self.libraryName, self._hash).replace("\\", "/")

    @classmethod
    def generateVersion(cls, versionString: str) -> Version:
        # general version string: "." delemeter
        # A: A=minor
        # A.B: A=minor, B=patch
        # A.B.C: A=major, B=minor, C=patch
        # A.B.C.D: A=variant, B=major, C=minor, D=patch
        # default is 0
        vers = [int(v) for v in versionString.split(".", 3)]
        if len(vers) == 1:
            return Version(0, 0, vers[0], 0)
        if len(vers) == 2:
            return Version(0, 0, *vers)
        if len(vers) == 3:
            return Version(0, *vers)
        else:
            return Version(*vers)

    def log(self, msg):
        prefix = " --" * self._logIndent

        # TODO:
        print(f"[{self.libraryName}]{prefix}", msg)

    def export(self, config: str) -> dict:
        raise RuntimeError("export() must be implemented.")

    @_logTask
    def checkSignature(self, path: str, signature: str, *, signatureAlgorithm: str = "sha256"):
        import hashlib
        with open(path, mode="rb") as fp:
            sig = hashlib.file_digest(fp, signatureAlgorithm).hexdigest().lower()
            signature = signature.lower()
            self.log(f"  Filepath = {path}")
            self.log(f"  Expected = {signature}")
            self.log(f"Calculated = {sig}")
            if sig == signature:
                self.log("Signature check OK.")
            else:
                self.log("Signature check failed.")
                raise BuildError("Signature check failed.")

    @_logTask
    def createDirectory(self, path: str, *, recreate: bool = True):
        path = os.path.join(self.buildDir, path)
        self.log(f"path = {path}")
        if os.path.exists(path):
            if recreate is False:
                return
            self.remove(path)
        os.makedirs(path)
        self.log("Created.")

    @_logTask
    def remove(self, path: str, *, nonExistOk: bool = True):
        path = os.path.join(self.buildDir, path)
        self.log(f"path = {path}")
        if os.path.exists(path):
            if (os.path.isdir(path)):
                self.log(f"Remove directory: {path}")
                shutil.rmtree(path)
            else:
                self.log(f"Remove file: {path}")
                os.remove(path)
            self.log("Removed.")
        elif nonExistOk is False:
            self.log(f"{path} is not found.")
            raise BuildError("File/Directory is not found.")
        else:
            self.log(f"Not existing. {path}")

    @_logTask
    def download(self, url: str, destination: str, *, signature: str = None, signatureAlgorithm: str = "sha256"):
        import urllib.error
        import urllib.request

        force = self._globalOptions.forceDownload
        if force:
            self.log("FORCE (re)downloading")

        destinationPath = os.path.join(self.buildDir, destination)
        self.log(f"URL: {url}")
        self.log(f"Destination: {destinationPath}")

        exists = os.path.exists(destinationPath)
        self.log(f"Existing? {exists}")

        if exists and force:
            self.log("Erase file.")
            os.remove(destinationPath)
            exists = False

        if exists and signature is not None:
            # signature チェック
            self.checkSignature(destinationPath, signature,
                                signatureAlgorithm=signatureAlgorithm)

        if exists:
            # キャッシュ済み
            self.log("Cached file is available. Skip downloading.")
            return

        self.log("Downloading...")
        try:
            urllib.request.urlretrieve(url, destinationPath)
        except urllib.error.HTTPError as e:
            raise BuildError(f"Failed to download source. {e}")

        if signature is not None:
            self.checkSignature(destinationPath, signature,
                                signatureAlgorithm=signatureAlgorithm)

        self.log("Downloaded.")

        return destinationPath

    @_logTask
    def unzip(self, zipPath: str, destination: str):
        zipPath = os.path.join(self.buildDir, zipPath)
        destination = os.path.join(self.buildDir, destination)
        self.log(f"zip file = {zipPath}")
        self.log(f"Destination = {destination}")
        self.remove(destination)
        shutil.unpack_archive(zipPath, destination)
        self.log("Unzipped.")

    @_logTask
    def cmake(self, args: list):
        args = [Preference.get().cmakePath] + args
        self.log("Execute cmake command.")
        self.log("> " + " ".join(args))
        if subprocess.run(args).returncode != 0:
            raise BuildError("Failed to cmake.")
        self.log("cmake OK.")

    @_logTask
    def cmakeConfigure(self, srcDir: str, buildDir: str, args: list):
        srcDir = os.path.join(self.buildDir, srcDir)
        buildDir = os.path.join(self.buildDir, buildDir)
        self.log(f"Source directory = {srcDir}")
        self.log(f"Build directory = {buildDir}")
        self.remove(buildDir)

        generator = Preference.get().generator
        arch = Preference.get().architecture
        pargs = ["-A", arch]
        if generator is not None:
            pargs += ["-G", generator]
        pargs += args
        pargs += ["-S", srcDir, "-B", buildDir]
        self.cmake(pargs)

    @_logTask
    def cmakeBuild(self, buildDir: str, config: str):
        buildDir = os.path.join(self.buildDir, buildDir)
        self.log(f"Build directory = {buildDir}")
        self.log(f"Config = {config}")
        self.cmake(["--build", buildDir, "--config", config])

    @_logTask
    def cmakeInstall(self, buildDir: str, config: str, prefix: str = ""):
        buildDir = os.path.join(self.buildDir, buildDir)
        installDir = self.installDir
        if prefix:
            installDir = os.path.join(installDir, prefix)
        self.log(f"Build directory = {buildDir}")
        self.log(f"Install directory = {installDir}")
        self.log(f"Config = {config}")
        self.cmake(["--install", buildDir, "--config", config, "--prefix", installDir])

    @_logTask
    def cmakeBuildAndInstall(self, buildDir: str, config: str, installPrefix: str = ""):
        self.cmakeBuild(buildDir, config)
        self.cmakeInstall(buildDir, config, installPrefix)

    @_logTask
    def applyPatch(self, patchFile: str, workingDirectory: str):
        import patch
        patchset = patch.fromfile(patchFile)
        patchset.apply(root=workingDirectory)
        self.log("Patch applied.")
