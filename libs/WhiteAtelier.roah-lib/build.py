from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "1b08c6586ca898b569234074cc808c7674f30105137914cbe144bbbe4e06a5ae",
        Version(0, 1, 0, 1): "378caa434c2911c7de6ebf83b2d64133243dbc6a8479a4647e7b79b09c50a26a",
        Version(0, 1, 0, 2): "14d2ff2dbfc7988d2b0495ac56a34ed6a791ddc731822b8eea742c422dc0be16",
        Version(0, 1, 0, 3): "31007ea2f01b5ef3f0d6e37cca1ab7ccd22df34d97e52117046b05d93621e324",
        Version(0, 1, 1, 0): "c48f802460cfa272c442f6b9fe4ad9373812101fada5f4b91d670921a4b04535",
        Version(0, 1, 2, 0): "b4bc41f730bf08a3f7de1232eb1971cb7c794d1b192019699838dd3d5f3f6384",
        Version(0, 1, 3, 0): "59e981bf41af64323f094ba324a66be8bf399c3e8d97a9ff6deb30676aa3a699",
        Version(0, 1, 4, 0): "622a5c2ec6720e0a315d5b1940bf7d13893c6f28b420a1dd14c2c83a48e44e6f",
        Version(0, 1, 5, 0): "23f4ce974502d7c0deb998529f3af9466b0f3d0c111aff7bc0ee32ba91a54496",
        Version(0, 1, 5, 1): "736ac240dc71bd030b0ea3c3897a841d88593179448166c432570f790d709ec7",
        Version(0, 1, 6, 0): "99fbab5a355f56262ce710522e84d4cd1e0b0508074226965a3b7a648582369a",
        Version(0, 1, 6, 1): "4fd301463f3786b88106ddc8d4b0ef9ad0bb2161811e56baec25c526f2a6720a",
        Version(0, 1, 7, 0): "6d6d68916494796dc5f3c5182951cc8d4892e5a44ce3e92d8c1381ced163abf9",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_BuildRoahAssert = Option(bool, True, "Build RoahAssert")
    option_BuildRoahLogger = Option(bool, True, "Build RoahLogger")
    option_BuildRoahString = Option(bool, True, "Build RoahString")
    option_BuildRoahConfig = Option(bool, True, "Build RoahConfig")
    option_BuildRoahURLParser = Option(bool, True, "Build RoahURLParser")
    option_BuildRoahSubprocess = Option(bool, True, "Build RoahSubprocess")
    
    option_BuildRoahLoggingWebViewerApp = Option(bool, True, "Build RoahLoggingWebViewerApp")

    # --- deps ---
    dep_spdlog = Dependency("gabime.spdlog", condition=lambda self: self.option_BuildRoahLogger)
    dep_toml11 = Dependency("ToruNiina.toml11", condition=lambda self: self.option_BuildRoahConfig)
    dep_ixwebsocket = Dependency("machinezone.IXWebSocket", condition=lambda self: self.option_BuildRoahLoggingWebViewerApp)
    dep_nlohmann_json = Dependency("nlohmann.json", condition=lambda self: self.option_BuildRoahLoggingWebViewerApp)
    dep_cli11 = Dependency("CLIUtils.CLI11", condition=lambda self: self.option_BuildRoahLoggingWebViewerApp)

    def build(self):
        if (self.version.major == 0):
            srcPath = "W:/works/programming/roah-lib"
        else:
            zipFile = self.download(
                "https://github.com/WhiteAtelier/roah-lib/archive/refs/tags/"
                f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
                Builder.signatures[self.version])
            self.unzip(zipFile, "src")

            srcPath = f"src/roah-lib-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_ROAH_ASSERT={self.option_BuildRoahAssert}",
            f"-DBUILD_ROAH_STRING={self.option_BuildRoahString}",
            f"-DBUILD_ROAH_SUBPROCESS={self.option_BuildRoahSubprocess}",
            f"-DBUILD_ROAH_LOGGER={self.option_BuildRoahLogger}",
            f"-DBUILD_ROAH_CONFIG={self.option_BuildRoahConfig}",
            f"-DBUILD_ROAH_URL_PARSER={self.option_BuildRoahURLParser}",
            f"-DBUILD_ROAH_LOGGING_WEB_VIEWER_APP={self.option_BuildRoahLoggingWebViewerApp}"
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("libroah")
