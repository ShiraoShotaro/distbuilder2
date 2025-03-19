from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 23, 0): "e0d9562aa27c6c0d47054002a400dcc17215a41386aee36e72b012b77d95a698",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_Static = Option(bool, True, "Build static")
    option_CompressionSupport = Option(bool, True, "Compression support")
    option_DecompressionSupport = Option(bool, True, "Decompression support")
    option_BuildGZip = Option(bool, False, "Build GZIP")
    option_GZipSupport = Option(bool, False, "GZIP support")
    option_ZlibSupport = Option(bool, False, "Zlib support")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        self.download(
            "https://github.com/ebiggers/libdeflate/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/libdeflate-{self.version.major}.{self.version.minor}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DCMAKE_INSTALL_PREFIX={self.installDir}",  # config 時に直接使っているみたいで, これは必須でした
            f"-DLIBDEFLATE_BUILD_GZIP={self.option_BuildGZip}",
            f"-DLIBDEFLATE_BUILD_SHARED_LIB={self.option_Shared}",
            f"-DLIBDEFLATE_BUILD_STATIC_LIB={self.option_Static}",
            "-DLIBDEFLATE_BUILD_TESTS=0",
            f"-DLIBDEFLATE_COMPRESSION_SUPPORT={self.option_CompressionSupport}",
            f"-DLIBDEFLATE_DECOMPRESSION_SUPPORT={self.option_DecompressionSupport}",
            f"-DLIBDEFLATE_GZIP_SUPPORT={self.option_GZipSupport}",
            f"-DLIBDEFLATE_ZLIB_SUPPORT={self.option_ZlibSupport}",
            "-DLIBDEFLATE_USE_SHARED_LIB=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "libdeflate_DIR": f"{self.installDir}/lib/cmake/libdeflate"
        }
