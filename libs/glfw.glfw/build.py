import os
from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 3, 4, 0): "a133ddc3d3c66143eba9035621db8e0bcf34dba1ee9514a9e23e96afd39fd57a",
        Version(0, 3, 3, 10): "5e4ae02dc7c9b084232824c2511679a7e0b0b09f2bae70191ad9703691368b58",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Shared = Option(bool, False, "Build shared")

    def build(self):
        if self.version.patch != 0:
            versionName = f"{self.version.major}.{self.version.minor}.{self.version.patch}"
        else:
            versionName = f"{self.version.major}.{self.version.minor}"

        zipFile = self.download(
            f"https://github.com/glfw/glfw/archive/refs/tags/{versionName}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/glfw-{versionName}"

        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            "-DUSE_MSVC_RUNTIME_LIBRARY_DLL=0",
            "-DGLFW_BUILD_DOCS=0",
            "-DGLFW_BUILD_EXAMPLES=0",
            "-DGLFW_BUILD_TEST=0",
            "-DGLFW_INSTALL=1",
            f"-DGLFW_BUILD_WIN32={os.name == 'nt'}"
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("glfw3")
