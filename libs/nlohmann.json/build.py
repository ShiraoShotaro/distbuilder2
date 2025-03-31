from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 3, 11, 3): "04022b05d806eb5ff73023c280b68697d12b93e1b7267a0b22a1a39ec7578069",
    }

    versions = list(signatures.keys())

    def build(self):
        zipFile = self.download(
            "https://github.com/nlohmann/json/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/json-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DJSON_BuildTests=0",
            "-DJSON_CI=0",
            "-DJSON_DisableEnumSerialization=0",
            "-DJSON_GlobalUDLs=0",
            "-DJSON_ImplicitConversions=1",
            "-DJSON_Install=1",
            "-DJSON_LegacyDiscardedValueComparison=0",
            "-DJSON_MultipleHeaders=1",
            "-DJSON_SystemInclude=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("nlohmann_json", "share/cmake/{packageName}")
