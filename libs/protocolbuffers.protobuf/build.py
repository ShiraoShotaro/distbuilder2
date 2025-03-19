from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 29, 1, 0): "ac5fe60325e14eef25fcfea838b73b82fb0e09b15504ce81f6361de3a41a40a1",
        Version(0, 29, 3, 0): "85803e01f347141e16a2f770213a496f808fff9f0138c7c0e0c9dfa708b0da92",
        # Version(0, 30, 1, 0): "199f1bf1b6ad579590dd3666e1b1c5ef0c930b148d231d0da41b0867bf42994d",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_WithZlib = Option(bool, True, "With zlib")
    option_UseStaticZlib = Option(bool, True, "Use static zlib")

    # --- deps ---
    dep_abseil = Dependency("abseil.abseil-cpp")
    dep_utf8_range = Dependency("protocolbuffers.utf8_range")
    dep_zlib = Dependency("madler.zlib", condition=lambda self: self.option_WithZlib.value)

    def build(self):
        # TODO: patch, rc対応してない
        self.download("https://github.com/protocolbuffers/protobuf/archive/refs/tags/"
                      f"v{self.version.major}.{self.version.minor}.zip",
                      "src.zip", signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/protobuf-{self.version.major}.{self.version.minor}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-Dprotobuf_ABSL_PROVIDER=package",
            "-Dprotobuf_ALLOW_CCACHE=0",
            "-Dprotobuf_BUILD_CONFORMANCE=0",
            "-Dprotobuf_BUILD_EXAMPLES=0",
            "-Dprotobuf_BUILD_LIBPROTOC=1",
            "-Dprotobuf_BUILD_LIBUPB=1",
            "-Dprotobuf_BUILD_PROTOBUF_BINARIES=1",
            "-Dprotobuf_BUILD_PROTOC_BINARIES=1",  # Default: 1
            f"-Dprotobuf_BUILD_SHARED_LIBS={self.option_Shared}",
            "-Dprotobuf_BUILD_TESTS=0",
            "-Dprotobuf_DISABLE_RTTI=0",
            "-Dprotobuf_INSTALL=1",
            "-Dprotobuf_JSONCPP_PROVIDER=package",  # BUILD_COMFORMANCE=1 の時に jsoncpp が必要
            "-Dprotobuf_MSVC_STATIC_RUNTIME=0",  # use MDd
            "-Dprotobuf_TEST_XML_OUTDIR=0",
            "-Dprotobuf_USE_UNITY_BUILD=0",
            "-Dutf8_range_ENABLE_INSTALL=1",
            "-Dutf8_range_ENABLE_TESTS=0",
            f"-Dprotobuf_WITH_ZLIB={self.option_WithZlib}",
        ]

        depBuilder = self.dep_abseil.generateBuilder(self)
        configArgs.append(f"-Dabsl_DIR={depBuilder.installDir}/lib/cmake/absl")

        if self.dep_zlib.isRequired(self):
            depBuilder = self.dep_zlib.generateBuilder(self)
            configArgs.append(f"-DZLIB_ROOT={depBuilder.installDir}")

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "protobuf_DIR": f"{self.installDir}/lib/cmake/protobuf"
        }
