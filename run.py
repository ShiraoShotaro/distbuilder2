import os
import json
import distbuilder


def main(*libraryNames: str):
    class CwdScope:
        def __init__(self):
            self._cwd = None

        def __enter__(self, *_):
            self._cwd = os.getcwd()

        def __exit__(self, *_):
            if self._cwd is not None:
                os.chdir(self._cwd)

    go = distbuilder.GlobalOptions(forceDownload=False)
    for libraryName in libraryNames:
        builderCls, path = distbuilder.searchBuilderAndPath(libraryName)
        with CwdScope():
            os.chdir(os.path.dirname(path))
            builder = builderCls("1.5.7", {}, go)  # TODO: version, variant 指定できるように
            builder.build()


def configure(args):
    with open(args.filepath, mode="r", encoding="utf-8") as fp:
        jdict = json.load(fp)

    deps = dict()
    for dep, info in jdict.items():
        builderCls, path = distbuilder.searchBuilderAndPath(dep)
        print(f"Library {dep} found.")
        print(f"-- {path}")
        if "options" not in info:
            info["options"] = dict()
        options = info["options"]
        builder = builderCls(info["version"], jdict, distbuilder.GlobalOptions())
        for opt in builder.options:
            options[opt.key] = opt.value
        for libdep in builder.dependencies:
            if not libdep.isRequired(builder):
                continue
            depBuilderCls, versions, overrideOptions = libdep.resolve(builder)
            if libdep.libraryName not in deps:
                deps[libdep.libraryName] = (depBuilderCls, versions, overrideOptions)
            else:
                deps[libdep.libraryName][1].intersection_update(versions)

    # deps から version の固定
    for libdep, (depBuilderCls, versions, overrideOptions) in deps.items():
        if libdep in jdict:
            # 依存しているライブラリが既に指定されている
            # バージョンが合致するか調べる
            version = depBuilderCls.generateVersion(jdict[libdep]["version"])
            if version not in versions:
                # version 合致しない
                raise distbuilder.BuildError(
                    f"Dependency {libdep} version ({version}) is not suitable. (Requires: {versions})")
        elif len(versions) != 0:
            # 一番新しいバージョンを依存に追加する
            print(f"{libdep} available versions: {[str(v) for v in versions]}")
            version = sorted(list(versions), reverse=True)[0]
            depBuilder = depBuilderCls(version, {}, distbuilder.GlobalOptions())
            jdict[libdep] = {
                "version": str(version),
                "options": {opt.key: opt.value for opt in depBuilder.options}
            }
        else:
            raise distbuilder.BuildError("No library version is available.")
        # オプション上書き
        jdict[libdep]["options"].update(overrideOptions)

    # dep 含めた状態で exports を決定
    exports = dict()
    for dep, info in jdict.items():
        builderCls, path = distbuilder.searchBuilderAndPath(dep)
        builder = builderCls(info["version"], jdict, distbuilder.GlobalOptions())
        exports.update(builder.export(args.config))

    with open(args.filepath, mode="w", encoding="utf-8") as fp:
        json.dump(jdict, fp, ensure_ascii=False, indent=4)

    # cmake file 書き出し
    with open(f"{os.path.splitext(args.filepath)[0]}.cmake", mode="w", encoding="utf-8") as fp:
        fp.writelines([f"set({k} {v})\n" for k, v in exports.items()])


