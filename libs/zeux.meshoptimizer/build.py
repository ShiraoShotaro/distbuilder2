from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 0, 24, 0): "beddcad535123bfcc8b0183f2d76b324b5c71dba733ccfd7f985dc7855f18567",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/zeux/meshoptimizer/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/meshoptimizer-{self.version.major}.{self.version.minor}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DMESHOPT_BUILD_DEMO=0",
            "-DMESHOPT_BUILD_GLTFPACK=0",
            f"-DMESHOPT_BUILD_SHARED_LIBS={self.option_Shared}",
            "-DMESHOPT_INSTALL=1",
            "-DMESHOPT_STABLE_EXPORTS=0",
            "-DMESHOPT_WERROR=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("meshoptimizer")
