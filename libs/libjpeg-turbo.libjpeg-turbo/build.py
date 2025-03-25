from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 3, 1, 0): "2ddfaadf8b660050ff066a03833416bf8500624f014877b80eff16e799f68e81",
    }

    versions = list(signatures.keys())

    # --- options ---
    # option_Static = Option(bool, True, "Build static")
    option_Shared = Option(bool, False, "Build shared")

    def build(self):
        self.download(
            "https://github.com/libjpeg-turbo/libjpeg-turbo/archive/refs/tags/"
            f"{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/libjpeg-turbo-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DENABLE_SHARED={self.option_Shared}",
            f"-DENABLE_STATIC={not self.option_Shared.value}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("libjpeg-turbo")
        toolchain.setDirpathVariable("JPEG_ROOT", self.installDir, "Path to JPEG root.")
