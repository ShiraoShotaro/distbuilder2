import glob
import os
import shutil
import re
import subprocess
import hashlib
import json
from typing import List, Union, Optional, Set
from collections import OrderedDict
from .errors import BuildError
from .preference import Preference
from .toolchain import Toolchain
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


class _IOLogBuffer:
    def __init__(self, stream, isStr, logFn):
        self._stream = stream
        self._isStr = isStr
        self._logFn = logFn
        self._buffer = list()
        self._data = bytes()

    def _tryDecode(self):
        try:
            return self._data.decode("utf-8").rstrip("\n")
        except UnicodeDecodeError:
            try:
                return self._data.decode("cp932").rstrip("\n")
            except UnicodeDecodeError:
                return None

    def read(self):
        while self._stream.readable():
            data = self._stream.read(1)
            if len(data) == 0:
                break
            self._data += data

            if self._isStr is True and self._data[-1] == b'\n'[0]:
                strData = self._tryDecode()
                if strData is not None:
                    self._logFn(strData)
                    self._buffer.append(strData)
                    self._data = bytes()
        if self._isStr is True:
            strData = self._tryDecode()
            if strData is not None and strData != "":
                self._logFn(strData)
                self._buffer.append(strData)
            self._data = "\n".join(self._buffer)

    def dump(self):
        return self._data


# , version: str, options: dict, globalOptions: dict


