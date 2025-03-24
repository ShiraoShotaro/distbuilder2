
import sys
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
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("file", type=str)
    args = parser.parse_args()

    tofile = args.file
    fromfile = "{0}.src{1}".format(*os.path.splitext(tofile))
    output = args.output if args.output is not None else f"{os.path.basename(tofile)}.patch"

    with open(os.path.join(args.root, fromfile), mode="r", encoding="utf-8") as ff:
        fromlines = ff.readlines()
    with open(os.path.join(args.root, tofile), mode="r", encoding="utf-8") as tf:
        tolines = tf.readlines()

    diff = difflib.unified_diff(fromlines, tolines, tofile, tofile)

    with open(output, mode="w", encoding="utf-8") as fp:
        fp.writelines(diff)


if __name__ == '__main__':
    main()
