from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 0, 0): "d144b3dcc7e9f031a9205395deb334b0b9681e1e7db61c066cca22ec2650a77b",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_Static = Option(bool, True, "Build static")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/fpagliughi/sockpp/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/sockpp-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DSOCKPP_BUILD_CAN=0",
            "-DSOCKPP_BUILD_DOCUMENTATION=0",
            "-DSOCKPP_BUILD_EXAMPLES=0",
            f"-DSOCKPP_BUILD_SHARED={self.option_Shared}",
            f"-DSOCKPP_BUILD_STATIC={self.option_Static}",
            "-DSOCKPP_BUILD_TESTS=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("sockpp")
