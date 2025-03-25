from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 11, 0, 0): "E17ED95300118C1D8091764692A16061AE03F8554E3D76DA8276FD847D78B517",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    def build(self):
        self.download(
            "https://github.com/harfbuzz/harfbuzz/archive/refs/tags/"
            f"{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/harfbuzz-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("harfbuzz")
