from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 4, 7, 0): "6431504A36FD864C8C83C4D0E2E18496E6968B4061D347988E20DF04C7BBDA96",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_WithZStd = Option(bool, True, "With Zstd")
    option_WithZlib = Option(bool, True, "With zlib")
    option_WithDeflate = Option(bool, True, "With libdeflate")

    # --- deps ---
    dep_zlib = Dependency("madler.zlib", condition=lambda self: self.option_WithZlib.value)
    dep_zstd = Dependency("facebook.zstd", condition=lambda self: self.option_WithZStd.value)
    dep_libdeflate = Dependency("ebiggers.libdeflate", condition=lambda self: self.option_WithDeflate.value)

    def build(self):
        self.download(
            "https://gitlab.com/libtiff/libtiff/-/archive/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/"
            f"libtiff-v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        # self.unzip("src.zip", "src")

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
        ]

        roots = list()

        if self.dep_zlib.isRequired(self):
            configArgs.append(f"-DZLIB_ROOT={self.dep_zlib.generateBuilder(self).installDir}")
        if self.dep_zstd.isRequired(self):
            # configArgs.append(f"-DZSTD_ROOT={self.dep_zstd.generateBuilder(self).installDir}")
            roots.append(self.dep_zstd.generateBuilder(self).installDir)
        if self.dep_libdeflate.isRequired(self):
            # configArgs.append(
            # f"-DDeflate_ROOT={self.dep_libdeflate.generateBuilder(self).installDir}")
            roots.append(self.dep_libdeflate.generateBuilder(self).installDir)

        configArgs.append("-DCMAKE_FIND_ROOT_PATH={}".format(";".join(roots)))

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "Tiff_DIR": f"{self.installDir}/lib/cmake/tiff"
        }
