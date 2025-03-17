from .errors import BuildError


class Option:
    def __init__(self, type, defaultValue, description=None):
        self._key = None
        self._type = type
        self._defaultValue = defaultValue
        self._description = description
        self._value = defaultValue

    def copy(self) -> "Option":
        opt = Option(self._type, self._defaultValue, self._description)
        opt._key = self._key
        return opt

    @property
    def key(self) -> str:
        assert self._key is not None
        return self._key

    @property
    def type(self):
        return self._type

    @property
    def defaultValue(self):
        return self._defaultValue

    @property
    def description(self):
        return self._description

    @property
    def value(self):
        return self._value

    def setValue(self, value):
        if isinstance(value, self._type):
            print(f"UPDATE CONFIG: {self._key}={value}")
            self._value = value
        else:
            raise BuildError("Invalid option value type.")

    def __str__(self) -> str:
        if self._type is bool:
            return "1" if self._value else "0"
        else:
            return str(self._value)
