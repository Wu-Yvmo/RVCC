import ctype


class VarInfo:
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.offset = -1
        self.t: ctype.CType|None = None