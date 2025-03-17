from typing import Union


class Version:
    def __init__(self, variant: int, major: int, minor: int, patch: int):
        self._variant = variant
        self._major = major
        self._minor = minor
        self._patch = patch

    @property
    def variant(self) -> int:
        return self._variant

    @property
    def major(self) -> int:
        return self._major

    @property
    def minor(self) -> int:
        return self._minor

    @property
    def patch(self) -> int:
        return self._patch

    def __str__(self) -> str:
        if self._variant > 0:
            return f"{self._variant}.{self._major}.{self._minor}.{self._patch}"
        if self._major > 0:
            return f"{self._major}.{self._minor}.{self._patch}"
        else:
            return f"{self._minor}.{self._patch}"

    def __lt__(self, other: "Version") -> bool:
        return (self._variant < other.variant
                and self._major < other.major
                and self._minor < other.minor
                and self._patch < other.patch)

    def __eq__(self, other: "Version") -> bool:
        return (self._variant == other.variant
                and self._major == other.major
                and self._minor == other.minor
                and self._patch == other.patch)

    def __hash__(self):
        return hash(str(self))

    def match(self,
              variant: Union[int, str],
              major: Union[int, str],
              minor: Union[int, str] = "*",
              patch: Union[int, str] = "*"):
        """ Check version matching.

        int version value or string version matching rule.
        "*" matchs all version.
        "123" matchs 123.
        "123-125" matchs 123, 124, 125.
        comma means "or".

        "123, 130-132" matchs 123, 130, 131, 132.

        Args:
            variant (str): variant version.
            major (str): major version.
            minor (str): minor version.
            patch (str): patch version.
        """

        def _check(ver, val):
            if isinstance(val, int):
                return ver == val
            if val == "*":
                return True
            vals = [[int(vv) for vv in v.strip().split("-", 1)] for v in val.split(",")]
            for v in vals:
                if len(v) == 1 and v[0] == ver:
                    return True
                elif len(v) == 2 and v[0] <= ver and ver <= v[1]:
                    return True
            return False

        return _check(self._variant, variant) \
            and _check(self._major, major)\
            and _check(self._minor, minor)\
            and _check(self._patch, patch)
