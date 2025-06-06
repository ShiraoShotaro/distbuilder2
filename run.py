import os
import json
import distbuilder
from typing import List, Dict


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


class _DependencyNode:
    def __init__(self, builder: distbuilder.BuilderBase):
        self.builder = builder
        self.libraryName = builder.libraryName
        self.used = False  # 依存の依存で実際に使われているか
        self.dirty = True  # ステートの更新が必要か
        self.availableVersions = builder.availableVersions
        self.flatten = False


def configure(depFilepath: str, buildDir: str, globalOpt: distbuilder.GlobalOptions):
    with open(depFilepath, mode="r", encoding="utf-8") as fp:
        jdict = json.load(fp)

    if not os.path.exists(buildDir):
        os.makedirs(buildDir)

    """
    option が決まると dependencies が決まる.
    dependencies が増えると, その中で再帰的に自分が含まれていて, option が制限される可能性がある
    そうすると option が変わり, dependencies が変化する可能性がある...

    builder がひとつのノードであり, option が変化した場合はその builder については再度 dirty となり再実行されるか.
    参照カウントか参照フラグも用意して, 最終的に使われたかどうかを調べるべきか.
    """

    # flatten libs
    roots: List[_DependencyNode] = list()
    depNodes: Dict[str, _DependencyNode] = dict()

    for lib, info in jdict.items():
        builderCls, _ = distbuilder.searchBuilderAndPath(lib)
        builder = builderCls(jdict, globalOpt)
        node = _DependencyNode(builder)
        roots.append(node)
        depNodes[builder.libraryName] = node

    def _traverse(node: _DependencyNode):
        # 今の options で必要な dependencies を列挙する.
        if node.dirty is True:
            node.dirty = False
            for dep in node.builder.dependencies:
                if not dep.isRequired(node.builder):
                    continue
                depNode = None
                if dep.libraryName not in depNodes:
                    builderCls = dep.searchBuilderClass()
                    builder = builderCls(jdict, globalOpt)
                    depNode = _DependencyNode(builder)
                    depNodes[dep.libraryName] = depNode
                else:
                    depNode = depNodes[dep.libraryName]

                # この depNode に対して, オプションの強制はあるか？
                overrideOptions = dep.overrideOptions
                if overrideOptions:
                    for option in depNode.builder.options:
                        if option.key in overrideOptions:
                            if option.hasValue() and option.value != overrideOptions[option.key]:
                                raise distbuilder.BuildError("Option value is conflict!!")
                            else:
                                option.setValue(overrideOptions[option.key])
                                depNode.dirty = True

                # この depNode に対して version の制約はあるか？
                newAvailableVersions = set()
                for aver in depNode.availableVersions:
                    if dep.isSuitableVersion(aver):
                        newAvailableVersions.add(aver)
                depNode.availableVersions = newAvailableVersions
                if len(depNode.availableVersions) == 0:
                    raise distbuilder.BuildError("No available version.")

                # 再帰呼び出し
                _traverse(depNode)

    for node in roots:
        _traverse(node)

    # 使用されているかチェック
    # 同時にバージョンも決定
    def _markAsUsedAndDesideVersion(node: _DependencyNode):
        node.used = True

        version = sorted(node.availableVersions, reverse=True)[0]
        node.builder.setVersion(version)

        for dep in node.builder.dependencies:
            if not dep.isRequired(node.builder):
                continue
            _markAsUsedAndDesideVersion(depNodes[dep.libraryName])

    for node in roots:
        _markAsUsedAndDesideVersion(node)

    # 使用されていない物を削除しつつ, Dependency に builder をセットする
    def _setBuilder(node: _DependencyNode):
        for dep in node.builder.dependencies:
            depNode = depNodes.get(dep.libraryName)
            if depNode is not None and depNode.used is True:
                dep._builder = depNode.builder
                _setBuilder(depNode)
            else:
                # 使っていない dependency には Empty を入れる.
                from distbuilder.builder import EmptyBuilder
                dep._builder = EmptyBuilder(jdict, globalOpt)

    for node in roots:
        _setBuilder(node)

    # 全ての依存が決定したはず.
    # json に dump してみる
    def _dump(j: dict, node: _DependencyNode):
        node.builder.updateHash()
        jj = dict(
            hash=node.builder.hash,
            hashData=node.builder.hashData,
            options={o.key: (o.value if o.hasValue() else None) for o in node.builder.options},
            dependencies=dict(),
        )
        for dep in node.builder.dependencies:
            depNode = depNodes.get(dep.libraryName)
            if depNode is not None:
                _dump(jj["dependencies"], depNode)
            else:
                jj["dependencies"][dep.libraryName] = "<Unused>"
        j[node.libraryName] = jj

    jobj = dict()
    for node in roots:
        _dump(jobj, node)

    outDependencyTreeDebugPath = os.path.join(buildDir, "dependency_tree_debug.json")
    with open(outDependencyTreeDebugPath, mode="w", encoding="utf-8") as fp:
        json.dump(jobj, fp, indent=2, ensure_ascii=False)
    print(f"[distbuilder] Export debug tree view: {outDependencyTreeDebugPath}")

    # 全て flatten し, ビルド順に並べる.
    jdeps = list()
    deps = list()

    def _flatten(node: _DependencyNode):
        if node.flatten is True:
            return
        for dep in node.builder.dependencies:
            if dep.libraryName in depNodes:
                _flatten(depNodes[dep.libraryName])

        node.builder.updateHash()
        conf = dict(
            libraryName=node.builder.libraryName,
            version=str(node.builder.version),
            hash=node.builder.hash,
            options={o.key: o.value for o in node.builder.options},
            deps={d.libraryName: d.hash for d in node.builder.dependencies}
        )
        jdeps.append(conf)
        deps.append(node.builder)
        node.flatten = True

    for lib in roots:
        _flatten(lib)

    # jdeps を json に書き出す.
    outDepsFilepath = os.path.join(buildDir, "deps.json")
    with open(outDepsFilepath, mode="w", encoding="utf-8") as fp:
        json.dump(jdeps, fp, indent=2, ensure_ascii=False)
    print(f"[distbuilder] Export deps: {outDepsFilepath}")

    # jdict を補完して書き戻す.
    for lib, info in jdict.items():
        depNode = depNodes[lib]
        info["version"] = str(depNode.builder.version)
        info["options"] = {o.key: (o.value if o.hasValue() else None) for o in depNode.builder.options}

    with open(depFilepath, mode="w", encoding="utf-8") as fp:
        json.dump(jdict, fp, indent=4, ensure_ascii=True)

    tc = distbuilder.Toolchain(globalOpt.config)
    for builder in deps:
        tc._builder = builder
        builder.export(tc)
        tc._builder = None

    outToolchainPath = os.path.join(buildDir, "toolchain.cmake")
    with open(outToolchainPath, mode="w", encoding="utf-8") as fp:
        fp.write(tc.dump())
    print(f"[distbuilder] Export toolchain: {outToolchainPath}")


