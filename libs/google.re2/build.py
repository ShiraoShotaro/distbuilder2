from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 2024, 7, 2): "a835fe55fbdcd8e80f38584ab22d0840662c67f2feb36bd679402da9641dc71e",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    option_BuildFramework = Option(bool, False, "Build framework")
    option_UseICU = Option(bool, False, "Use ICU")

    # --- deps ---
    dep_abseil = Dependency("abseil.abseil-cpp")

    def build(self):
        self.download(
            "https://github.com/google/re2/archive/refs/tags/"
            f"{self.version.major}-{self.version.minor:02d}-{self.version.patch:02d}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/re2-{self.version.major}-{self.version.minor:02d}-{self.version.patch:02d}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            "-DBUILD_TESTING=0",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            f"-DRE2_BUILD_FRAMEWORK={self.option_BuildFramework}",
            "-DRE2_BUILD_TESTING=0",
            f"-DRE2_USE_ICU={self.option_UseICU}",
        ]

        depBuilder = self.dep_abseil.generateBuilder(self)
        configArgs.append(f"-Dabsl_DIR={depBuilder.installDir}/lib/cmake/absl")

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "re2_DIR": f"{self.installDir}/lib/cmake/re2"
        }
