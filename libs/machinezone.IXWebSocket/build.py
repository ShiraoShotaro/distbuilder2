from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 11, 4, 6): "99f9288e0f742ad08bc60d99abeef6169a3bf137f9c1ef1cca5d39ffbbe9d44b",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_UseZlib = Option(bool, False, "Use zlib")

    # --- deps ---
    dep_zlib = Dependency("madler.zlib", condition=lambda self: self.option_UseZlib)

    def build(self):
        zipFile = self.download(
            "https://github.com/machinezone/IXWebSocket/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/IXWebSocket-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            f"-DUSE_ZLIB={self.option_UseZlib}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("ixwebsocket")
