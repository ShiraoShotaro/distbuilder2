from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 4, 7, 0): "6431504A36FD864C8C83C4D0E2E18496E6968B4061D347988E20DF04C7BBDA96",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_WithZstd = Option(bool, False, "With Zstd")
    option_WithZlib = Option(bool, False, "With zlib")
    option_WithDeflate = Option(bool, False, "With libdeflate")

    # --- deps ---
    dep_zlib = Dependency("madler.zlib", condition=lambda self: self.option_WithZlib.value)
    dep_zstd = Dependency("facebook.zstd", condition=lambda self: self.option_WithZStd.value)
    dep_libdeflate = Dependency("ebiggers.libdeflate",
                                condition=lambda self: self.option_WithDeflate.value,
                                overrideOptions={"ZlibSupport": True})

    def build(self):
        self.download(
            "https://gitlab.com/libtiff/libtiff/-/archive/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/"
            f"libtiff-v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/libtiff-v{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-Dtiff-deprecated=0",
            "-Dtiff-docs=0",
            "-Dtiff-install=1",
            "-Dtiff-tests=0",
            "-Dtiff-tools=0",
            f"-Dzlib={self.option_WithZlib}",
            f"-Dzstd={self.option_WithZStd}",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}"
        ]

        # Apply patch
        self.applyPatch(
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/FindDeflate.cmake.patch",
            srcPath)
        self.applyPatch(
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/ZSTDCodec.cmake.patch",
            srcPath)

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("Tiff", "lib/cmake/tiff")
