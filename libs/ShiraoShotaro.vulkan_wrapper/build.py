from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    # 手元のクローンからそのまま使う
    signatures = {
        Version(0, 0, 0, 0): "",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_UseSpdlog = Option(bool, True, "Use spdlog for logging")
    option_SupportGLFWSurface = Option(bool, True, "Support GLFW surface")
    option_SupportWin32Surface = Option(bool, True, "Support Win32 surface")
    option_BuildTests = Option(bool, True, "Build tests")
    option_BuildDocs = Option(bool, True, "Build docs")

    # --- deps ---
    dep_spdlog = Dependency("gabime.spdlog", condition=lambda self: self.option_UseSpdlog.value)
    dep_glfw = Dependency("glfw.glfw", condition=lambda self: self.option_SupportGLFWSurface.value)
    dep_gtest = Dependency("google.googletest", condition=lambda self: self.option_BuildTests.value)

    def build(self):
        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DVKWP_SPDLOG_LOGGING={self.option_UseSpdlog}",
            f"-DVKWP_SUPPORT_GLFW_SURFACE={self.option_SupportGLFWSurface}",
            f"-DVKWP_SUPPORT_WIN32_SURFACE={self.option_SupportWin32Surface}",
            f"-DBUILD_TESTS={self.option_BuildTests}",
            f"-DBUILD_DOCS={self.option_BuildDocs}",
        ]

        srcPath = "S:/works/programming/vulkan_wrapper"
        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("vkwp")
