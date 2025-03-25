from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 2, 13, 3): "6B40AF9EA284135D6A5C905340D43B5003C799810B5804FFA8A2CF91EBE2CFF5",
    }

    recipeVersion = 0
    versions = list(signatures.keys())

    # --- options ---
    # option_Shared = Option(bool, False, "Build shared")
    option_WithHarfBuzz = Option(bool, False, "Build with halfbuzz")
    option_WithPNG = Option(bool, False, "Build with png")
    option_WithZlib = Option(bool, False, "Build with zlib")

    # --- deps ---
    dep_harfbuzz = Dependency("harfbuzz.harfbuzz",
                              condition=lambda self: self.option_WithHarfBuzz.value)
    dep_png = Dependency("pnggroup.libpng",
                         condition=lambda self: self.option_WithPNG.value)
    dep_zlib = Dependency("madler.zlib",
                          condition=lambda self: self.option_WithZlib.value)

    def build(self):
        self.download(
            "https://gitlab.freedesktop.org/freetype/freetype/-/archive/"
            f"VER-{self.version.major}-{self.version.minor}-{self.version.patch}/"
            f"freetype-VER-{self.version.major}-{self.version.minor}-{self.version.patch}.zip",
            "src.zip",
            signature=Builder.signatures[self.version])
        self.unzip("src.zip", "src")

        srcPath = f"src/freetype-VER-{self.version.major}-{self.version.minor}-{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
        ]

        if self.dep_harfbuzz.isRequired(self):
            configArgs.append("-DFT_REQUIRE_HARFBUZZ=1")
            configArgs.append(
                f"-Dharfbuzz_DIR={self.dep_harfbuzz.generateBuilder(self).installDir}/lib/cmake/harfbuzz")
        if self.dep_png.isRequired(self):
            configArgs.append("-DFT_REQUIRE_PNG=1")
            configArgs.append(
                f"-DPNG_DIR={self.dep_png.generateBuilder(self).installDir}/lib/cmake/PNG")
        if self.dep_zlib.isRequired(self):
            configArgs.append("-DFT_REQUIRE_ZLIB=1")
            configArgs.append(
                f"-DZLIB_ROOT={self.dep_zlib.generateBuilder(self).installDir}")

        # Apply patch
        self.applyPatch(
            f"v{self.version.major}.{self.version.minor}.{self.version.patch}/CMakeLists.txt.patch",
            srcPath)

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, config: str):
        return {
            "freetype_DIR": f"{self.installDir}/lib/cmake/freetype"
        }
