from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 11, 1, 4): "7e85cbf6125a76daa0f83cd9240eff863d988aca68cd5f66c01ff7b59fa886b6",
    }

    versions = list(signatures.keys())

    def build(self):
        zipFile = self.download(
            "https://github.com/fmtlib/fmt/archive/refs/tags/"
            f"{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/fmt-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DFMT_CUDA_TEST=0",
            "-DFMT_DEBUG_POSTFIX=d",
            "-DFMT_DOC=0",
            "-DFMT_FUZZ=0",
            "-DFMT_INSTALL=1",
            "-DFMT_TEST=0",
            "-DFMT_UNICODE=1",
            "-DFMT_WERROR=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("fmt")
