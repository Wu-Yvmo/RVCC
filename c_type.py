import utils


class CType:
    def __init__(self):
        super().__init__()
        # 该字段用于标记类型是否是全局类型 默认不是全局类型
        self.glb = False
        # 该字段用于标记类型是否是static。默认不是static
        self.static = False
    
    def length(self) -> int:
        raise Exception('')
    
    def align(self) -> int:
        raise Exception('')

class Void(CType):
    def __init__(self):
        super().__init__()

    def length(self) -> int:
        raise Exception('should not get length')
    
    def align(self) -> int:
        raise Exception('void do not say')

class I64(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 8
    
    def align(self) -> int:
        return 8

class I32(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 4
    
    def align(self) -> int:
        return 4

class I16(CType):
    def __init__(self):
        super().__init__()

    def length(self) -> int:
        return 2
    
    def align(self) -> int:
        return 2

class I8(CType):
    def __init__(self):
        super().__init__()
    
    def length(self) -> int:
        return 1
    
    def align(self) -> int:
        return 1

class Bool(CType):
    def __init__(self):
        super().__init__()

    def length(self) -> int:
        return 1

    def align(self) -> int:
        return 1
    
class Ptr(CType):
    def __init__(self, base: CType):
        super().__init__()
        self.base = base
    
    def length(self) -> int:
        return 8
    
    def align(self) -> int:
        return 8

# 数组
class Ary(CType):
    def __init__(self, base: CType, length: int):
        super().__init__()
        self.base = base
        self.len = length
    
    def length(self) -> int:
        return self.base.length() * self.len
    
    def align(self) -> int:
        return self.base.align()

class Enum(CType):
    def __init__(self, label: str):
        super().__init__()
        self.label = label
        self.len = 4
        self.aln = 4

    def length(self) -> int:
        return self.len

    def align(self) -> int:
        return self.aln

class Func(CType):
    def __init__(self, args: list[tuple[str, CType]], ret: CType):
        super().__init__()
        self.args = args
        self.ret = ret
    
    def length(self) -> int:
        raise Exception('func here!')

class CStruct(CType):
    def __init__(self, label: None|str, items: list[tuple[str, CType]]):
        super().__init__()
        self.label = label
        # 要编地址
        self.len = 0
        self.aln = 1
        self.items: dict[str, tuple[CType, int]] = {}
        self.load_content(items)
    
    # 加载成员. 之所以把这个逻辑独立出来是为了让结构体能够以Ghost的形式存在
    def load_content(self, items: list[tuple[str, CType]]):
        for item in items:
            # 将当前偏移量对齐到本元素的偏移量
            self.len = utils.align2(self.len, item[1].align())
            self.items[item[0]] = (item[1], self.len)
            self.len += item[1].length()
            # 更新align
            if self.aln < item[1].align():
                self.aln = item[1].align()
        # 将结构体的长度对齐到结构体的对齐数
        self.len = utils.align2(self.len, self.aln)

    def length(self) -> int:
        return self.len
    
    # 计算偏移量
    def offset(self, key: str) -> int:
        return self.items[key][1]
    
    def subtype(self, key: str) -> CType:
        return self.items[key][0]
    
    def align(self) -> int:
        return self.aln

# 幽灵结构体 在结构体没有完成定义时使用 为了让结构体内部的成员
# 得以访问自己.
class CStructGhost(CType):
    def __init__(self, label: str):
        pass

class CUnion(CType):
    def __init__(self, label: None|str, items: list[tuple[str, CType]]):
        super().__init__()
        self.label = label
        self.items = items
        self.len = 0
        self.aln = 1
        # CUnion的大小应当是所有成员中最大的那个
        for item in items:
            if self.len < item[1].length():
                self.len = item[1].length()
            if self.aln < item[1].align():
                self.aln = item[1].align()
        # 对齐自身大小
        self.len = utils.align2(self.len, self.aln)
    
    def length(self):
        return self.len
    
    def subtype(self, key: str) -> CType:
        for item in self.items:
            if key == item[0]:
                return item[1]
        raise Exception('')

    def align(self) -> int:
        return self.aln

class CEnum(CType):
    def __init__(self, label: None|str, items: list[tuple[str, int]]):
        super().__init__()
        self.label = label
        self.items = items

def same_type(tl: CType, tr: CType) -> bool:
    # 判断类型是否相同
    if isinstance(tl, I8) and isinstance(tr, I8):
        return True
    if isinstance(tl, I16) and isinstance(tr, I16):
        return True
    if isinstance(tl, I32) and isinstance(tr, I32):
        return True
    if isinstance(tl, I64) and isinstance(tr, I64):
        return True
    return False

if __name__ == '__main__':
    print(I64().length())
    print(I32().length())
    print(Ptr(I32()).length())