from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 34, 4): "5322aee0ecde764a82195e8c286a0d2682886cabf901d3003a86e0d2b6c777cf",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared.")
    option_Static = Option(bool, True, "Build static.")

    def build(self):
        self.download(
            "https://github.com/c-ares/c-ares/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/c-ares-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DCARES_STATIC={self.option_Static}",
            f"-DCARES_SHARED={self.option_Shared}",
            "-DCARES_INSTALL=1",
            "-DCARES_STATIC_PIC=0",
            "-DCARES_BUILD_TESTS=0",
            "-DCARES_BUILD_CONTAINER_TESTS=0",
            "-DCARES_BUILD_TOOLS=0",
            "-DCARES_SYMBOL_HIDING=1",  # Default is off
            "-DCARES_THREADS=1",
            "-DCARES_MSVC_STATIC_RUNTIME=0",  # MD
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("c-ares")
