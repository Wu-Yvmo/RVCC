from enum import Enum, auto

class RegNo(Enum):
    FP = auto()
    SP = auto()
    A0 = auto()
    A1 = auto()

class Register:
    def __init__(self, no: RegNo):
        super().__init__()
        self.no = no

# IR是通用中间表达
class IR:
    def __init__(self):
        super().__init__()

# 标签，name是标签名
class Label(IR):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

# 预编译指令
class PreOrder(IR):
    def __init__(self, order: str, content: str):
        super().__init__()
        self.order = order
        self.content = content

# 指令
class Instruction(IR):
    def __init__(self):
        super().__init__()

# 加载立即数
class LI(Instruction):
    def __init__(self, dest: Register, value: str):
        super().__init__()
        self.dest = dest
        self.value = value

# 返回
class RET(Instruction):
    def __init__(self):
        super().__init__()

# 指令+
class ADD(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令+立即数版本
class ADDI(Instruction):
    def __init__(self, dest: Register, src1: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.value = value

# 指令-
class SUB(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令*
class MUL(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令/
class DIV(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令xor
class XOR(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 指令xori
class XORI(Instruction):
    def __init__(self, dest: Register, src: Register, value: str):
        super().__init__()
        self.dest = dest
        self.src = src
        self.value = value

# 指令seqz
class SEQZ(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 指令snez
class SNEZ(Instruction):
    def __init__(self, dest: Register, src: Register):
        super().__init__()
        self.dest = dest
        self.src = src

# 指令slt
class SLT(Instruction):
    def __init__(self, dest: Register, src1: Register, src2: Register):
        super().__init__()
        self.dest = dest
        self.src1 = src1
        self.src2 = src2

# 存储双字
class SD(Instruction):
    def __init__(self, src: Register, offset: str, base: Register):
        super().__init__()
        self.src = src
        self.offset = offset
        self.base = base

# 加载双字
class LD(Instruction):
    def __init__(self, dest: Register, offset: str, base: Register):
        super().__init__()
        self.dest = dest
        self.offset = offset
        self.base = base

if __name__ == '__main__':
    print('Hello, world')
    a: list[IR] = [Label('a')]
    a.append(PreOrder('order', 'content'))
    print(a)