# TODO: 依存ライブラリに要求するオプションの validation をしないといけない
def build(args):
    class CwdScope:
        def __init__(self):
            self._cwd = None

        def __enter__(self, *_):
            self._cwd = os.getcwd()

        def __exit__(self, *_):
            if self._cwd is not None:
                os.chdir(self._cwd)

    globalOpt = distbuilder.GlobalOptions(
        cleanBuild=args.clean,
        forceDownload=args.forceDownload,
        createDirectory=True)

    with open(args.filepath, mode="r", encoding="utf-8") as fp:
        jdict = json.load(fp)

    builtLibs = set()
    buildLibs = dict()

    for lib in jdict.keys():
        builderCls, path = distbuilder.searchBuilderAndPath(lib)
        buildLibs[lib] = (builderCls(jdict[lib]["version"], jdict, globalOpt), path)

    while len(buildLibs) > 0:
        builtAny = False
        for lib, (builder, path) in buildLibs.copy().items():
            resolved = True
            for libdep in builder.dependencies:
                if libdep.isRequired(builder) and libdep.libraryName not in builtLibs:
                    resolved = False
                    break
            if not resolved:
                continue

            # build
            if not os.path.exists(builder.installDir) or len(os.listdir(builder.installDir)) == 0:
                with CwdScope():
                    print("PATH!!!", path)
                    os.chdir(os.path.dirname(path))
                    builder.prepare()
                    builder.build()
            else:
                builder.log("Cached. build skip.")
            del buildLibs[lib]
            builtLibs.add(lib)
            builtAny = True
        if builtAny is False:
            raise distbuilder.BuildError("Dependency error.")


def testBuild(args):
    globalOpt = distbuilder.GlobalOptions(
        cleanBuild=args.clean,
        forceDownload=args.forceDownload)
    builderCls, path = distbuilder.searchBuilderAndPath(args.libraryName)
    versions = builderCls.versions

    # args.option から options を作成
    options = dict()
    for opt in args.option:
        k, v = opt.split("=", 2)
        option: distbuilder.Option = getattr(builderCls, f"option_{k}")
        if option.type is not str:
            v = option.type(int(v))
        options[k] = v
        print(f"Override option: {k} = {v}")

    rootdir = os.path.join(distbuilder.Preference.get().buildRootDirectory, "testbuild")
    os.makedirs(rootdir, exist_ok=True)
    for version in versions:
        # TODO: options
        builder = builderCls(version, {}, globalOpt)
        args.filepath = os.path.join(rootdir, f"testbuild.{builder.libraryName}.{version}.json")
        with open(args.filepath, mode="w", encoding="utf-8") as fp:
            json.dump({
                builder.libraryName: {"version": str(version), "options": options}
            }, fp)
        configure(args)
    build(args)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # ライブラリ名を指定しない.
    # ビルド要求の py ファイルかなにかを要求する

    parser.add_argument("--preference", type=str, help="Path to preference file.", default=None)
    subp = parser.add_subparsers()
    subp_configure = subp.add_parser("configure", help="Configure dependencies")
    subp_configure.add_argument("--config", type=str, choices=["Release", "Debug"], required=True)
    subp_configure.add_argument("filepath", type=str, help="Path to deps json")
    subp_configure.set_defaults(handler=configure)
    subp_build = subp.add_parser("build", help="Build dependencies")
    subp_build.add_argument("filepath", type=str, help="Path to deps json")
    subp_build.add_argument("--config", type=str, choices=["Release", "Debug"], required=True)
    subp_build.add_argument("--clean", action="store_true", help="Clear build cache.")
    subp_build.add_argument("--forceDownload", action="store_true", help="Force (re)download.")
    subp_build.set_defaults(handler=build)
    subp_test = subp.add_parser("test", help="Building test.")
    subp_test.add_argument("libraryName", type=str)
    subp_test.add_argument("--clean", action="store_true", help="Clear build cache.")
    subp_test.add_argument("--forceDownload", action="store_true", help="Force (re)download.")
    subp_test.add_argument("--config", type=str, choices=["Release", "Debug"], required=True)
    subp_test.add_argument("-o", "--option", nargs="+", type=str, default=list())
    subp_test.set_defaults(handler=testBuild)

    args = parser.parse_args()
    preferencePath = args.preference
    if preferencePath is None:
        preferencePath = os.path.join(os.path.dirname(__file__), "preference.toml")
    distbuilder.Preference.load(preferencePath)

    args.handler(args)
