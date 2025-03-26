from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "bf4798b9635a3b34e40a30cb54b5bc185807945da8839e041ab8d91f268d26b1",
    }

    versions = list(signatures.keys())

    # --- deps ---
    dep_abseil = Dependency("abseil.abseil-cpp")

    def build(self):
        zipFile = self.download(
            "https://github.com/protocolbuffers/utf8_range/archive/1d1ea7e3fedf482d4a12b473c1ed25fe0f371a45.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = "src/utf8_range-1d1ea7e3fedf482d4a12b473c1ed25fe0f371a45"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-Dutf8_range_ENABLE_INSTALL=1",
            "-Dutf8_range_ENABLE_TESTS=0",
        ]
        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("utf8_range")
