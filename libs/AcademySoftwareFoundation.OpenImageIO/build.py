from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(3, 0, 4, 0): "D23607007EBEC38341033021156BF077EE5654EACA92E13742A7F9DA097D995A",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    # --- deps ---
    dep_zlib = Dependency("madler.zlib")
    dep_Imath = Dependency("AcademySoftwareFoundation.Imath")
    dep_openexr = Dependency("AcademySoftwareFoundation.openexr")
    dep_libjpeg_turbo = Dependency("libjpeg-turbo.libjpeg-turbo")
    dep_libultrahdr = Dependency("google.libultrahdr")

    dep_libtiff = Dependency("libtiff.libtiff")

    def build(self):
        self.download(
            "https://github.com/AcademySoftwareFoundation/OpenImageIO/archive/refs/tags/"
            f"v{self.version.variant}.{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = ("src/OpenImageIO-"
                   f"{self.version.variant}.{self.version.major}.{self.version.minor}.{self.version.patch}")

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DOIIO_BUILD_PROFILER=0",
            "-DOIIO_BUILD_TESTS=0",
            "-DOIIO_BUILD_TOOLS=0",
            "-DINSTALL_DOCS=0",
            "-DINSTALL_FONTS=0",
            "-DBUILD_DOCS=0",
            "-DUSE_PYTHON=0",
            f"-DBUILD_SHARED_LIB={self.option_Shared}",
            f"-DZLIB_ROOT={self.dep_zlib.generateBuilder(self).installDir}",
            f"-DImath_DIR={self.dep_Imath.generateBuilder(self).installDir}/lib/cmake/Imath",
            f"-DOpenEXR_DIR={self.dep_openexr.generateBuilder(self).installDir}/lib/cmake/OpenEXR",
            f"-Dlibjpeg-turbo_DIR={self.dep_libjpeg_turbo.generateBuilder(self).installDir}/lib/cmake/libjpeg-turbo",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        # self.cmakeBuildAndInstall("build", "Debug")
        # self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "OpenImageIO_DIR": f"{self.installDir}/lib/cmake/OpenImageIO"
        }
