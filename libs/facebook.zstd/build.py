from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 5, 6): "3b1c3b46e416d36931efd34663122d7f51b550c87f74de2d38249516fe7d8be5",
        Version(0, 1, 5, 7): "7897bc5d620580d9b7cd3539c44b59d78f3657d33663fe97a145e07b4ebd69a4"
    }

    versions = list(signatures.keys())
    recipeVersion = 0

    option_BuildCompression = Option(bool, True, "Build compression")
    option_BuildDecompression = Option(bool, True, "Build decompression")
    option_BuildProgram = Option(bool, False, "Build program.")
    option_Shared = Option(bool, True, "Build shared.")
    option_Static = Option(bool, True, "Build static.")
    option_LegacySupport = Option(bool, True, "Legacy support")
    option_LZ4Support = Option(bool, False)
    option_LZMASupport = Option(bool, False)
    option_MultiThreadSupport = Option(bool, True)
    option_ProgramsLinkShared = Option(bool, False)
    option_UseStaticRuntime = Option(bool, False, "Build MT/MTd")
    option_ZlibSupport = Option(bool, False)

    dep_zlib = Dependency("madler.zlib",
                          condition=lambda builder: builder.option_ZlibSupport.value)

    def build(self):
        self.download(
            "https://github.com/facebook/zstd/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/zstd-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DZSTD_BUILD_COMPRESSION={self.option_BuildCompression}",
            f"-DZSTD_BUILD_DECOMPRESSION={self.option_BuildDecompression}",
            "-DZSTD_BUILD_DEPRECATED=0",
            f"-DZSTD_BUILD_PROGRAMS={self.option_BuildProgram}",
            f"-DZSTD_BUILD_SHARED={self.option_Shared}",
            f"-DZSTD_BUILD_STATIC={self.option_Static}",
            "-DZSTD_BUILD_TESTS=0",
            f"-DZSTD_LEGACY_SUPPORT={self.option_LegacySupport}",
            f"-DZSTD_LZ4_SUPPORT={self.option_LZ4Support}",
            f"-DZSTD_LZMA_SUPPORT={self.option_LZMASupport}",
            f"-DZSTD_MULTITHREAD_SUPPORT={self.option_MultiThreadSupport}",
            f"-DZSTD_PROGRAMS_LINK_SHARED={self.option_ProgramsLinkShared}",
            f"-DZSTD_USE_STATIC_RUNTIME={self.option_UseStaticRuntime}",
            f"-DZSTD_ZLIB_SUPPORT={self.option_ZlibSupport}"
        ]

        if self.version.match(0, 1, 5, 6):
            # https://github.com/facebook/zstd/issues/3999
            configArgs.append(f"-DCMAKE_RC_FLAGS=-I{self.buildDir}/{srcPath}/lib")

        self.cmakeConfigure(f"{srcPath}/build/cmake", "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("zstd")
