from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 4, 2, 0): "8afdf5bcc08bcf413140ff18263668d650552ff90dab0fcb9fa1e8845637664a",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_Version = Option(str, "0.0.0", "MongoDB C Driver version (e.g. 8.0.20)")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/mongodb/mongo-cxx-driver/archive/refs/tags/"
            f"r{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/mongo-cxx-driver-r{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DBUILD_TESTING=OFF",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            f"-DBUILD_VERSION={self.option_Version}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("mongo-cxx-driver")
