from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 38, 10): "ed6852794350a3026cf1198cfe9af81097272d952de8e81b8ebc21ebd53a2275",
        Version(0, 1, 39, 3): "c0444b1e6e9d55c2ad8c997524b8f561c8d27cd374730fe6233a2573b6af2358",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_Monolithic = Option(bool, False, "Build shared")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/AcademySoftwareFoundation/MaterialX/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/MaterialX-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DMATERIALX_BUILD_GEN_MSL=1",
            "-DMATERIALX_BUILD_GEN_GLSL=1",
            "-DMATERIALX_BUILD_IOS=0",
            "-DMATERIALX_BUILD_DOCS=0",
            "-DMATERIALX_BUILD_OIIO=0",
            f"-DMATERIALX_BUILD_SHARED_LIBS={self.option_Shared}",
            f"-DMATERIALX_BUILD_MONOLITHIC={self.option_Monolithic}",
            "-DMATERIALX_BUILD_GRAPH_EDITOR=0",
            "-DMATERIALX_BUILD_PYTHON=0",
            "-DMATERIALX_BUILD_TESTS=0",
            "-DMATERIALX_BUILD_VIEWER=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("MaterialX")
