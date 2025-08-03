from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    # 手元のクローンからそのまま使う
    signatures = {
        Version(0, 0, 0, 0): "",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_BuildApps = Option(bool, False, "Build apps")
    option_BuildTests = Option(bool, False, "Build tests")

    # --- deps ---
    dep_spdlog = Dependency("gabime.spdlog")
    dep_vkwp = Dependency("ShiraoShotaro.vulkan_wrapper",
                          overrideOptions={"SupportGLFWSurface": True})
    dep_imath = Dependency("AcademySoftwareFoundation.Imath")
    dep_sockpp = Dependency("fpagliughi.sockpp")
    dep_json = Dependency("nlohmann.json")

    dep_gtest = Dependency("google.googletest", condition=lambda self: self.option_BuildTests.value)

    dep_glfw = Dependency("glfw.glfw", condition=lambda self: self.option_BuildApps.value)
    dep_zstd = Dependency("facebook.zstd", condition=lambda self: self.option_BuildApps.value)
    dep_cli = Dependency("CLIUtils.CLI11", condition=lambda self: self.option_BuildApps.value)

    def build(self):
        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_APPS={self.option_BuildApps}",
            f"-DBUILD_TESTS={self.option_BuildTests}",
        ]

        srcPath = "S:/works/programming/debug-vkimage-viewer"
        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("roah_dbgv")
