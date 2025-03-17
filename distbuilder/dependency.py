from typing import Callable, Union
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
                 versionPatch: str = "*"):
        self._libraryName: str = libraryName
        self._condition: bool = condition
        self._versionVariant: str = versionVariant
        self._versionMajor: str = versionMajor
        self._versionMinor: str = versionMinor
        self._versionPatch: str = versionPatch

    @property
    def libraryName(self) -> str:
        return self._libraryName

    def isRequired(self, builder) -> bool:
        condition = True
        if callable(self._condition):
            condition = self._condition(builder)
        else:
            condition = bool(self._condition)
        return condition

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
        return (builderCls, versions)

    def generateBuilder(self, builder):
        depBuilderCls, availableVersions = self.resolve(builder)
        requiredVersion = depBuilderCls.generateVersion(builder.depsConfValue[self._libraryName]["version"])
        if requiredVersion not in availableVersions:
            raise BuildError("Dependency version error.")
        return depBuilderCls(requiredVersion, builder.depsConfValue, GlobalOptions())
