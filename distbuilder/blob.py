import os
from .preference import Preference
from .errors import BuildError


class Blob:
    def __init__(self, builder):
        from .builder import BuilderBase
        self._builder: BuilderBase = builder
        self._blobRoot = os.path.join(Preference.get().buildRootDirectory, "_blob")

    def _createDirectory(self, signature: str) -> str:
        signature = signature.lower()
        dirpath = os.path.join(self._blobRoot, signature[0:2], signature[2:4])
        os.makedirs(dirpath, exist_ok=True)
        return dirpath

    def fetch(self, url: str, signature: str, *, ext: str = None) -> str:
        signature = signature.lower()
        dirpath = self._createDirectory(signature)
        if ext is None:
            ext = os.path.splitext(url)[1]
        filepath = os.path.join(dirpath, f"{signature}{ext}")
        if self._builder.globalOptions.forceDownload:
            if os.path.exists(filepath):
                self._builder.log("FORCE (re)downloading. Erasing cached file...")
                self._builder.log(f"-- Path: {filepath}")
                os.remove(filepath)

        if not os.path.exists(filepath):
            # download してくる
            import urllib.error
            import urllib.request
            self._builder.log("Downloading...")
            self._builder.log(f"-- URL: {url}")
            self._builder.log(f"-- Destination: {filepath}")
            try:
                urllib.request.urlretrieve(url, filepath)
            except urllib.error.HTTPError as e:
                raise BuildError(f"Failed to download source. {e}")
        else:
            self._builder.log("Cached file is available. Skip downloading.")

        # signature チェック
        try:
            self._builder.checkSignature(filepath, signature,
                                         signatureAlgorithm="sha-256")
        except BuildError as e:
            # signature 不一致, ファイルを消しておく
            os.remove(filepath)
            raise e

        return filepath
