from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        # Version(0, 1, 71, 0): "9313c3f8f4dd3341597f152d506a50caf571fe40f886e24ea9078891990df285",
        Version(0, 1, 68, 2): "2a17adb0d23768413ca85990dbf800a600863d272fcc37a9f67f3b5e34ae9174",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_UseStaticZlib = Option(bool, True, "Use static zlib.")

    # --- deps ---
    dep_abseil = Dependency("abseil.abseil-cpp")
    dep_zlib = Dependency("madler.zlib")
    dep_cares = Dependency("c-ares.c-ares")
    dep_protobuf = Dependency("protocolbuffers.protobuf")
    dep_utf8 = Dependency("protocolbuffers.utf8_range")
    dep_re2 = Dependency("google.re2")
    dep_ssl = Dependency("google.boringssl")

    def build(self):
        self.download(
            "https://github.com/grpc/grpc/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/grpc-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DgRPC_ABSL_PROVIDER=package",
            "-DgRPC_BUILD_CODEGEN=1",
            "-DgRPC_BUILD_GRPCPP_OTEL_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_CPP_PLUGIN=1",
            "-DgRPC_BUILD_GRPC_CSHARP_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_NODE_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_PHP_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_PYTHON_PLUGIN=0",
            "-DgRPC_BUILD_GRPC_RUBY_PLUGIN=0",
            "-DgRPC_BUILD_MSVC_MP_COUNT=0",
            "-DgRPC_BUILD_TESTS=0",
            "-DgRPC_CARES_PROVIDER=package",
            "-DgRPC_DOWNLOAD_ARCHIVES=0",
            "-DgRPC_INSTALL=1",
            "-DgRPC_MSVC_STATIC_RUNTIME=0",  # Use MD
            "-DgRPC_PROTOBUF_PROVIDER=package",
            # f"-DProtobuf_DIR={self.dep_protobuf.generateBuilder(self).installDir}/lib/cmake/protobuf",
            "-DgRPC_RE2_PROVIDER=package",
            "-DgRPC_SSL_PROVIDER=package",
            "-DgRPC_USE_PROTO_LITE=0",
            "-DgRPC_ZLIB_PROVIDER=package",
            f"-DZLIB_USE_STATIC_LIBS={self.option_UseStaticZlib}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("gRPC", "lib/cmake/grpc")
