from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 1, 16, 0): "a9607c9215866bd425a725610c5e0f739eeb50887a57903df48891446ce6fb3c",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_BuildGmock = Option(bool, False, "Build gmock")

    def build(self):
        self.download(
            "https://github.com/google/googletest/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/googletest-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DINSTALL_GTEST=1",
            "-Dgtest_force_shared_crt=1",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            f"-DBUILD_GMOCK={self.option_BuildGmock}"
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("GTest")
