from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 15, 0): "076f3b4d452b95433083bcc66d07f79addba2d3fcb2b9177abeb7367d47aefbb",
        Version(0, 1, 15, 1): "322c144e24abee5d0326ddbe5bbc0e0c39c85ac8c2cb3c90d10290a85428327a",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_UseFmt = Option(bool, False, "Use fmt lib.")
    option_DisableDefaultLogger = Option(bool, False, "Disable default logger")

    # --- deps ---
    dep_fmt = Dependency("fmtlib.fmt", condition=lambda self: self.option_UseFmt.value)

    def build(self):
        zipFile = self.download(
            "https://github.com/gabime/spdlog/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/spdlog-{self.version.major}.{self.version.minor}.{self.version.patch}"

        # HO = header only
        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DSPDLOG_BUILD_SHARED={self.option_Shared}",
            "-DSPDLOG_BUILD_EXAMPLE=0",
            "-DSPDLOG_BUILD_EXAMPLE_HO=0",
            "-DSPDLOG_BUILD_PIC=0",
            "-DSPDLOG_BUILD_TESTS=0",
            "-DSPDLOG_BUILD_TESTS_HO=0",
            "-DSPDLOG_BUILD_WARNINGS=0",
            f"-DSPDLOG_DISABLE_DEFAULT_LOGGER={self.option_DisableDefaultLogger}",
            "-DSPDLOG_INSTALL=1",
            "-DSPDLOG_MSVC_UTF8=1",
            "-DSPDLOG_FMT_EXTERNAL_HO=0",
            f"-DSPDLOG_USE_STD_FORMAT={not self.option_UseFmt.value}",
            f"-DSPDLOG_FMT_EXTERNAL={self.option_UseFmt.value}",
        ]

        self.executeBuildAndInstall(srcPath, configArgs)

    def export(self, toolchain):
        toolchain.setDir("spdlog")
