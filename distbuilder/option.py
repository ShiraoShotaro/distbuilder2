from .errors import BuildError


class Option:
    def __init__(self, type, defaultValue, description=None):
        self._builder = None
        self._key = None
        self._type = type
        self._defaultValue = defaultValue
        self._description = description
        self._value = None

    def copy(self) -> "Option":
        opt = Option(self._type, self._defaultValue, self._description)
        opt._builder = self._builder
        opt._key = self._key
        opt._value = self._value
        return opt

    # def _instantiate(self, builder) -> "Option":
    #     opt = Option(self._type, self._defaultValue, self._description)
    #     opt._key = self._key
    #     opt._builder = builder
    #     opt._value = None
    #     return opt

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
        return self._value if self._value is not None else self._defaultValue

    def hasValue(self) -> bool:
        return self._value is not None

    def setValue(self, value):
        if isinstance(value, self._type):
            self._value = value
            self._builder._setDirty()
        else:
            raise BuildError("Invalid option value type.")

    def __str__(self) -> str:
        if self._type is bool:
            return "1" if self.value else "0"
        else:
            return str(self.value)

    def __bool__(self) -> bool:
        if self._type is bool:
            return self.value
        else:
            raise BuildError(f"Unconvertible to bool. Option: {self.key}")
