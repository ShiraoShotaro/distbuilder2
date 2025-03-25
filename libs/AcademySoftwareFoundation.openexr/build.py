from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 3, 3, 2): "1efca7246bd4c4429fb4120e99358a04559360b6fa61a4c89040d8f35a87373e",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_EnableThreading = Option(bool, True, "Enable threading")

    # --- deps ---
    dep_libdeflate = Dependency("ebiggers.libdeflate",
                                overrideOptions={"ZlibSupport": True})
    dep_Imath = Dependency("AcademySoftwareFoundation.Imath")

    def build(self):
        self.download(
            "https://github.com/AcademySoftwareFoundation/openexr/archive/refs/tags/"
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/openexr-{self.version.major}.{self.version.minor}.{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DPYTHON=0",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            "-DBUILD_TESTING=0",
            "-DBUILD_WEBSITE=0",
            "-DOPENEXR_BUILD_EXAMPLES=0",
            "-DOPENEXR_BUILD_LIBS=1",
            "-DOPENEXR_BUILD_PYTHON=0",
            "-DOPENEXR_BUILD_TOOLS=0",
            f"-DOPENEXR_ENABLE_THREADING={self.option_EnableThreading}",
            "-DOPENEXR_INSTALL=1",
            "-DOPENEXR_INSTALL_DOCS=0",
            "-DOPENEXR_INSTALL_PKG_CONFIG=0",
            "-DOPENEXR_INSTALL_TOOLS=0",
            "-DOPENEXR_TEST_LIBRARIES=0",
            "-DOPENEXR_TEST_PYTHON=0",
            "-DOPENEXR_TEST_TOOLS=0",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("OpenEXR")
