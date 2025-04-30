import cast
from ir import *
from typing import List


class CodegenContext:
    def __init__(self):
        super().__init__()
        self.address_tracker: list[dict[str, int]] = []
        # 栈帧长度计数 按字节为单位
        self.frame_length = 0
    
    def enter_scope(self):
        self.address_tracker.append({})

    def exit_scope(self):
        self.address_tracker.pop()
    
    def register_var(self, name: str):
        self.frame_length += 8
        self.address_tracker[-1][name] = self.frame_length

    def query_var(self, name: str) -> int:
        for frame in self.address_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'unknown var: {name}')

def codegen_ast2ir_stmt(ctx: CodegenContext, stmt: cast.Stmt) -> list[IR]:
    if isinstance(stmt, cast.ExpStmt):
        return codegen_ast2ir_expstmt(ctx, stmt)
    elif isinstance(stmt, cast.BlkStmt):
        return codegen_ast2ir_blkstmt(ctx, stmt)
    elif isinstance(stmt, cast.VarDefsStmt):
        return codegen_ast2ir_vardefsstmt(ctx, stmt)
    raise Exception('')

def codegen_ast2ir_expstmt(ctx: CodegenContext, expstmt: cast.ExpStmt) -> list[IR]:
    return codegen_ast2ir_exp(ctx, expstmt.exp)

def codegen_ast2ir_blkstmt(ctx: CodegenContext, blkstmt: cast.BlkStmt) -> list[IR]:
    ctx.enter_scope()
    irs: list[IR] = []
    for stmt in blkstmt.stmts:
        irs.extend(codegen_ast2ir_stmt(ctx, stmt))
    ctx.exit_scope()
    return irs

def codegen_ast2ir_vardefsstmt(ctx: CodegenContext, vardefs: cast.VarDefsStmt) -> list[IR]:
    irs: list[IR] = []
    for vardef in vardefs.var_defs:
        irs.extend(codegen_ast2ir_vardef(ctx, vardef))
    return irs

def codegen_ast2ir_vardef(ctx: CodegenContext, vardef: cast.VarDef) -> list[IR]:
    ctx.register_var(vardef.name.value)
    if vardef.init:
        irs: list[IR] = codegen_ast2ir_exp(ctx, vardef.init)
        irs.append(SD(Register(RegNo.A0), str(-ctx.query_var(vardef.name.value)), Register(RegNo.FP)))
        return irs
    return []

# 压栈寄存器
def codegen_ast2ir_reg_save(reg: Register) -> list[IR]:
    irs: list[IR] = []
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
    irs.append(SD(Register(RegNo.A0), '0', Register(RegNo.SP)))
    return irs

def codegen_ast2ir_reg_load():
    irs: list[IR] = []
    irs.append(LD(Register(RegNo.A0), '0', Register(RegNo.SP)))
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
    return irs

def codegen_ast2ir_exp(ctx: CodegenContext, exp: cast.Exp) -> list[IR]:
    result: list[IR] = []
    if isinstance(exp, cast.Num):
        result.append(LI(Register(RegNo.A0), str(exp.value)))
        return result
    elif isinstance(exp, cast.BinExp):
        # 赋值表达式单独进行处理
        if exp.op == cast.BinOp.ASN:
            if not isinstance(exp.l, cast.Idt):
                raise Exception('')
            # 1.生成左子表达式的地址
            result.append(LI(Register(RegNo.A0), str(-ctx.query_var(exp.l.idt.value))))
            # 2.a0压栈
            result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
            result.append(SD(Register(RegNo.A0), '0', Register(RegNo.SP)))
            # 3.生成右子表达式的值
            result.extend(codegen_ast2ir_exp(ctx, exp.r))
            # 4.出栈到a1
            result.append(LD(Register(RegNo.A1), '0', Register(RegNo.SP)))
            result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
            # 5.sd a0, 地址(fp)
            result.append(SD(Register(RegNo.A0), str(-ctx.query_var(exp.l.idt.value)), Register(RegNo.FP)))
            return result
        # 1.生成右子表达式
        result.extend(codegen_ast2ir_exp(ctx, exp.r))
        # 2.入栈a0
        result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
        result.append(SD(Register(RegNo.A0), '0', Register(RegNo.SP)))
        # 2.生成左子表达式
        result.extend(codegen_ast2ir_exp(ctx, exp.l))
        # 出栈到a1
        result.append(LD(Register(RegNo.A1), '0', Register(RegNo.SP)))
        result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
        # 运算
        if exp.op == cast.BinOp.ADD:
            result.append(ADD(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == cast.BinOp.SUB:
            result.append(SUB(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == cast.BinOp.MUL:
            result.append(MUL(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == cast.BinOp.DIV:
            result.append(DIV(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == cast.BinOp.EQ:
            result.append(XOR(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(SEQZ(Register(RegNo.A0), Register(RegNo.A0)))
        elif exp.op == cast.BinOp.NE:
            result.append(XOR(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        elif exp.op == cast.BinOp.LT:
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == cast.BinOp.LE:
            # a0 <= a1 翻译为 a0 > a1 结果取反
            # a1 > a0
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
            result.append(XORI(Register(RegNo.A0), Register(RegNo.A0), '1'))
        elif exp.op == cast.BinOp.GT:
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
        elif exp.op == cast.BinOp.GE:
            # a0 >= a1 翻译为 a0 < a1 结果取反
            # a1 > a0
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(XORI(Register(RegNo.A0), Register(RegNo.A0), '1'))
        else:
            raise Exception('')
    elif isinstance(exp, cast.UExp):
        result.extend(codegen_ast2ir_exp(ctx, exp.exp))
        if exp.op == cast.UOp.ADD:
            pass
        elif exp.op == cast.UOp.SUB:
            result.append(LI(Register(RegNo.A1), '0'))
            result.append(SUB(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
    elif isinstance(exp, cast.Idt):
        result.append(LD(Register(RegNo.A0), str(-ctx.query_var(exp.idt.value)), Register(RegNo.FP)))
    else:
        raise Exception('')
    return result

def codegen_ast2ir(ast: cast.Stmt) -> list[IR]:
    ctx = CodegenContext()
    irs: list[IR] = [PreOrder('globl', 'main'), Label('main')]
    irs.extend(codegen_ast2ir_stmt(ctx, ast))
    irs.append(RET())
    return irs


def codegen_ir2asm(irs: List[IR]) -> str:
    code = ""
    for ir in irs:
        if isinstance(ir, Label):
            code += f"{ir.name}:\n"
        elif isinstance(ir, PreOrder):
            code += f"    .{ir.order} {ir.content}\n"
        elif isinstance(ir, Instruction):
            if isinstance(ir, LI):
                code += f"    li {ir.dest.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, RET):
                code += "    ret\n"
            elif isinstance(ir, ADDI):
                code += f"    addi {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, ADD):
                code += f"    add {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, SUB):
                code += f"    sub {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, MUL):
                code += f"    mul {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, DIV):
                code += f"    div {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, XOR):
                code += f"    xor {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, XORI):
                code += f"    xori {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, SEQZ):
                code += f"    seqz {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, SNEZ):
                code += f"    snez {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, SLT):
                code += f"    slt {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, SD):
                code += f"    sd {ir.src.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, LD):
                code += f"    ld {ir.dest.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            else:
                raise Exception('')
    return code

def codegen(ast: cast.Stmt) -> str:
    irs = codegen_ast2ir(ast)
    code = codegen_ir2asm(irs)
    return code