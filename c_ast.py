from dataclasses import dataclass
from typing import * # type: ignore
from enum import Enum, auto

import c_type
from ir import RegNo
import varinfo
import ctoken

class Stmt:
    def __init__(self):
        super().__init__()

@dataclass
class Exp:
    def __init__(self):
        super().__init__()
        self.type: c_type.CType|None = None

class BinOp(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    ASN = auto()
    BITS_AND = auto()
    COMMA = auto()
    # access，访问
    ACS = auto()

@dataclass
class BinExp(Exp):
    def __init__(self, l: Exp, op: BinOp, r: Exp):
        super().__init__()
        self.l = l
        self.op = op
        self.r = r

class UOp(Enum):
    ADD = auto()
    SUB = auto()
    NOT = auto()
    REF = auto()
    DEREF = auto()
    SIZEOF = auto()

def binop2uop(binop: BinOp) -> UOp:
    if binop == BinOp.ADD:
        return UOp.ADD
    elif binop == BinOp.SUB:
        return UOp.SUB
    elif binop == BinOp.BITS_AND:
        return UOp.REF
    elif binop == BinOp.MUL:
        return UOp.DEREF
    else:
        raise Exception('')

class UExp(Exp):
    def __init__(self, op: UOp, exp: Exp|Stmt):
        super().__init__()
        self.op = op
        self.exp = exp # 我们要修改这个地方的可能性 对类型签名进行sizeof需要额外的修改
        # 还是说我们应该基于这个前提构造表达式？
        # 所以说我是愿意计算一些表达式的
    
    def __str__(self) -> str:
        return f'({self.op}, {self.exp})'

class CastExp(Exp):
    def __init__(self, exp: Exp, cast_to: c_type.CType):
        super().__init__()
        self.exp = exp
        self.cast_to = cast_to

class Num(Exp):
    def __init__(self, value: int):
        super().__init__()
        self.value = value
    
    def __str__(self) -> str:
        return f'({self.value})'

class Str(Exp):
    def __init__(self, value: str):
        super().__init__()
        # 这里增加一个转义字符适配的步骤
        self.value = self.__convert_str(value)
    
    def __convert_str(self, value: str) -> str:
        # 转义字符适配
        after: str = ''
        # a b t n v f r e j k l
        embed_convert: dict[str, str] = {
            'a': '\a',
            'b': '\b',
            't': '\t',
            'n': '\n',
            'v': '\v',
            'f': '\f',
            'r': '\r',
            'e': chr(27),
            'j': chr(106),
            'k': chr(107),
            'l': chr(108),
            '\\': '\\', 
        }
        while len(value) > 0:
            # 不需要转义
            if value[0] != '\\':
                after += value[0]
                value = value[1:]
                continue
            # 转义字符
            value = value[1:]
            if embed_convert.get(value[0]) is not None:
                after += embed_convert[value[0]]
                value = value[1:]
                continue
            # 不是16或8进制转义字符 （说明不是转义字符）
            if value[0] != 'x' and (ord(value[0]) > ord('7') or ord(value[0]) < ord('0')):
                after += value[0]
                value = value[1:]
                continue
            # 8进制 或 16进制 对于8进制 不能长于3位 对于16进制 无限长
            # 16 进制
            if value[0] == 'x':
                # print(f'is hex: {value}')
                value = value[1:]
                ctr = 0
                while len(value) > 0 and self.__is_hexchar(value[0]):
                    ctr *= 16
                    ctr += self.__eval_hexchar(value[0])
                    value = value[1:]
                after += chr(ctr)
                continue
            # 8 进制
            ctr = 0
            for _ in range(3):
                if len(value) == 0:
                    break
                if not self.__is_octchar(value[0]):
                    break
                ctr *= 8
                ctr += self.__eval_octchar(value[0])
                value = value[1:]
            after += chr(ctr)
        return after
    
    def __is_hexchar(self, c: str) -> bool:
        v = ord(c)
        return (v >= ord('0') and v <= ord('9')) or (v >= ord('a') and v <= ord('f')) or (v >= ord('A') and v <= ord('F'))
    
    def __eval_hexchar(self, c: str) -> int:
        v = ord(c)
        if v >= ord('0') and v <= ord('9'):
            return v - ord('0')
        if v >= ord('a') and v <= ord('f'):
            return v - ord('a') + 10
        if v >= ord('A') and v <= ord('F'):
            return v - ord('A') + 10
        raise Exception('')
    
    def __is_octchar(self, c: str) -> bool:
        v = ord(c)
        return v >= ord('0') and v <= ord('7')
    
    def __eval_octchar(self, c: str) -> int:
        v = ord(c)
        if v >= ord('0') and v <= ord('7'):
            return v - ord('0')
        raise Exception('')

class Idt(Exp):
    def __init__(self, idt: ctoken.CToken):
        super().__init__()
        self.idt = idt

    def __str__(self) -> str:
        return f'({self.idt.value})'

# 调用
class Call(Exp):
    def __init__(self, func_source: Exp, inargs: list[Exp]):
        super().__init__()
        self.func_source = func_source
        self.inargs = inargs

class BlkExp(Exp):
    def __init__(self, stmt: Stmt):
        super().__init__()
        self.stmt = stmt

# # 下标运算
# class Index(Exp):
#     def __init__(self, source: Exp, index: Exp):
#         super().__init__()
#         self.source = source
#         self.index = index

# stmt

class ExpStmt(Stmt):
    def __init__(self, exp: Exp):
        super().__init__()
        self.exp = exp

class BlkStmt(Stmt):
    def __init__(self, stmts: list[Stmt]):
        super().__init__()
        self.stmts = stmts
        self.varinfos: list[varinfo.VarInfo] = []

class VarDescribe:
    def __init__(self):
        super().__init__()
        self.t: c_type.CType|None = None
        self.init: Exp|None = None
        self.body: Stmt|None = None
    
    def get_type(self) -> c_type.CType:
        raise Exception('')
    
    def get_name(self) -> str:
        raise Exception('')
    
    def is_funcdef(self) -> bool:
        raise Exception('')

class VarDefsStmt(Stmt):
    def __init__(self, btype: c_type.CType, var_describes: list[VarDescribe]):
        '''
        var_defs:
            1. 变量定义
            2. 函数定义
            3. 函数/变量声明
        '''
        super().__init__()
        self.btype = btype
        self.var_describes = var_describes

    def is_funcdef(self) -> bool:
        return len(self.var_describes) == 1 and self.var_describes[0].is_funcdef()

class GhostVarDescribe(VarDescribe):
    def __init__(self, init: Exp| None):
        super().__init__()
        self.init = init
        self.t: c_type.CType|None = None

    def get_type(self) -> c_type.CType:
        if self.t is None:
            raise Exception('')
        return self.t

    def get_name(self) -> str:
        raise Exception(f'{self.t}')
    
    def is_funcdef(self) -> bool:
        return False
    
class NormalVarDescribe(VarDescribe):
    def __init__(self, name: ctoken.CToken, init: Exp|None):
        super().__init__()
        self.name = name
        self.init = init
        self.t: c_type.CType|None = None
    
    def get_type(self) -> c_type.CType:
        if self.t is None:
            raise Exception('')
        return self.t
    
    def get_name(self) -> str:
        return self.name.value
    
    def is_funcdef(self) -> bool:
        return False

class FuncVarDescribe(VarDescribe):
    def __init__(self, vardescribe: VarDescribe, params: list[VarDefsStmt], body: Stmt|None):
        super().__init__()
        self.vardescribe = vardescribe
        self.params = params
        self.body = body
        self.t: c_type.CType|None = None
    
    def get_type(self) -> c_type.CType:
        return self.vardescribe.get_type()
    
    def get_name(self) -> str:
        return self.vardescribe.get_name()
    
    def is_funcdef(self) -> bool:
        return self.body is not None

class PtrVarDescribe(VarDescribe):
    def __init__(self, vardescribe: VarDescribe):
        super().__init__()
        self.vardescribe = vardescribe
        self.t: c_type.CType|None = None

    def get_type(self) -> c_type.CType:
        return self.vardescribe.get_type()

    def get_name(self) -> str:
        return self.vardescribe.get_name()

    def is_funcdef(self) -> bool:
        return False
    
class AryVarDescribe(VarDescribe):
    def __init__(self, vardescribe: VarDescribe, length: int):
        super().__init__()
        self.vardescribe = vardescribe
        self.length = length
        self.t: c_type.CType|None = None
    
    def get_type(self) -> c_type.CType:
        return self.vardescribe.get_type()
    
    def get_name(self) -> str:
        return self.vardescribe.get_name()
    
    def is_funcdef(self) -> bool:
        return False

class RetStmt(Stmt):
    def __init__(self, value: Exp|None):
        super().__init__()
        self.value = value

class IfStmt(Stmt):
    def __init__(self, cond: Exp, t: Stmt, f: Stmt|None):
        super().__init__()
        self.cond = cond
        self.t = t
        self.f = f

class ForStmt(Stmt):
    def __init__(self, init: None|VarDefsStmt|Exp, cond: None|Exp, step: None|Exp, body: Stmt):
        super().__init__()
        self.init = init
        self.cond = cond
        self.step = step
        self.body = body

class WhileStmt(Stmt):
    def __init__(self, cond: Exp, body: Stmt):
        super().__init__()
        self.cond = cond
        self.body = body

# typedef是个吉祥物 什么都不需要做
class TypedefStmt(Stmt):
    def __init__(self):
        super().__init__()
# class Prog:
#     def __init__(self, stmts: list[VarDefsStmt]):
#         super().__init__()
#         self.stmts = stmts

# 对后续工作进行一些讨论。统一使用VarDefs表示变量定义、声明和函数定义
# 对数据结构要进行修改

if __name__ == '__main__':
    print(RegNo.A0 + 1 == RegNo.A1)
    reg = RegNo.A0 + 1
    reg = list(RegNo)[0]
    print(reg.name)