class CType:
    def __init__(self):
        super().__init__()
        self.glb = False
    
    def length(self) -> int:
        raise Exception('')

class I64(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 8

class I32(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 4

class I16(CType):
    def __init__(self):
        super().__init__()

    def length(self) -> int:
        return 2

class I8(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 1

class Ptr(CType):
    def __init__(self, base: CType):
        super().__init__()
        self.base = base
    
    def length(self) -> int:
        return 8

# 数组
class Ary(CType):
    def __init__(self, base: CType, length: int):
        super().__init__()
        self.base = base
        self.len = length
    
    def length(self) -> int:
        return self.base.length() * self.len
    
class Func(CType):
    def __init__(self, args: list[CType], ret: CType):
        super().__init__()
        self.args = args
        self.ret = ret

if __name__ == '__main__':
    print(I64().length())
    print(I32().length())
    print(Ptr(I32()).length())