class BuilderBase:
    def __init__(self, depsConfValue: dict, globalOptions: GlobalOptions):
        self._libraryName = self.__class__.__module__.__name__
        self._builderScriptPath = self.__class__.__module__.__file__
        self._logIndent = 0

        # version
        # -- 指定されないこともある. その場合はビルド実行できない.
        self._version: Option[Version] = None
        if self._libraryName in depsConfValue:
            version = depsConfValue[self._libraryName].get("version", None)
            if version is not None:
                if isinstance(version, Version):
                    self._version = version
                else:
                    self._version = self.generateVersion(version)

        # Global Options
        self._globalOptions: GlobalOptions = globalOptions

        # deps config value
        self._depsConfValue: dict = depsConfValue.copy()

        # この builder に対する option values
        optionValues = dict()
        if self._libraryName in depsConfValue:
            optionValues = depsConfValue[self._libraryName].get("options", dict())

        # option, dependency をピックアップする.
        self._options = list()
        self._dependencies = list()
        for member in dir(self.__class__):
            if member.startswith("option_"):
                m = getattr(self.__class__, member)
                if isinstance(m, Option):
                    m._key = member[7:]
                    opt = m._instantiate(self, optionValues.get(m._key))
                    setattr(self, member, opt)
                    self._options.append(opt)
            if member.startswith("dep_"):
                m = getattr(self.__class__, member)
                if isinstance(m, Dependency):
                    dep = m.copy()
                    setattr(self, member, dep)
                    self._dependencies.append(dep)
        self._options.sort(key=lambda v: v.key)
        self._dependencies.sort(key=lambda v: v.libraryName)

        # Hash
        self._hashData: Optional[dict] = None
        self._hash: Option[str] = None

        # CMake toolchain
        self._toolchain: Optional[Toolchain] = None

        # File Handle
        self._fp = None

    def _setDirty(self):
        self._hash = None
        self._hashData = None

    def updateHash(self, *, force: bool = False):
        if force is False and self._hash is not None:
            return

        if self.isResolved() is not True:
            raise BuildError(f"Cannot calc hash. library ({self._libraryName}) unresolved.")

        # -- calc build.py signature
        # 空行, コメント行は全てカットする.
        script = ""
        if not self._globalOptions.ignoreScriptVersion:
            with open(self._builderScriptPath, mode="r", encoding="utf-8") as fp:
                scriptLines = fp.readlines()

            for ln in scriptLines:
                lnn = ln.strip()
                if lnn == "" or lnn.startswith("#"):
                    continue
                script += ln.rstrip() + "\n"
            script = hashlib.sha256(script.encode()).hexdigest()
        else:
            self.log("!!!! Script version is IGNORED !!!!")

        # -- build json object
        jobj = OrderedDict(
            libraryName=self._libraryName,
            scriptSignature=script,
            version=str(self._version),
            options=list(),
            deps=list(),
        )

        for option in self._options:
            jobj["options"].append(OrderedDict(key=option.key, value=str(option)))
        for dep in self._dependencies:
            if dep.isRequired(self):
                dep.updateHash()
                jobj["deps"].append(OrderedDict(libraryName=dep.libraryName, hash=dep.hash))
            # else: 使用しない dependency は記述しない.
        self._hashData = json.dumps(jobj, indent=2, ensure_ascii=False)

        # -- calc hash
        self._hash = hashlib.md5(self._hashData.encode()).hexdigest()

    def setVersion(self, version: Version):
        self._version = version
        self._setDirty()

    def isResolved(self) -> bool:
        if self._hash is not None:
            return True
        if self._version is None:
            self.log("Unresolved. version is None.")
            return False
        for dep in self._dependencies:
            if not dep.isResolved():
                self.log(f"Unresolved. Dependency (library:{dep.libraryName}) is not resolved.")
                return False
        return True

    def prepare(self):
        if self._hash is None:
            self.updateHash()

        # ディレクトリ作る
        if self._globalOptions.createDirectory:
            if self._globalOptions.cleanBuild and os.path.exists(self.buildDir):
                shutil.rmtree(self.buildDir)
            os.makedirs(self.buildDir, exist_ok=True)

            if os.path.exists(self.installDir):
                shutil.rmtree(self.installDir)
            os.makedirs(self.installDir, exist_ok=True)

            # hash str を json で保存する
            with open(os.path.join(self.buildDir, "info.json"), mode="w", encoding="utf-8") as fp:
                fp.write(self._hashData)
            with open(os.path.join(self.installDir, "info.json"), mode="w", encoding="utf-8") as fp:
                fp.write(self._hashData)

            # deps に対して cmake toolchain を作る.
            self._toolchain = Toolchain(self.globalOptions.config)

            def _traverse(bld):
                for dep in bld.dependencies:
                    if dep.isRequired(bld):
                        self._toolchain._builder = dep.builder
                        dep.builder.export(self._toolchain)
                        self._toolchain._builder = None
                        _traverse(dep.builder)

            _traverse(self)
            self.exportToolchainForBuild()

    def exportToolchainForBuild(self):
        # toolchain を build directory に書き出す
        with open(os.path.join(self.buildDir, "toolchain.cmake"), mode="w", encoding="utf-8") as fp:
            fp.write(self._toolchain.dump())

    @property
    def libraryName(self) -> str:
        """ ライブラリ名を取得 """
        return self._libraryName

    @property
    def version(self) -> Optional[Version]:
        """ ビルドバージョンを取得. """
        return self._version

    @property
    def availableVersions(cls) -> Set[Version]:
        return set(cls.versions)

    @property
    def globalOptions(self) -> GlobalOptions:
        """ GlobalOption を取得. """
        return self._globalOptions

    # @property
    # def depsConfValue(self) -> dict:
    #     """ コンフィグを取得 """
    #     # Deprecated.
    #     raise RuntimeError("DEPRECATED.")
    #     return self._depsConfValue.copy()

    @property
    def options(self) -> List[Option]:
        """ オプションの一覧を取得. """
        return self._options.copy()

    @property
    def dependencies(self) -> List[Dependency]:
        """ 依存ライブラリ一覧を取得. """
        return self._dependencies.copy()

    @property
    def hash(self) -> Optional[str]:
        """ ハッシュを取得. """
        return self._hash

    @property
    def hashData(self) -> Optional[str]:
        """ ハッシュ元文字列データを取得. """
        return self._hashData

    @property
    def buildDir(self) -> str:
        self.updateHash()
        return os.path.join(Preference.get().buildRootDirectory, self.libraryName, self._hash).replace("\\", "/")

    @property
    def installDir(self) -> str:
        self.updateHash()
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

        print(f"[{self.libraryName}]{prefix}", msg)

        if self._fp is not None:
            print(f"{prefix}", msg, file=self._fp)

    def _executeBuildSequence(self):
        class BuildScope:
            def __init__(self, builder):
                self._cwd = None
                self._builder = builder

            def __enter__(self, *_):
                self._cwd = os.getcwd()
                os.chdir(os.path.dirname(self._builder._builderScriptPath))

            def __exit__(self, *_):
                if self._cwd is not None:
                    os.chdir(self._cwd)
                if self._builder._fp is not None:
                    self._builder._fp = None

        with BuildScope(self):
            self.prepare()
            with open(os.path.join(self.buildDir, "build.log"), mode="w", encoding="utf-8") as fp:
                self._fp = fp
                self.build()

    def build(self):
        raise RuntimeError("build() must be implemented and do not call super class build().")

    def export(self, toolchain: Toolchain) -> dict:
        raise RuntimeError("export() must be implemented and do not call super class export().")

    def _makeAbspath(self, path: str):
        if os.path.isabs(path):
            return path
        else:
            return os.path.join(self.buildDir, path)

    @_logTask
    def checkSignature(self, path: str, signature: str, *, signatureAlgorithm: str = "sha256"):
        import hashlib
        path = self._makeAbspath(path)
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
        path = self._makeAbspath(path)
        self.log(f"path = {path}")
        if os.path.exists(path):
            if recreate is False:
                return
            self.remove(path)
        os.makedirs(path)
        self.log("Created.")

    @_logTask
    def remove(self, path: str, *, nonExistOk: bool = True):
        path = self._makeAbspath(path)
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
    def download(self, url: str, signature: str, *, ext: str = None) -> str:
        from .blob import Blob
        blob = Blob(self)
        return blob.fetch(url, signature, ext=ext)

    @_logTask
    def unzip(self, zipPath: str, destination: str):
        zipPath = self._makeAbspath(zipPath)
        destination = self._makeAbspath(destination)
        self.log(f"zip file = {zipPath}")
        self.log(f"Destination = {destination}")
        exists = os.path.exists(destination)
        if exists and self._globalOptions.unzipAndOverwrite:
            self.remove(destination)
            exists = False
        if exists is False:
            shutil.unpack_archive(zipPath, destination)
            self.log("Unzipped.")
        else:
            self.log("!!! Destination path is already exist, Skip unzip. (no_unzipOverwrite) !!!")

    def _executeCommand(self, args: list, *,
                        stdin=None,
                        stdoutBin: bool = False, stderrBin: Optional[str] = False,
                        cwd: Optional[str] = None,
                        env: Optional[dict] = None,
                        label: str = ""):

        self.log("Commandline: {}".format(" ".join([(c if " " not in c else f'"{c}"') for c in args])))
        self.log("Executing...")
        ret = subprocess.Popen(args,
                               stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=cwd, env=env, bufsize=0)

        if label != "":
            label = f":{label}"
        stdout = _IOLogBuffer(ret.stdout, not stdoutBin, lambda t: self.log(f"stdout{label}>{t}"))
        stderr = _IOLogBuffer(ret.stderr, not stderrBin, lambda t: self.log(f"stderr{label}>{t}"))

        import threading
        stdoutTh = threading.Thread(target=lambda: stdout.read())
        stderrTh = threading.Thread(target=lambda: stderr.read())
        stdoutTh.start()
        stderrTh.start()
        stdoutTh.join()
        stderrTh.join()
        return (ret.wait(), stdout.dump(), stderr.dump())

    @_logTask
    def executeCommand(self, args: list, *,
                       stdin=None,
                       stdoutEncoding: Optional[str] = "utf-8", stderrEncoding: Optional[str] = "utf-8",
                       cwd: Optional[str] = None,
                       env: Optional[dict] = None,
                       label: str = ""):
        return self._executeCommand(args, stdin=stdin,
                                    stdoutEncoding=stdoutEncoding, stderrEncoding=stderrEncoding,
                                    cwd=cwd, env=env, label=label)

    def _cmake(self, args: list, *, label: str = ""):
        if label != "":
            label = f"cmake:{label}"
        args = [Preference.get().cmakePath] + args
        self.log("Execute cmake command.")
        if self._executeCommand(args, label=label)[0] != 0:
            raise BuildError("Failed to cmake.")
        self.log("cmake OK.")

    @_logTask
    def cmake(self, args: list, *, label: str = ""):
        self._cmake(args, label=label)

    @_logTask
    def cmakeConfigure(self, srcDir: str, buildDir: str, args: list, *, withToolchain: bool = True):
        srcDir = self._makeAbspath(srcDir)
        buildDir = self._makeAbspath(buildDir)
        toolchainFile = os.path.join(self.buildDir, "toolchain.cmake")
        self.log(f"Source directory = {srcDir}")
        self.log(f"Build directory = {buildDir}")
        if withToolchain is True:
            self.log(f"Toolchain = {toolchainFile}")
        self.remove(buildDir)

        generator = Preference.get().generator
        arch = Preference.get().architecture
        pargs = ["-A", arch]
        if generator is not None:
            pargs += ["-G", generator]
        pargs += args
        if withToolchain is True:
            pargs.append(f"-DCMAKE_TOOLCHAIN_FILE={toolchainFile}")
        pargs += ["-S", srcDir, "-B", buildDir]
        self._cmake(pargs, label="configure")

    @_logTask
    def cmakeBuild(self, buildDir: str, config: str):
        if config in self._globalOptions.configs:
            buildDir = self._makeAbspath(buildDir)
            self.log(f"Build directory = {buildDir}")
            self.log(f"Config = {config}")
            self._cmake(["--build", buildDir, "--config", config], label=f"build[{config}]")

    @_logTask
    def cmakeInstall(self, buildDir: str, config: str, prefix: str = ""):
        if config in self._globalOptions.configs:
            buildDir = self._makeAbspath(buildDir)
            installDir = self.installDir
            if prefix:
                installDir = os.path.join(installDir, prefix)
            self.log(f"Build directory = {buildDir}")
            self.log(f"Install directory = {installDir}")
            self.log(f"Config = {config}")
            self._cmake(["--install", buildDir, "--config", config, "--prefix", installDir],
                        label=f"install[{config}]")

    def cmakeBuildAndInstall(self, buildDir: str, config: str, installPrefix: str = ""):
        self.cmakeBuild(buildDir, config)
        self.cmakeInstall(buildDir, config, installPrefix)

    @_logTask
    def copyFile(self, srcFile: str, destFile: str, *, allowOverwrite=False):
        srcFile = self._makeAbspath(srcFile)
        destFile = self._makeAbspath(destFile)
        if os.path.exists(destFile):
            if allowOverwrite is True:
                os.remove(destFile)
            else:
                raise BuildError(f"Failed to copy file. {destFile} is already existing.")
        self.log("File copying...")
        self.log(f"-- src: {srcFile}")
        self.log(f"-- dst: {destFile}")
        shutil.copy(srcFile, destFile)
        self.log("Copied.")

    @_logTask
    def applyPatch(self, patchFile: str, root: str):
        import patch_ng
        patchFile = os.path.abspath(patchFile)
        root = self._makeAbspath(root)
        self.log("Patch applying...")
        self.log(f"-- patch file: {patchFile}")
        self.log(f"-- root dir: {root}")

        patchset = patch_ng.fromfile(patchFile)
        ret = patchset.apply(root=root)
        if ret is False:
            raise BuildError("Failed to apply patch.")
        self.log("Patch applied.")

    @_logTask
    def applyPatches(self, patchRoot: str, targetRoot: str):
        patchRoot = os.path.abspath(patchRoot)
        patchFiles = glob.glob(f"{patchRoot}/**/*.patch", recursive=True)
        self.log(f"{len(patchFiles)} files to patch.")
        for patchFile in patchFiles:
            self.applyPatch(patchFile, targetRoot)


class _Dummy:
    __name__ = "<dummylib>"
    __file__ = ""


class EmptyBuilder(BuilderBase):
    __module__ = _Dummy
    versions = list()

    def updateHash(self, *_, **__):
        raise RuntimeError("program error.")

    def isResolved(self):
        return True

    def prepare(self):
        pass

    def build(self):
        pass

    def export(self, config: str):
        return dict()
