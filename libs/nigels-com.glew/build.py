import os
from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 2, 2, 0): "a9046a913774395a095edcc0b0ac2d81c3aacca61787b39839b941e9be14e0d4",
        Version(0, 2, 3, 0): "b261a06dfc8b970e0a1974488530e58dd2390acf68acb05b45235cd6fb17a086",
        Version(0, 2, 3, 1): "09e0083ae46930aba9b53e72c92ee1a557e24ed393526fec26cb0ebabd834720",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    def build(self):
        zipFile = self.download(
            "https://github.com/nigels-com/glew/releases/download"
            f"/glew-{self.version.major}.{self.version.minor}.{self.version.patch}"
            f"/glew-{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/glew-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DBUILD_UTILS=OFF",
            "-DBUILD_FRAMEWORK=OFF",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
        ]

        for c in ["Debug", "Release"]:
            self.cmakeConfigure(os.path.join(srcPath, "build", "cmake"), f"build/{c}",
                                configArgs + [f"-DCMAKE_BUILD_TYPE={c}"])
            self.cmakeBuildAndInstall(f"build/{c}", c)

    def export(self, toolchain):
        toolchain.setDir("GLEW", "lib/cmake/glew")
