import c_type


class VarInfo:
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.offset = -1
        self.t: c_type.CType|None = None