# TODO: 依存ライブラリに要求するオプションの validation をしないといけない
def build(buildDir: str, globalOpt: distbuilder.GlobalOptions):
    depsFilepath = os.path.join(buildDir, "deps.json")
    with open(depsFilepath, mode="r", encoding="utf-8") as fp:
        jdeps = json.load(fp)

    # jdeps は list なので, libraryName をキーにした dict に直す
    jdict = {j["libraryName"]: j for j in jdeps}

    # 一旦先に全ての builder を作る.
    deps = dict()
    for lib in jdeps:
        builderCls, path = distbuilder.searchBuilderAndPath(lib["libraryName"])
        builder: distbuilder.BuilderBase = builderCls(jdict, globalOpt)
        deps[builder.libraryName] = builder

        for dep in builder.dependencies:
            if dep.isRequired(builder):
                # かならず依存先のライブラリは deps に居るはず.
                depBuilder = deps[dep.libraryName]
                dep._builder = depBuilder
            else:
                from distbuilder.builder import EmptyBuilder
                dep._builder = EmptyBuilder(jdict, globalOpt)

        assert builder.isResolved()
        builder.updateHash()
        if builder.hash != lib["hash"]:
            print(builder.libraryName, builder.hash, lib["hash"])
            print(builder.hashData)
            raise distbuilder.BuildError("Invalid hash.")

        # info.json, toolchain.cmake が作られてしまうので 2以下
        if os.path.exists(builder.installDir) is False or len(os.listdir(builder.installDir)) <= 2:
            builder._executeBuildSequence()
        else:
            builder.log("Build skip.")


