import os
from .preference import Preference
from .global_options import GlobalOptions
from .functions import searchBuilderAndPath


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

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

    def _testBuild(args):
        globalOpt = GlobalOptions()

        builderCls, path = searchBuilderAndPath(args.libraryName)
        versions = builderCls.versions.copy()

        for version in versions:
            builder = builderCls(version, dict(), globalOpt)
            print(builder.allOptions)
            print(builder.allDependencies)
        return

        # args.option から options を作成
        options = dict()
        for opt in args.option:
            k, v = opt.split("=", 2)
            option: distbuilder.Option = getattr(builderCls, f"option_{k}")
            if option.type is not str:
                v = option.type(int(v))
            options[k] = v
            print(f"Override option: {k} = {v}")

        rootdir = os.path.join(Preference.get().buildRootDirectory, "testbuild")
        os.makedirs(rootdir, exist_ok=True)
        for version in versions:
            libraryName_tmp = builderCls.__module__.__name__
            # TODO: options
            builder = builderCls({libraryName_tmp: {"version": version}}, GlobalOptions())
            filepath = os.path.join(rootdir, f"testbuild.{builder.libraryName}.{version}.json")
            with open(filepath, mode="w", encoding="utf-8") as fp:
                json.dump({
                    builder.libraryName: {"version": str(version), "options": options}
                }, fp)
            # TODO:
            configure(filepath, rootdir, configureGlobalOpt)
            build(rootdir, buildGlobalOpt)

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
    subp_test.set_defaults(handler=_testBuild)

    args = parser.parse_args()
    preferencePath = args.preference
    if preferencePath is None:
        preferencePath = os.path.join(os.path.dirname(__file__), "../preference.toml")
    Preference.load(preferencePath)

    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_usage()
