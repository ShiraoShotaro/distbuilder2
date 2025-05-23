from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(V, Mj, Mi, P): SHA256Hash,
    }

    versions = list(signatures.keys())

    # --- options ---
    # option_Shared = Option(bool, False, "Build shared")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/facebook/zstd/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

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

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir(PACKAGE_NAME)
