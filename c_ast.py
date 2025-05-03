from typing import * # type: ignore
from enum import Enum, auto

import varinfo
import ctoken

class Exp:
    def __init__(self):
        super().__init__()

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

def binop2uop(binop: BinOp) -> UOp:
    if binop == BinOp.ADD:
        return UOp.ADD
    elif binop == BinOp.SUB:
        return UOp.SUB
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

class VarDef:
    def __init__(self, name: ctoken.CToken, init: Exp|None):
        super().__init__()
        self.name = name
        self.init = init

class VarDefsStmt(Stmt):
    def __init__(self, var_defs: list[VarDef]):
        super().__init__()
        self.var_defs = var_defs

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

class Prog:
    pass