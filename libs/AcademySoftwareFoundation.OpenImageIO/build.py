from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        # Version(2, 5, 18, 0): "a999a45b5caccf370309e60b5d59622919c4a546aa6d0cec79cab0c361a380f9",
        Version(3, 0, 4, 0): "d23607007ebec38341033021156bf077ee5654eaca92e13742a7f9da097d995a",
    }

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
    dep_libpng = Dependency("pnggroup.libpng")
    dep_freetype = Dependency("freetype.freetype")

    def build(self):
        zipFile = self.download(
            "https://github.com/AcademySoftwareFoundation/OpenImageIO/archive/refs/tags/"
            f"v{self.version.variant}.{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = ("src/OpenImageIO-"
                   f"{self.version.variant}.{self.version.major}.{self.version.minor}.{self.version.patch}")

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_SHARED_LIB={self.option_Shared}",
            "-DOIIO_BUILD_PROFILER=0",
            "-DOIIO_BUILD_TESTS=0",
            "-DOIIO_BUILD_TOOLS=0",
            "-DINSTALL_DOCS=0",
            "-DINSTALL_FONTS=0",
            "-DBUILD_DOCS=0",
            "-DUSE_PYTHON=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        # self.cmakeBuildAndInstall("build", "Debug")
        # self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("OpenImageIO")
