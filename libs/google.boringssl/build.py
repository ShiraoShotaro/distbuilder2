from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 0, 20241209, 0): "8c749098b9bfd010dd7d6c6d23325a64ad97fbd274b3bc5d985e8000d2dd14be",
        Version(0, 0, 20250311, 0): "211412789496232a64d80b432c29cac13717d5f22ea89424f1130f799226e20d",
    }

    versions = list(signatures.keys())

    def build(self):
        zipFile = self.download(
            "https://github.com/google/boringssl/archive/refs/tags/"
            f"{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/boringssl-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("OpenSSL")
        toolchain.setDirpathVariable("OPENSSL_ROOT_DIR", self.installDir, "Path to OpenSSL Root")
