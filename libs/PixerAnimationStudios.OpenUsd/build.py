import platform
from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 25, 2, 1): "acd3f514a025c76a053db34f08974e583389e99331709d290b4864d4eca37c67",  # 25.02a
    }

    versions = list(signatures.keys())

    # --- options ---
    option_Monolithic = Option(bool, False, "Build monolithic")
    option_BuildUsdTools = Option(bool, True, "Build USD Tools")
    option_BuildImaging = Option(bool, True, "Build imaging components")
    option_BuildUsdImaging = Option(bool, True, "Build usdimaging components")
    option_EnableMaterialX = Option(bool, False, "Enable MaterialX support")
    option_EnableGL = Option(bool, True, "Enable GL support")
    option_EnableVulkan = Option(bool, False, "Enable Vulkan support")
    option_UseOneTBB = Option(bool, True, "Use OneTBB, or (legacy) TBB.")

    # --- deps ---
    # TBB/oneTBB: Always required.
    # dep_tbb = Dependency("madler.zlib", condition=lambda self: True)  # TODO:
    dep_oneTBB = Dependency("uxlfoundation.oneTBB",
                            condition=lambda self: self.option_UseOneTBB.value)

    # ZLIB
    # TODO: 将来的に必要になりそう.
    # dep_zlib = Dependency("madler.zlib")

    # OpenSubdiv
    dep_OpenSubdiv = Dependency("PixerAnimationStudios.OpenSubdiv",
                                condition=lambda s: s.option_BuildImaging.value,
                                overrideOptions={"Shared": True})

    # MaterialX
    dep_MaterialX = Dependency("AcademySoftwareFoundation.MaterialX",
                               condition=lambda s: s.option_EnableMaterialX.value,
                               overrideOptions={"Shared": True},
                               versionVariant="0",
                               versionMajor="1",
                               versionMinor="38")

    def build(self):
        versionStr = f"{self.version.major:02d}.{self.version.minor:02d}"
        if self.version.patch > 0:
            # "a" から順に
            versionStr += bytes([96 + self.version.patch]).decode()

        zipFile = self.download(
            "https://github.com/PixarAnimationStudios/OpenUSD/archive/refs/tags/"
            f"v{versionStr}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/OpenUSD-{versionStr}"

        for cfg in ["Debug", "Release"]:
            configArgs = [
                "-DCMAKE_DEBUG_POSTFIX=d",
                "-DPXR_BUILD_DOCUMENTATION=0",
                "-DPXR_BUILD_HTML_DOCUMENTATION=0",
                "-DPXR_BUILD_PYTHON_DOCUMENTATION=0",
                "-DPXR_BUILD_TESTS=0",
                "-DPXR_BUILD_EXAMPLES=0",
                "-DPXR_BUILD_TUTORIALS=0",
                f"-DPXR_BUILD_USD_TOOLS={self.option_BuildUsdTools}",
                "-DPXR_BUILD_USD_VALIDATION=1",
                "-DPXR_ENABLE_PYTHON_SUPPORT=0",

                f"-DPXR_ENABLE_GL_SUPPORT={self.option_EnableGL}",
                f"-DPXR_ENABLE_VULKAN_SUPPORT={self.option_EnableVulkan}",

                # Imaging
                f"-DPXR_BUILD_IMAGING={self.option_BuildImaging}",
                "-DPXR_ENABLE_PTEX_SUPPORT=0",  # TODO:
                "-DPXR_ENABLE_OPENVDB_SUPPORT=0",  # TODO:
                "-DPXR_BUILD_EMBREE_PLUGIN=0",  # TODO:
                "-DPXR_BUILD_PRMAN_PLUGIN=0",  # TODO:
                "-DPXR_BUILD_OPENIMAGEIO_PLUGIN=0",  # TODO:
                "-DPXR_BUILD_OPENCOLORIO_PLUGIN=0",  # TODO:

                # UsdImaging
                f"-DPXR_BUILD_USD_IMAGING={self.option_BuildUsdImaging}",
                "-DPXR_BUILD_USDVIEW=0",
                "-DPXR_BUILD_ALEMBIC_PLUGIN=0",  # TODO:
                "-DPXR_BUILD_DRACO_PLUGIN=0",
                f"-DPXR_ENABLE_MATERIALX_SUPPORT={self.option_EnableMaterialX}",
                "-DPXR_BUILD_MAYAPY_TESTS=0",
                "-DPXR_BUILD_ANIMX_TESTS=0",
            ]

            if platform.system() == "Windows":
                # Increase the precompiled header buffer limit.
                configArgs.append('-DCMAKE_CXX_FLAGS="/Zm150"')

            if self.option_Monolithic.value is True:
                configArgs.append("-DPXR_BUILD_MONOLITHIC=ON")
            else:
                configArgs.append("-DBUILD_SHARED_LIBS=ON")

            # ほんとに. installPrefix を指定しとかないといけないらしい.
            configArgs.append(f"-DCMAKE_INSTALL_PREFIX={self.installDir}")

            # Patch
            self.applyPatches(f"v{versionStr}", srcPath)

            self.cmakeConfigure(srcPath, "build", configArgs)
            self.cmakeBuildAndInstall("build", cfg)

    def export(self, toolchain):
        # root が pxrConfig.cmake のある場所.
        toolchain.setDir("pxr", "")
