from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 6, 47): "D7EFC089968972FB79A4AB71BD9311F56C58A51B858A17BAB85D806EC48CC77A",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    # --- deps ---
    dep_zlib = Dependency("madler.zlib")

    def build(self):
        self.download(
            "https://github.com/pnggroup/libpng/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/libpng-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DPNG_BUILD_ZLIB=0",
            "-DPNG_DEBUG=0",
            f"-DPNG_SHARED={self.option_Shared}",
            f"-DPNG_STATIC={not self.option_Shared.value}",
            "-DPNG_TESTS=0",
            "-DPNG_TOOLS=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("PNG")