def testBuild(args):
    configureGlobalOpt = distbuilder.GlobalOptions(
        ignoreScriptVersion=args.ignoreScriptVersion)
    buildGlobalOpt = distbuilder.GlobalOptions(
        createDirectory=True,
        cleanBuild=args.cleanAll,
        forceDownload=args.forceDownload,
        unzipAndOverwrite=not args.no_unzipOverwrite,
        ignoreScriptVersion=args.ignoreScriptVersion,
        configs=args.config)

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
        libraryName_tmp = builderCls.__module__.__name__
        # TODO: options
        builder = builderCls({libraryName_tmp: {"version": version}}, distbuilder.GlobalOptions())
        filepath = os.path.join(rootdir, f"testbuild.{builder.libraryName}.{version}.json")
        with open(filepath, mode="w", encoding="utf-8") as fp:
            json.dump({
                builder.libraryName: {"version": str(version), "options": options}
            }, fp)
        # TODO:
        configure(filepath, rootdir, configureGlobalOpt)
        build(rootdir, buildGlobalOpt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # ライブラリ名を指定しない.
    # ビルド要求の py ファイルかなにかを要求する

    def _configure(args):
        configure(args.filepath, args.buildDir, distbuilder.GlobalOptions())

    def _build(args):
        globalOpt = distbuilder.GlobalOptions(
            cleanBuild=args.cleanAll,
            forceDownload=args.forceDownload,
            createDirectory=True,
            unzipAndOverwrite=not args.no_unzipOverwrite,
            configs=args.config)
        build(args.buildDir, globalOpt)

    parser.add_argument("--preference", type=str, help="Path to preference file.", default=None)
    subp = parser.add_subparsers()
    subp_configure = subp.add_parser("configure", help="Configure dependencies")
    subp_configure.add_argument("-B", "--buildDir", type=str, help="Path to build directory", required=True)
    subp_configure.add_argument("filepath", type=str, help="Path to deps json")
    subp_configure.set_defaults(handler=_configure)
    subp_build = subp.add_parser("build", help="Build dependencies")
    subp_build.add_argument("-B", "--buildDir", type=str, required=True, help="Path to build directory.")
    subp_build.add_argument("--cleanAll", action="store_true", help="Clear build cache (including all dependencies).")
    subp_build.add_argument("--forceDownload", action="store_true", help="Force (re)download.")
    subp_build.add_argument("--no-unzipOverwrite", action="store_true", default=False, help="NO unzip overwrite.")
    subp_build.add_argument("--config", nargs="+", type=str, choices=["Release", "Debug"], default=("Debug", "Release"))
    subp_build.set_defaults(handler=_build)
    subp_test = subp.add_parser("test", help="Building test.")
    subp_test.add_argument("libraryName", type=str)
    subp_test.add_argument("--cleanAll", action="store_true", help="Clear build cache (including all dependencies).")
    subp_test.add_argument("--forceDownload", action="store_true", help="Force (re)download.")
    subp_test.add_argument("-o", "--option", nargs="+", type=str, default=list())
    subp_test.add_argument("--no-unzipOverwrite", action="store_true", default=False, help="NO unzip overwrite.")
    subp_test.add_argument("--ignoreScriptVersion", action="store_true", default=False, help="Ignore script version")
    subp_test.add_argument("--config", nargs="+", type=str, choices=["Release", "Debug"], default=("Debug", "Release"))
    subp_test.set_defaults(handler=testBuild)

    args = parser.parse_args()
    preferencePath = args.preference
    if preferencePath is None:
        preferencePath = os.path.join(os.path.dirname(__file__), "preference.toml")
    distbuilder.Preference.load(preferencePath)

    args.handler(args)
