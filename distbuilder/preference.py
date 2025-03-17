import os
from typing import List


class Preference:
    def __init__(self, cfg):
        self._cfg = cfg

        self._root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self._buildDirectory = os.path.abspath(self._cfg["directory"]["build"])
        self._installDirectory = os.path.abspath(self._cfg["directory"]["install"])
        self._sourceDirectories = [os.path.join(self._root, "libs")] \
            + [os.path.abspath(p) for p in self._cfg["directory"]["sources"]]

        # 初期化
        # buildDirectory, installDirectory を作る
        os.makedirs(self._buildDirectory, exist_ok=True)
        os.makedirs(self._installDirectory, exist_ok=True)

    @property
    def buildRootDirectory(self) -> str:
        return self._buildDirectory

    @property
    def installRootDirectory(self) -> str:
        return self._installDirectory

    @property
    def sourceDirectories(self) -> List[str]:
        return self._sourceDirectories.copy()

    @property
    def generator(self) -> str:
        return self._cfg["cmake"].get("generator")

    @property
    def architecture(self) -> str:
        return self._cfg["cmake"]["arch"]

    @property
    def cmakePath(self) -> str:
        return self._cfg["cmake"].get("path", "cmake")

    @classmethod
    def load(cls, path: str):
        import toml
        with open(path, mode="r", encoding="utf-8") as fp:
            cls._instance = Preference(toml.load(fp))

    @classmethod
    def get(cls) -> "Preference":
        return cls._instance
