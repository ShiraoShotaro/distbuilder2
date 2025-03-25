from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 4, 0): "98BBCC32163AAB78137E5A8E87F34067CFB36CA167514622A838490207FD218D",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    # --- deps ---
    dep_jpeg = Dependency("libjpeg-turbo.libjpeg-turbo")

    def build(self):
        self.download(
            "https://github.com/google/libultrahdr/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/libultrahdr-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            "-DUHDR_BUILD_BENCHMARK=0",
            "-DUHDR_BUILD_DEPS=0",
            "-DUHDR_BUILD_EXAMPLES=0",
            "-DUHDR_BUILD_FUZZERS=0",
            "-DUHDR_BUILD_JAVA=0",
            "-DUHDR_BUILD_TESTS=0",
            "-DUHDR_ENABLE_GLES=0",  # /w GPU acceleration
            "-DUHDR_ENABLE_INSTALL=1",
            "-DCMAKE_CROSSCOMPILING=0",
            "-DUHDR_ENABLE_INTRINSICS=1",  # /w SIMD
            "-DUHDR_ENABLE_LOGS=0",
            "-DUHDR_WRITE_ISO=1",
            "-DUHDR_WRITE_XMP=1",
        ]

        # Apply patch
        self.applyPatch(
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/CMakeLists.txt.patch",
            srcPath)

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        # TODO:
        # toolchain.setDir("absl")
        pass
