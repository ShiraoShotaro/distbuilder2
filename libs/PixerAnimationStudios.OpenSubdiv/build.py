from distbuilder import BuilderBase, Option, Dependency, Version
import platform


class Builder(BuilderBase):

    signatures = {
        # CY2023
        Version(0, 3, 5, 1): "6d11dd49142383ce22e8b520a9808f14615037574abbb803bcafc0314a9d11a8",

        # CY2025, CY2024
        Version(0, 3, 6, 0): "453b8a5ad90a9f9217c300a18b0cf7e32b24189a76115229aea3c87388208215",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")
    # option_WithGLFW = Option(bool, False, "With GLFW")
    option_EnableCUDA = Option(bool, False, "Enable CUDA backend")

    # --- deps ---
    # dep_glfw = Dependency("glfw.glfw", condition=lambda self: self.option_WithGLFW.value)

    def build(self):
        zipFile = self.download(
            "https://github.com/PixarAnimationStudios/OpenSubdiv/archive/refs/tags/"
            f"v{self.version.major}_{self.version.minor}_{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/OpenSubdiv-{self.version.major}_{self.version.minor}_{self.version.patch}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            "-DNO_EXAMPLES=1",
            "-DNO_TUTORIALS=1",
            "-DNO_REGRESSION=1",
            "-DNO_DOC=1",
            "-DNO_OMP=1",
            f"-DNO_CUDA={not self.option_EnableCUDA.value}",
            "-DNO_OPENCL=1",
            "-DNO_DX=1",
            "-DNO_TESTS=1",
            "-DNO_GLEW=1",
            # f"-DNO_GLFW={not self.option_WithGLFW.value}",
            "-DNO_GLFW=0",
            "-DNO_PTEX=1",
            "-DNO_TBB=1",
        ]

        # Use Metal for macOS and all Apple embedded systems.
        if platform.system() == "Darwin":
            configArgs.append('-DNO_OPENGL=1')

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("OpenSubdiv")
