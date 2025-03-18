from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "bf4798b9635a3b34e40a30cb54b5bc185807945da8839e041ab8d91f268d26b1",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- deps ---
    dep_abseil = Dependency("abseil.abseil-cpp",)

    def build(self):
        self.download(
            "https://github.com/protocolbuffers/utf8_range/archive/1d1ea7e3fedf482d4a12b473c1ed25fe0f371a45.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = "src/utf8_range-1d1ea7e3fedf482d4a12b473c1ed25fe0f371a45"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-Dutf8_range_ENABLE_INSTALL=1",
            "-Dutf8_range_ENABLE_TESTS=0",
        ]

        depBuilder = self.dep_abseil.generateBuilder(self)
        configArgs.append(f"-Dabsl_DIR={depBuilder.installDir}/lib/cmake/absl")

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "absl_DIR": f"{self.installDir}/lib/cmake/absl"
        }
