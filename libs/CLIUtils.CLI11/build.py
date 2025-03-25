from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 2, 5, 0): "887270cae374a0b9e22b39647f9fc4bc742587fb26d6a221da2d2bbcf3109b0b",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Precompiled = Option(bool, True, "Precompiled")
    option_Sanitizers = Option(bool, False, "Sanitizers")
    option_SingleFile = Option(bool, False, "Single file")

    def build(self):
        self.download(
            "https://github.com/CLIUtils/CLI11/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/CLI11-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DCLI11_BUILD_DOCS=0",
            "-DCLI11_BUILD_EXAMPLES=0",
            "-DCLI11_BUILD_TESTS=0",
            "-DCLI11_INSTALL=1",
            f"-DCLI11_PRECOMPILED={self.option_Precompiled}",
            f"-DCLI11_SANITIZERS={self.option_Sanitizers}",
            f"-DCLI11_SINGLE_FILE={self.option_SingleFile}"
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("CLI11", "share/cmake/{packageName}")
