from typing import Optional, Tuple


class Toolchain:
    def __init__(self, config: str):
        self._dirs: dict = dict()
        self._variables: dict = dict()
        self._packages: dict = dict()
        self._postCmakes: list = list()
        self._config: str = config
        self._builder = None

    def setDir(self, packageName: str, path: str):
        assert self._builder is not None
        self._dirs[self._builder.libraryName] = (packageName, path)

    def getDir(self, libraryName: str) -> Tuple[Optional[str], Optional[str]]:
        return self._dirs.get(libraryName, (None, None))

    def setFilepathVariable(self, key: str, data: str):
        self._variables[key] = (f'"{data}"', "FILEPATH")

    def setStringVariable(self, key: str, data: str):
        self._variables[key] = (f'"{data}"', "STRING")

    def addFindPackage(self, packageName: str, *, required=True, quiet=True):
        self._packages[packageName] = dict(required=required, quiet=quiet)

    def addPostCmake(self, cmake: str):
        self._postCmakes.append(cmake)

    def dump(self) -> str:
        dirs = list()
        reqs = list()
        vars = list()
        post = list()
        dirs.append("# package directories")
        reqs.append("# find packages")
        vars.append("# add variables")
        post.append("# post scripts")
        for packageName, path in self._dirs.values():
            path = path.replace("\\", "/")
            dirs.append(f'set({packageName}_DIR "{path}" CACHE FILEPATH)')
            if packageName not in self._packages:
                reqs.append(f'find_package({packageName} REQUIRED CONFIG)')

        for packageName, options in self._packages.items():
            if options["required"] is True:
                reqs.append(f'find_package({packageName} REQUIRED CONFIG)')
            elif options["quiet"] is True:
                reqs.append(f'find_package({packageName} QUIET CONFIG)')
            else:
                reqs.append(f'find_package({packageName} CONFIG)')

        for key, (value, valtype) in self._variables.items():
            vars.append(f'set({key} {value} CACHE {valtype})')

        for cmake in self._postCmakes:
            post.append(cmake)
            post.append("")

        return "\n".join([
            "# AUTO-GENERATED FILE",
            "",
            "# ---------------------------------------------------------------------",
            "{}".format("\n".join(dirs)),
            "# ---------------------------------------------------------------------",
            "{}".format("\n".join(vars)),
            "# ---------------------------------------------------------------------",
            "{}".format("\n".join(reqs)),
            "# ---------------------------------------------------------------------",
            "{}".format("\n".join(post)),
        ])
