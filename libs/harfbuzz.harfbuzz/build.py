from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 11, 0, 0): "e17ed95300118c1d8091764692a16061ae03f8554e3d76da8276fd847d78b517",
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

        # Apply patch
        # -- INSTALL_INCLUDEDIR が定義されてなくて include dir がおかしくなる
        self.applyPatch(
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/CMakeLists.txt.patch",
            srcPath)

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("harfbuzz")
