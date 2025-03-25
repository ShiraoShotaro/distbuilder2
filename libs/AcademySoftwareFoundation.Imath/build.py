from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 3, 1, 12): "82d8f31c46e73dba92525bea29c4fe077f6a7d3b978d5067a15030413710bf46",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    def build(self):
        self.download(
            "https://github.com/AcademySoftwareFoundation/Imath/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/Imath-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DPYTHON=0",
            "-DCMAKE_CONFIGURATION_TYPES=Release;Debug",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            "-DBUILD_TESTING=0",
            "-DBUILD_WEBSITE=0",
            "-DIMATH_INSTALL=1",
            "-DIMATH_INSTALL_PKG_CONFIG=0",
            "-DIMATH_INSTALL_SYM_LINK=0",
            "-DIMATH_USE_NOEXCEPT=1",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("Imath")
