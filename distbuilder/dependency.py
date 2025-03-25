from typing import Callable, Union, Optional
from .functions import searchBuilderAndPath
from .version import Version
from .errors import BuildError
from .global_options import GlobalOptions


class Dependency:
    def __init__(self, libraryName: str, *,
                 condition: Union[bool, Callable[[object], bool]] = True,
                 versionVariant: str = "*",
                 versionMajor: str = "*",
                 versionMinor: str = "*",
                 versionPatch: str = "*",
                 overrideOptions: dict = None):
        from .builder import BuilderBase
        self._libraryName: str = libraryName
        self._condition: bool = condition
        self._versionVariant: str = versionVariant
        self._versionMajor: str = versionMajor
        self._versionMinor: str = versionMinor
        self._versionPatch: str = versionPatch
        self._overrideOptions: dict = overrideOptions if overrideOptions else dict()
        self._builder: Optional[BuilderBase] = None

    @property
    def libraryName(self) -> str:
        return self._libraryName

    @property
    def overrideOptions(self) -> dict:
        return self._overrideOptions.copy()

    @property
    def hash(self) -> Optional[str]:
        if self._builder is not None:
            return self._builder.hash
        else:
            return None

    def copy(self):
        dep = Dependency(self._libraryName,
                         condition=self._condition,
                         versionVariant=self._versionVariant,
                         versionMajor=self._versionMajor,
                         versionMinor=self._versionMinor,
                         versionPatch=self._versionPatch,
                         overrideOptions=self._overrideOptions.copy())
        dep._builder = self._builder
        return dep

    def searchBuilderClass(self):
        return searchBuilderAndPath(self._libraryName)[0]

    def isResolved(self) -> bool:
        if self._builder is None:
            return False
        return self._builder.isResolved()

    def isRequired(self, builder) -> bool:
        condition = True
        if callable(self._condition):
            condition = self._condition(builder)
        else:
            condition = bool(self._condition)
        return condition

    def isSuitableVersion(self, version: Version) -> bool:
        return version.match(self._versionVariant, self._versionMajor, self._versionMinor, self._versionPatch)

    def resolve(self, builder):
        # 条件に合致するライブラリを見つける
        if not self.isRequired(builder):
            return

        builderCls, path = searchBuilderAndPath(self._libraryName)
        versions = set()
        for version in builderCls.versions:
            if version.match(self._versionVariant, self._versionMajor, self._versionMinor, self._versionPatch):
                versions.add(version)

        if not versions:
            raise BuildError(f"Not found dependency. {self._libraryName} "
                             f"({self._versionVariant}.{self._versionMajor}.{self._versionMinor}.{self._versionPatch})")

        # option を override 指定する
        # 既に指定された option で, 異なる値だった場合は止める
        for optkey, opt in self._overrideOptions.items():
            if optkey in builder.options:
                if builder.options[optkey] != opt:
                    raise BuildError("Dependency option error.")

        return (builderCls, versions, self._overrideOptions)

    def generateBuilder(self, builder):
        depBuilderCls, availableVersions, _ = self.resolve(builder)
        requiredVersion = depBuilderCls.generateVersion(builder.depsConfValue[self._libraryName]["version"])
        if requiredVersion not in availableVersions:
            raise BuildError("Dependency version error.")
        return depBuilderCls(requiredVersion, builder.depsConfValue, GlobalOptions())
