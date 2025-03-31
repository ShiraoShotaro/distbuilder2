from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 2021, 13, 0): "f8dba2602f61804938d40c24d8f9b1f1cc093cd003b24901d5c3cc75f3dbb952",
        Version(0, 2021, 12, 0): "fe6ca052b5bdd2c6e0616b360c9b0dcbcc46e01bbd0aa8fd0517c17fc58931db",
    }

    versions = list(signatures.keys())

    # --- options ---
    # option_Shared = Option(bool, False, "Build shared")
    option_Strict = Option(bool, False, "Strict")

    # --- deps ---
    # dep_zlib = Dependency("madler.zlib", condition=lambda self: True)

    def build(self):
        zipFile = self.download(
            "https://github.com/uxlfoundation/oneTBB/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/oneTBB-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DTBB_TEST=0",
            "-DTBB_TEST_SPEC=0",
            "-DTBB_EXAMPLES=0",
            "-DTBB_FUZZ_TESTING=0",
            "-DTBB_INSTALL=1",
            f"-DTBB_STRICT={self.option_Strict}",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("TBB")
