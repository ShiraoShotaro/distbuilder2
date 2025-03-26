from typing import Iterable, Optional, Set


class GlobalOptions:
    def __init__(self, *,
                 cleanBuild: bool = False,
                 forceDownload: bool = False,
                 createDirectory: bool = False,
                 unzipAndOverwrite: bool = True,
                 ignoreScriptVersion: bool = False,
                 configs: Iterable[str] = ("Debug", "Release")):
        self._cleanBuild = cleanBuild
        self._forceDownload = forceDownload
        self._createDirectory = createDirectory
        self._unzipAndOverwrite = unzipAndOverwrite
        self._ignoreScriptVersion = ignoreScriptVersion
        self._configs: Set[str] = set(configs)

    @property
    def cleanBuild(self) -> bool:
        return self._cleanBuild

    @property
    def forceDownload(self) -> bool:
        return self._forceDownload

    @property
    def createDirectory(self) -> bool:
        return self._createDirectory

    @property
    def unzipAndOverwrite(self) -> bool:
        return self._unzipAndOverwrite

    @property
    def ignoreScriptVersion(self) -> bool:
        return self._ignoreScriptVersion

    @property
    def config(self) -> str:
        # 廃止予定.
        return "Release"

    @property
    def configs(self) -> Set[str]:
        return self._configs
