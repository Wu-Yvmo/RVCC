from typing import * # type: ignore
from enum import Enum, auto

import ctype
from ir import RegNo
import varinfo
import ctoken

class Exp:
    def __init__(self):
        super().__init__()
        self.type: ctype.CType|None = None

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
    def __init__(self, op: UOp, exp: Exp):
        super().__init__()
        self.op = op
        self.exp = exp

class Num(Exp):
    def __init__(self, value: int):
        super().__init__()
        self.value = value

class Idt(Exp):
    def __init__(self, idt: ctoken.CToken):
        super().__init__()
        self.idt = idt

# 调用
class Call(Exp):
    def __init__(self, func_source: Exp, inargs: list[Exp]):
        super().__init__()
        self.func_source = func_source
        self.inargs = inargs

# 下标运算
class Index(Exp):
    def __init__(self, source: Exp, index: Exp):
        super().__init__()
        self.source = source
        self.index = index

# stmt
class Stmt:
    def __init__(self):
        super().__init__()

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
        self.t: ctype.CType|None = None
    
    def get_type(self) -> ctype.CType:
        raise Exception('')
    
    def get_name(self) -> str:
        raise Exception('')
    
    def is_funcdef(self) -> bool:
        raise Exception('')

class VarDefsStmt(Stmt):
    def __init__(self, btype: ctype.CType, var_describes: list[VarDescribe]):
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

class NormalVarDescribe(VarDescribe):
    def __init__(self, name: ctoken.CToken, init: Exp|None):
        super().__init__()
        self.name = name
        self.init = init
        self.t: ctype.CType|None = None
    
    def get_type(self) -> ctype.CType:
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
        self.t: ctype.CType|None = None
    
    def get_type(self) -> ctype.CType:
        if self.t is None:
            raise Exception('')
        return self.t
    
    def get_name(self) -> str:
        return self.vardescribe.get_name()
    
    def is_funcdef(self) -> bool:
        return self.body is not None

class AryVarDescribe(VarDescribe):
    def __init__(self, vardescribe: VarDescribe, length: int):
        super().__init__()
        self.vardescribe = vardescribe
        self.length = length
        self.t: ctype.CType|None = None
    
    def get_type(self) -> ctype.CType:
        if self.t is None:
            raise Exception('')
        return self.t
    
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