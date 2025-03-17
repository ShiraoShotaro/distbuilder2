

class GlobalOptions:
    def __init__(self, *,
                 cleanBuild: bool = False,
                 forceDownload: bool = False,
                 createDirectory: bool = False):
        self._cleanBuild = cleanBuild
        self._forceDownload = forceDownload
        self._createDirectory = createDirectory

    @property
    def cleanBuild(self) -> bool:
        return self._cleanBuild

    @property
    def forceDownload(self) -> bool:
        return self._forceDownload

    @property
    def createDirectory(self) -> bool:
        return self._createDirectory
