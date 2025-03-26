import glob
import os
import difflib
import argparse
from datetime import datetime, timezone


def file_mtime(path):
    t = datetime.fromtimestamp(os.stat(path).st_mtime,
                               timezone.utc)
    return t.astimezone().isoformat()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, required=True)
    parser.add_argument("--rootSrc", type=str, default=None,
                        help="Default is <--root>.src directory")
    parser.add_argument("--output", type=str, default="./patchs")
    parser.add_argument("file", type=str, nargs="*", default=list())
    args = parser.parse_args()

    if args.rootSrc is None:
        args.rootSrc = f"{args.root}.src"

    # tofile = args.file
    # fromfile = "{0}.src{1}".format(*os.path.splitext(tofile))
    # output = args.output if args.output is not None else f"{os.path.basename(tofile)}.patch"

    if not args.file:
        # 全てのファイルを対象に.
        files = glob.glob(f"{args.root}/**", recursive=True)
        for file in files:
            if os.path.isfile(file):
                args.file.append(os.path.relpath(file, args.root).replace("\\", "/"))

    os.makedirs(args.output, exist_ok=True)

    for file in args.file:
        print(f"-- {file}")
        fromfile = os.path.join(args.rootSrc, file)
        tofile = os.path.join(args.root, file)
        try:
            with open(fromfile, mode="r", encoding="utf-8") as ff:
                fromlines = ff.readlines()
            with open(tofile, mode="r", encoding="utf-8") as tf:
                tolines = tf.readlines()

            diff = difflib.unified_diff(fromlines, tolines, file, file, n=0)
            diff = [f for f in diff]
            if diff:
                outputfile = os.path.join(args.output, f"{file}.patch")
                print("DIFF!", outputfile)
                os.makedirs(os.path.dirname(outputfile), exist_ok=True)
                with open(outputfile, mode="w", encoding="utf-8") as fp:
                    fp.writelines(diff)
        except UnicodeDecodeError:
            print("Binary file. skip.")


if __name__ == '__main__':
    main()
