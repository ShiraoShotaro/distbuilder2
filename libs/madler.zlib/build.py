from distbuilder import BuilderBase, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 3, 1): "50b24b47bf19e1f35d2a21ff36d2a366638cdf958219a66f30ce0861201760e6",
    }

    versions = list(signatures.keys())

    def build(self):
        self.download(
            "https://github.com/madler/zlib/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/zlib-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DZLIB_BUILD_EXAMPLES=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs + [f"-DCMAKE_INSTALL_PREFIX={self.installDir}"])
        self.cmakeBuild("build", "Release")
        self.cmakeInstall("build", "Release")

        self.cmakeConfigure(srcPath, "build", configArgs + [f"-DCMAKE_INSTALL_PREFIX={self.installDir}"])
        self.cmakeBuild("build", "Debug")
        self.cmakeInstall("build", "Debug")

    def export(self, toolchain):
        toolchain.setDirpathVariable("ZLIB_ROOT", self.installDir, "Path to ZLIB root.")
