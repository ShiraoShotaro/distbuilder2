from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 0, 20250127, 0): "f470da4226a532560e9ee69868da3598d9d37dc00408a56db83e2fd19e3e2ae6",
        Version(0, 0, 20250814, 1): "7a56c409044fe02851302fba09fd00c9e06bd8160278f88e51122c76b44b6c00",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_BuildMonilithicShared = Option(bool, True, "Build shared")
    option_CXXStandard = Option(str, "20", "Use CXX Standard")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/abseil/abseil-cpp/archive/refs/tags/"
            f"{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/abseil-cpp-{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DCMAKE_CXX_STANDARD={self.option_CXXStandard.value}",
            "-DBUILD_TESTING=0",
            f"-DABSL_BUILD_MONOLITHIC_SHARED_LIBS={self.option_BuildMonilithicShared}",
            "-DABSL_BUILD_TESTING=0",
            "-DABSL_BUILD_TEST_HELPERS=0",
            "-DABSL_ENABLE_INSTALL=1",
            "-DABSL_MSVC_STATIC_RUNTIME=0",  # Use MD
            "-DABSL_USE_SYSTEM_INCLUDES=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("absl")
