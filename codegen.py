import cast
from ir import *
from typing import List

# 我们讨论一下怎么生成return语句
# 现在这个逻辑应该是不正确的
# 要一鼓作气直接高层次IR化
# 设计一种HIR 高层次IR
# 把以前的IR变成LIR
class HIR:
    pass

class HIR_PROGRAM:
    pass

class HIR_BLOCK:
    pass

class HIR_ALLOC(HIR):
    pass

class HIR_Store(HIR):
    pass

class HIR_Load(HIR):
    pass

class HIR_ADD(HIR):
    pass

class HIR_SUB(HIR):
    pass

class HIR_MUL(HIR):
    pass

class HIR_DIV(HIR):
    pass

# HIR暂时不启用

# return的生成可以使用一个专门的生成逻辑
# 我们到底应该怎么生成逻辑？
# 如果是同名变量，一次扫描后应当如何避免值冲突？
# 我们现在想实现的是
# 把所有变量都扫描出来
# 然后进行编址
# 其中一个很好的主意是 直接把地址计算进变量内部（这算好主意吗？）
# 在parse的时候收集变量？可以考虑这个方案

# 给所有的变量收集到一个列表里？

# 设置一个列表 专门跟踪经过的代码块域
# 在这些域里进行变量的查找

# 现在必须要明确的是 变量的扫描（即栈帧的统计） 和变量的定位 是必须分开的
# 在BlkStmt中有一个跟踪本Blk内所有变量的数据结构？
#     存储：一个列表直接代替（已经实现）
# 在Codegen上下文中有一个跟踪当前栈帧的数据结构？
#     存储：一个list完成，后面的进入作用域和离开作用域就操作这个（已经实现）
# 在Codegen中有一个所有变量的统计表？
#     存储：所有变量和对应的offset（未实现，有必要吗？）
# 如何进行变量的查找？
#     在Blk的列表中从后往前查找
class CodegenContext:
    def __init__(self):
        super().__init__()
        # 栈帧长度计数 按字节为单位
        self.frame_length: int = 0
        # 已经生效了的帧
        self.frame_tracker: list[cast.BlkStmt] = []
    
    def init_frame_length(self, stmt: cast.Stmt):
        # 1.对所有变量进行编址
        if isinstance(stmt, cast.BlkStmt):
            return self.__init_frame_length_blkstmt(stmt)
        # 2.对齐栈长度为16字节
        # （暂时未实现）
        raise Exception('')

    def __init_frame_length_blkstmt(self, blkstmt: cast.BlkStmt):
        for varinfo in blkstmt.varinfos:
            self.frame_length += 8
            varinfo.offset = self.frame_length
        # 累加所有子blk
        for stmt in blkstmt.stmts:
            if isinstance(stmt, cast.BlkStmt):
                self.__init_frame_length_blkstmt(stmt)

    def enter_scope(self, blkstmt: cast.BlkStmt):
        self.frame_tracker.append(blkstmt)

    def exit_scope(self):
        self.frame_tracker.pop()

    def query_var(self, name: str) -> int:
        for frame in self.frame_tracker[::-1]:
            for vi in frame.varinfos:
                if vi.name == name:
                    return vi.offset
        raise Exception('')

def codegen_ast2ir_prog(ctx: CodegenContext, prog: cast.Stmt) -> list[IR]:
    ctx.init_frame_length(prog)
    irs: list[IR] = []
    # fp寄存器压栈
    irs.extend(codegen_ast2ir_reg_save(Register(RegNo.FP)))
    # sp复制到fp中
    irs.append(MV(Register(RegNo.FP), Register(RegNo.SP)))
    # sp按照当前的栈帧大小对齐后增长
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), str(-ctx.frame_length)))
    irs.extend(codegen_ast2ir_stmt(ctx, prog))
    irs.extend(codegen_ast2ir_retcontent(ctx))
    return irs

def codegen_ast2ir_stmt(ctx: CodegenContext, stmt: cast.Stmt) -> list[IR]:
    if isinstance(stmt, cast.ExpStmt):
        return codegen_ast2ir_expstmt(ctx, stmt)
    elif isinstance(stmt, cast.BlkStmt):
        return codegen_ast2ir_blkstmt(ctx, stmt)
    elif isinstance(stmt, cast.VarDefsStmt):
        return codegen_ast2ir_vardefsstmt(ctx, stmt)
    elif isinstance(stmt, cast.RetStmt):
        return codegen_ast2ir_retstmt(ctx, stmt)
    raise Exception('')

def codegen_ast2ir_expstmt(ctx: CodegenContext, expstmt: cast.ExpStmt) -> list[IR]:
    return codegen_ast2ir_exp(ctx, expstmt.exp)

def codegen_ast2ir_blkstmt(ctx: CodegenContext, blkstmt: cast.BlkStmt) -> list[IR]:
    ctx.enter_scope(blkstmt)
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
    if vardef.init:
        irs: list[IR] = codegen_ast2ir_exp(ctx, vardef.init)
        irs.append(SD(Register(RegNo.A0), str(-ctx.query_var(vardef.name.value)), Register(RegNo.FP)))
        return irs
    return []

# 现在有个问题 return 的 正文不需要跳转
def codegen_ast2ir_retstmt(ctx: CodegenContext, ret: cast.RetStmt) -> list[IR]:
    irs: list[IR] = []
    if ret.value:
        irs.extend(codegen_ast2ir_exp(ctx, ret.value))
    irs.append(J('.L.return'))
    return irs

# 寄存器入栈
def codegen_ast2ir_reg_save(reg: Register) -> list[IR]:
    irs: list[IR] = []
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
    irs.append(SD(reg, '0', Register(RegNo.SP)))
    return irs

# 寄存器出栈
def codegen_ast2ir_reg_load(reg: Register) -> list[IR]:
    irs: list[IR] = []
    irs.append(LD(reg, '0', Register(RegNo.SP)))
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
    return irs

# 为变量名和表达式提供寻址
def codegen_address(ctx: CodegenContext, to_address: str|cast.Exp) -> list[IR]:
    if isinstance(to_address, str):
        irs: List[IR] = []
        irs.append(LI(Register(RegNo.A0), str(-ctx.query_var(to_address))))
        return irs
    if isinstance(to_address, cast.Idt):
        irs: List[IR] = []
        irs.append(LI(Register(RegNo.A0), str(-ctx.query_var(to_address.idt.value))))
    raise Exception('')

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

def codegen_ast2ir_retcontent(ctx: CodegenContext) -> list[IR]:
    # 返回的操作
    # 1.sp = fp
    # 2.fp出栈
    # 3.ret
    irs: list[IR] = [
        Label('.L.return'),
        ADDI(Register(RegNo.SP), Register(RegNo.SP), str(ctx.frame_length)),
        MV(Register(RegNo.SP), Register(RegNo.FP)),
    ]
    irs.extend(codegen_ast2ir_reg_load(Register(RegNo.FP)))
    irs.append(RET())
    return irs

def codegen_ast2ir(ast: cast.Stmt) -> list[IR]:
    ctx = CodegenContext()
    irs: list[IR] = [PreOrder('globl', 'main'), Label('main')]
    irs.extend(codegen_ast2ir_prog(ctx, ast))
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
            elif isinstance(ir, J):
                code += f'    j {ir.dest}\n'
            elif isinstance(ir, MV):
                code += f"    mv {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
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
