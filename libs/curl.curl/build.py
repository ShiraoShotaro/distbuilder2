from distbuilder import BuilderBase, Option, Dependency, Version


class Builder(BuilderBase):

    signatures = {
        Version(0, 8, 19, 0): "c2842525900529f866ac50ccb6dc175ed317fa1025b439dcf84d089100effdb9",
    }

    versions = list(signatures.keys())

    # --- options ---
    option_BuildCurlExe = Option(bool, False, "Build curl executable")
    option_Shared = Option(bool, False, "Build shared")
    option_Static = Option(bool, True, "Build static")
    option_EnableAres = Option(bool, False, "Enable c-ares")
    option_EnableUnicode = Option(bool, True, "Enable Unicode support")
    option_EnableSSL = Option(bool, False, "Enable SSL support")
    option_UseBoringSSL = Option(bool, False, "Enable BoringSSL support")
    option_UseLibPSL = Option(bool, False, "Enable libpsl support")
    option_UseLibSSL2 = Option(bool, False, "Enable libssl2 support")
    option_UseNGHTTP2 = Option(bool, False, "Enable nghttp2 support")
    option_UseLibidn2 = Option(bool, False, "Enable libidn2 support") 

    # --- deps ---
    dep_cares = Dependency("c-ares.c-ares", condition=lambda self: self.option_EnableAres.value)
    dep_boringssl = Dependency(
        "google.boringssl", 
        condition=lambda self: self.option_UseBoringSSL.value and self.option_EnableSSL.value)
    dep_zlib = Dependency("madler.zlib")
    dep_zstd = Dependency("facebook.zstd")

    def build(self):
        zipFile = self.download(
            "https://github.com/curl/curl/archive/refs/tags/"
            f"curl-{self.version.major}_{self.version.minor}_{self.version.patch}.zip",
            Builder.signatures[self.version])
        self.unzip(zipFile, "src")

        srcPath = f"src/curl-curl-{self.version.major}_{self.version.minor}_{self.version.patch}"

        # zstd は FindZstd によるもので, CONFIG モードでは見つけてくれなかったので CMAKE_PREFIX_PATH に追加している
        configArgs = [
            "-DCMAKE_DEBUG_POSTFIX=d",
            f"-DBUILD_CURL_EXE={self.option_BuildCurlExe}",
            f"-DBUILD_SHARED_LIBS={self.option_Shared}",
            f"-DBUILD_STATIC_LIBS={self.option_Static}",
            f"-DBUILD_STATIC_CURL={self.option_Static}",
            f"-DENABLE_ARES={self.option_EnableAres}",
            f"-DENABLE_UNICODE={self.option_EnableUnicode}",
            f"-DCURL_ENABLE_SSL={self.option_EnableSSL}",
            f"-DCURL_USE_LIBPSL={self.option_UseLibPSL}",
            f"-DCURL_USE_LIBSSH2={self.option_UseLibSSL2}",
            f"-DUSE_NGHTTP2={self.option_UseNGHTTP2}",
            f"-DUSE_LIBIDN2={self.option_UseLibidn2}",
            f"-DCMAKE_PREFIX_PATH={self.dep_zstd.builder.installDir}",
            "-DCURL_DISABLE_INSTALL=OFF",
            "-DCURL_BUILD_EVERYTHING=OFF",
            "-DENABLE_DEBUG=OFF",
        ]

        self.cmakeConfigure(srcPath, "build", configArgs)
        self.cmakeBuildAndInstall("build", "Debug")
        self.cmakeBuildAndInstall("build", "Release")

    def export(self, toolchain):
        toolchain.setDir("CURL")
