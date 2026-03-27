from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "df529db3d3caec8dfd4e0389b2feca1601358ff54c9a8d60424d9868fe91c803",
    }

    versions = list(signatures.keys())

    # --- deps ---
    dep_spdlog = Dependency("gabime.spdlog")

    def build(self):
        zipFile = self.download(
            "https://github.com/ShiraoShotaro/roah-logger/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/roah-logger-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d"
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("roah-logger")
