from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "1b08c6586ca898b569234074cc808c7674f30105137914cbe144bbbe4e06a5ae",
        Version(0, 1, 0, 1): "378caa434c2911c7de6ebf83b2d64133243dbc6a8479a4647e7b79b09c50a26a",
        Version(0, 1, 0, 2): "14d2ff2dbfc7988d2b0495ac56a34ed6a791ddc731822b8eea742c422dc0be16",
        Version(0, 1, 0, 3): "31007ea2f01b5ef3f0d6e37cca1ab7ccd22df34d97e52117046b05d93621e324",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_BuildRoahAssert = Option(bool, True, "Build RoahAssert")
    option_BuildRoahLogger = Option(bool, True, "Build RoahLogger")
    option_BuildRoahConfig = Option(bool, True, "Build RoahConfig")

    # --- deps ---
    dep_spdlog = Dependency("gabime.spdlog", condition=lambda self: self.option_BuildRoahLogger)
    dep_toml11 = Dependency("ToruNiina.toml11", condition=lambda self: self.option_BuildRoahConfig)

    def build(self):
        zipFile = self.download(
            "https://github.com/WhiteAtelier/roah-lib/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/roah-lib-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_ROAH_ASSERT={self.option_BuildRoahAssert}",
            f"-DBUILD_ROAH_LOGGER={self.option_BuildRoahLogger}",
            f"-DBUILD_ROAH_CONFIG={self.option_BuildRoahConfig}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("libroah")
