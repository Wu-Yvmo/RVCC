import c_ast
import ctype
from ir import *
from typing import * # type: ignore

import varinfo # type: ignore

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
        self.frame_tracker: list[list[varinfo.VarInfo]] = []
        # if标号的计数器
        self.if_counter = 0
        # for标号的计数器
        self.for_counter = 0
        # while标号的计数器
        self.while_counter = 0
        # 当前正在处理的函数的名字
        self.func_name = ''
        # 全局变量的名称 和 类型
        # self.glb_var_tracker: dict[str, ctype.CType] = {}
    
    def init_frame_length(self, vardefs: c_ast.VarDefsStmt):
        # 现在是对整个函数进行初始化
        # 要对传入的参数也进行编址
        if not isinstance(vardefs.var_describes[0], c_ast.FuncVarDescribe):
            raise Exception('')
        frame_0: list[varinfo.VarInfo] = []
        for param in vardefs.var_describes[0].params:
            vi = varinfo.VarInfo(param.var_describes[0].get_name())
            vi.t = param.var_describes[0].get_type()
            self.frame_length += vi.t.length()
            vi.offset = self.frame_length
            frame_0.append(vi)
        self.frame_tracker.append(frame_0)
        # 1.对所有变量进行编址
        if isinstance(vardefs.var_describes[0].body, c_ast.BlkStmt):
            return self.__init_frame_length_blkstmt(vardefs.var_describes[0].body)
        # 2.对齐栈长度为16字节
        # （暂时未实现）
        raise Exception('')

    def __init_frame_length_blkstmt(self, blkstmt: c_ast.BlkStmt):
        # 现在的主要问题在变量编址上 数组
        # 按照测试用例的要求，变量在栈上的存储方式是类似数组的
        for varinfo in blkstmt.varinfos[::-1]:
            if varinfo.t is None:
                raise Exception('')
            self.frame_length += varinfo.t.length()
            varinfo.offset = self.frame_length
        # 累加所有子blk
        for stmt in blkstmt.stmts:
            if isinstance(stmt, c_ast.BlkStmt):
                self.__init_frame_length_blkstmt(stmt)
            elif isinstance(stmt, c_ast.IfStmt):
                if isinstance(stmt.t, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.t)
                if stmt.f and isinstance(stmt.f, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.f)
            elif isinstance(stmt, c_ast.ForStmt):
                if isinstance(stmt.body, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.body)
            elif isinstance(stmt, c_ast.WhileStmt):
                if isinstance(stmt.body, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.body)
    
    def enter_scope(self, blkstmt: c_ast.BlkStmt):
        self.frame_tracker.append(blkstmt.varinfos)

    def exit_scope(self):
        self.frame_tracker.pop()

    def query_var(self, name: str) -> int:
        for frame in self.frame_tracker[::-1]:
            for vi in frame:
                if vi.name == name:
                    return vi.offset
        raise Exception('')
    
    # ...上文
    # cond求值
    # jeqz .L.if.{ctr}.false
    #     true 分支
    #     j .L.if.{ctr}.end
    # .L.if.{ctr}.false:
    #     false分支
    # .L.if.{ctr}.end：
    #     ...下文
    # 总共生成2个标签：.L.if.{ctr}.false 和 .L.if.{ctr}.end
    def gen_if_labels(self) -> tuple[str, str]:
        '''
        * .0: .L.if.{ctr}.false 标签
        * .1: .L.if.{ctr}.end 标签
        '''
        if_ctr = self.if_counter
        self.if_counter += 1
        return (f'.L.if.{if_ctr}.false', f'.L.if.{if_ctr}.end')
    
    # for的continue跳转到.L.for{ctr}.step
    # for的break跳转到.L.for.{ctr}.end
    # 伪代码：
    #     ...上文
    #     init代码
    # .L.for.{ctr}.cond:
    #     cond求值
    #     jeqz .L.for.{ctr}.end
    #     body
    # .L.for{ctr}.step:
    #     step求值
    #     j cond
    # .L.for.{ctr}.end:
    #     ...下文
    # 总共生成3个标签：.L.for.{ctr}.cond .L.for{ctr}.step 和 .L.for.{ctr}.end
    def gen_for_labels(self) -> tuple[str, str, str]:
        '''
        * .0:.L.for.{ctr}.cond
        * .1:.L.for.{ctr}.step
        * .2:.L.for.{ctr}.end
        '''
        for_ctr = self.for_counter
        self.for_counter += 1
        return (f'.L.for.{for_ctr}.cond', f'.L.for.{for_ctr}.step', f'.L.for.{for_ctr}.end')

    # while的continue跳转到.L.while.{ctr}.cond
    # while 的break跳转到.L.while.{ctr}.end
    #     ...上文
    # .L.while.{ctr}.cond:
    #     表达式求值
    #     jeqz .L.while.{ctr}.end
    #     body正文
    # .L.while.{ctr}.end:
    #     ...下文
    # 总共生成2个标签： .L.while.{ctr}.cond 和 .L.while.{ctr}.end
    def gen_while_labels(self) -> tuple[str, str]:
        '''
        * 0: .L.while.{ctr}.cond
        * 1: .L.while.{ctr}.end
        '''
        while_ctr = self.while_counter
        self.while_counter += 1
        return (f'.L.while.{while_ctr}.cond', f'.L.while.{while_ctr}.end')

def codegen_ast2ir_global_vardefs(ctx: CodegenContext, vardefs: c_ast.VarDefsStmt) -> list[IR]:
    irs: list[IR] = []
    if vardefs.is_funcdef():
        ctx.func_name = vardefs.var_describes[0].get_name()
        # 1.生成全局声明和函数开头
        irs.extend([
            PreOrder('text', ''),
            PreOrder('globl', vardefs.var_describes[0].get_name()),
            Label(vardefs.var_describes[0].get_name()),
        ])
        # 2.生成函数入口的保存操作
        #   ra寄存器压栈
        irs.extend(codegen_ast2ir_reg_save(Register(RegNo.RA)))
        #   fp寄存器压栈
        irs.extend(codegen_ast2ir_reg_save(Register(RegNo.FP)))
        #   sp复制到fp中
        irs.append(MV(Register(RegNo.FP), Register(RegNo.SP)))
        # 初始化栈帧
        if not isinstance(vardefs.var_describes[0], c_ast.FuncVarDescribe):
            raise Exception('')
        if vardefs.var_describes[0].body is None:
            raise Exception('')
        ctx.init_frame_length(vardefs)
        # sp按照当前的栈帧大小对齐后增长
        irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), str(-ctx.frame_length)))
        # 把寄存器中的内容复制到栈帧中
        # 具体的执行办法是：a0到a6全部压栈
        # 然后依次出栈到a0
        for i in range(len(vardefs.var_describes[0].params)):
            reg = list(RegNo)[i]
            irs.extend(codegen_ast2ir_reg_save(Register(reg)))
        for i in range(len(vardefs.var_describes[0].params))[::-1]:
            # 生成变量地址
            irs.extend(codegen_address(ctx, vardefs.var_describes[0].params[i].var_describes[0].get_name()))
            # 将变量地址移动到a1
            irs.append(MV(Register(RegNo.A1), Register(RegNo.A0)))
            irs.extend(codegen_ast2ir_reg_load(Register(RegNo.A0)))
            # 将变量的值存储到0(a1)中
            irs.append(SD(Register(RegNo.A0), '0', Register(RegNo.A1)))
        # 3.生成函数体
        irs.extend(codegen_ast2ir_stmt(ctx, vardefs.var_describes[0].body))
        # 4.生成ret逻辑
        irs.extend(codegen_ast2ir_retcontent(ctx))
        return irs
    # 说明是全局变量 暂时没有提供支持
    for vardescribe in vardefs.var_describes:
        irs.append(PreOrder('data', ''))
        irs.append(PreOrder('globl', f'{vardescribe.get_name()}'))
        irs.append(Label(f'{vardescribe.get_name()}'))
        irs.append(PreOrder('zero', f'{vardescribe.get_type().length()}'))
    return irs

# def codegen_ast2ir_prog(ctx: CodegenContext, prog: c_ast.Stmt) -> list[IR]:
#     ctx.init_frame_length(prog)
#     irs: list[IR] = []
#     # fp寄存器压栈
#     irs.extend(codegen_ast2ir_reg_save(Register(RegNo.FP)))
#     # sp复制到fp中
#     irs.append(MV(Register(RegNo.FP), Register(RegNo.SP)))
#     # sp按照当前的栈帧大小对齐后增长
#     irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), str(-ctx.frame_length)))
#     irs.extend(codegen_ast2ir_stmt(ctx, prog))
#     irs.extend(codegen_ast2ir_retcontent(ctx))
#     return irs

def codegen_ast2ir_stmt(ctx: CodegenContext, stmt: c_ast.Stmt) -> list[IR]:
    if isinstance(stmt, c_ast.ExpStmt):
        return codegen_ast2ir_expstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.BlkStmt):
        return codegen_ast2ir_blkstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.VarDefsStmt):
        return codegen_ast2ir_vardefsstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.RetStmt):
        return codegen_ast2ir_retstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.IfStmt):
        return codegen_ast2ir_ifstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.ForStmt):
        return codegen_ast2ir_forstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.WhileStmt):
        return codegen_ast2ir_whilestmt(ctx, stmt)
    raise Exception('')

def codegen_ast2ir_expstmt(ctx: CodegenContext, expstmt: c_ast.ExpStmt) -> list[IR]:
    return codegen_ast2ir_exp(ctx, expstmt.exp)

def codegen_ast2ir_blkstmt(ctx: CodegenContext, blkstmt: c_ast.BlkStmt) -> list[IR]:
    ctx.enter_scope(blkstmt)
    irs: list[IR] = []
    for stmt in blkstmt.stmts:
        irs.extend(codegen_ast2ir_stmt(ctx, stmt))
    ctx.exit_scope()
    return irs

def codegen_ast2ir_vardefsstmt(ctx: CodegenContext, vardefs: c_ast.VarDefsStmt) -> list[IR]:
    irs: list[IR] = []
    for vardef in vardefs.var_describes:
        irs.extend(codegen_ast2ir_vardef(ctx, vardef))
    return irs

def codegen_ast2ir_vardef(ctx: CodegenContext, vardescribe: c_ast.VarDescribe) -> list[IR]:
    #vardescribe 是 NormalVarDescribe
    if isinstance(vardescribe, c_ast.NormalVarDescribe):
        if vardescribe.init is not None:
            irs: list[IR] = codegen_ast2ir_exp(ctx, vardescribe.init)
            irs.append(SD(Register(RegNo.A0), str(-ctx.query_var(vardescribe.name.value)), Register(RegNo.FP)))
            return irs
        return []
    if isinstance(vardescribe, c_ast.FuncVarDescribe):
        pass
    if isinstance(vardescribe, c_ast.AryVarDescribe):
        # 不需要做什么
        return []
    # if isinstance(vardescribe, c_ast.PtrVarDe)
    raise Exception('')

# 现在有个问题 return 的 正文不需要跳转
def codegen_ast2ir_retstmt(ctx: CodegenContext, ret: c_ast.RetStmt) -> list[IR]:
    irs: list[IR] = []
    if ret.value:
        irs.extend(codegen_ast2ir_exp(ctx, ret.value))
    irs.append(J(f'.L.{ctx.func_name}.return'))
    return irs

def codegen_ast2ir_ifstmt(ctx: CodegenContext, ifstmt: c_ast.IfStmt) -> list[IR]:
    irs: list[IR] = []
    # 1.生成条件表达式
    irs.extend(codegen_ast2ir_exp(ctx, ifstmt.cond))
    # 2.构造if标签
    (false_label, end_label) = ctx.gen_if_labels()
    # 3.生成跳转到false分支的语句
    irs.append(BEQZ(Register(RegNo.A0), false_label))
    # 4.生成true分支
    irs.extend(codegen_ast2ir_stmt(ctx, ifstmt.t))
    # 5.生成跳转到end的语句
    irs.append(J(end_label))
    # 6.生成false标签
    irs.append(Label(false_label))
    if ifstmt.f:
        # 如果false分支存在 就生成主体
        irs.extend(codegen_ast2ir_stmt(ctx, ifstmt.f))
    # 7.生成end标签
    irs.append(Label(end_label))
    return irs

def codegen_ast2ir_forstmt(ctx: CodegenContext, forstmt: c_ast.ForStmt) -> list[IR]:
    irs: list[IR] = []
    # 1.如果init存在 生成init
    if forstmt.init:
        if isinstance(forstmt.init, c_ast.VarDefsStmt):
            irs.extend(codegen_ast2ir_vardefsstmt(ctx, forstmt.init))
        else:
            irs.extend(codegen_ast2ir_exp(ctx, forstmt.init))
    # 2.构造标签
    (cond, step, end) = ctx.gen_for_labels()
    # 3.生成条件标签
    irs.append(Label(cond))
    # 4.生成条件求值 如果条件存在则生成 默认是1
    irs.append(LI(Register(RegNo.A0), '1'))
    if forstmt.cond:
        irs.extend(codegen_ast2ir_exp(ctx, forstmt.cond))
    # 5.生成跳转到end的语句
    irs.append(BEQZ(Register(RegNo.A0), end))
    # 6.生成主体
    irs.extend(codegen_ast2ir_stmt(ctx, forstmt.body))
    # 7.生成step标签
    irs.append(Label(step))
    # 8.生成step
    if forstmt.step:
        irs.extend(codegen_ast2ir_exp(ctx, forstmt.step))
    # 9.生成跳转到cond的语句
    irs.append(J(cond))
    # 10.生成end标签
    irs.append(Label(end))
    return irs

def codegen_ast2ir_whilestmt(ctx: CodegenContext, whilestmt: c_ast.WhileStmt) -> list[IR]:
    irs: list[IR] = []
    # 1.构造标签
    (cond, end) = ctx.gen_while_labels()
    # 2.生成cond标签
    irs.append(Label(cond))
    # 3.生成条件语句
    irs.extend(codegen_ast2ir_exp(ctx, whilestmt.cond))
    # 4.生成跳转到end的语句
    irs.append(BEQZ(Register(RegNo.A0), end))
    # 5.生成主体
    irs.extend(codegen_ast2ir_stmt(ctx, whilestmt.body))
    # 6.生成跳转到cond的语句
    irs.append(J(cond))
    # 7.生成end标签
    irs.append(Label(end))
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
def codegen_address(ctx: CodegenContext, to_address: str|c_ast.Exp) -> list[IR]:
    if isinstance(to_address, str):
        irs: List[IR] = []
        irs.append(ADDI(Register(RegNo.A0), Register(RegNo.FP), str(-ctx.query_var(to_address))))
        return irs
    if isinstance(to_address, c_ast.Idt):
        irs: List[IR] = []
        # 最终生成的地址
        if to_address.type is None:
            raise Exception('')
        if to_address.type.glb:
            irs.append(LA(Register(RegNo.A0), to_address.idt.value))
            return irs
        irs.append(ADDI(Register(RegNo.A0), Register(RegNo.FP), str(-ctx.query_var(to_address.idt.value))))
        return irs
    if isinstance(to_address, c_ast.UExp) and to_address.op == c_ast.UOp.DEREF:
        irs: List[IR] = []
        # 对子表达式求值
        irs.extend(codegen_ast2ir_exp(ctx, to_address.exp))
        return irs
    raise Exception(f'can not be addressed: {to_address}')

def codegen_ast2ir_exp(ctx: CodegenContext, exp: c_ast.Exp) -> list[IR]:
    if exp.type is None:
        raise Exception('')
    result: list[IR] = []
    if isinstance(exp, c_ast.Num):
        result.append(LI(Register(RegNo.A0), str(exp.value)))
        return result
    elif isinstance(exp, c_ast.BinExp):
        # 赋值表达式单独进行处理
        if exp.op == c_ast.BinOp.ASN:
            # 任何有左地址的都可以进行赋值运算
            # if not isinstance(exp.l, c_ast.Idt):
            #     raise Exception('')
            # 1.生成左子表达式的地址
            result.extend(codegen_address(ctx, exp.l))
            # result.append(LI(Register(RegNo.A0), str(-ctx.query_var(exp.l.idt.value))))
            # 2.a0压栈
            result.extend(codegen_ast2ir_reg_save(Register(RegNo.A0)))
            # result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
            # result.append(SD(Register(RegNo.A0), '0', Register(RegNo.SP)))
            # 3.生成右子表达式的值
            result.extend(codegen_ast2ir_exp(ctx, exp.r))
            # 4.出栈到a1
            result.extend(codegen_ast2ir_reg_load(Register(RegNo.A1)))
            # result.append(LD(Register(RegNo.A1), '0', Register(RegNo.SP)))
            # result.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
            # 5.sd a0, 0(a1)
            result.append(SD(Register(RegNo.A0), '0', Register(RegNo.A1)))
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
        if exp.op == c_ast.BinOp.ADD:
            result.append(ADD(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.SUB:
            result.append(SUB(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.MUL:
            result.append(MUL(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.DIV:
            result.append(DIV(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.EQ:
            result.append(XOR(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(SEQZ(Register(RegNo.A0), Register(RegNo.A0)))
        elif exp.op == c_ast.BinOp.NE:
            result.append(XOR(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        elif exp.op == c_ast.BinOp.LT:
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.LE:
            # a0 <= a1 翻译为 a0 > a1 结果取反
            # a1 > a0
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
            result.append(XORI(Register(RegNo.A0), Register(RegNo.A0), '1'))
        elif exp.op == c_ast.BinOp.GT:
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
        elif exp.op == c_ast.BinOp.GE:
            # a0 >= a1 翻译为 a0 < a1 结果取反
            # a1 > a0
            result.append(SLT(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            result.append(XORI(Register(RegNo.A0), Register(RegNo.A0), '1'))
        else:
            raise Exception('')
    elif isinstance(exp, c_ast.UExp):
        if exp.op == c_ast.UOp.ADD:
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
        elif exp.op == c_ast.UOp.SUB:
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            result.append(LI(Register(RegNo.A1), '0'))
            result.append(SUB(Register(RegNo.A0), Register(RegNo.A1), Register(RegNo.A0)))
        elif exp.op == c_ast.UOp.REF:
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            result.extend(codegen_address(ctx, exp.exp))
        elif exp.op == c_ast.UOp.DEREF:# 那么问题就在于 任何情况下deref都应当直接load吗
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            if isinstance(exp.type, ctype.Ary):
                pass
            else:
                result.append(LD(Register(RegNo.A0), '0', Register(RegNo.A0)))
        elif exp.op == c_ast.UOp.SIZEOF:
            if exp.exp.type is None:
                raise Exception('')
            t = exp.exp.type.length()
            result.append(LI(Register(RegNo.A0), str(t)))
        else:
            raise Exception('')
    elif isinstance(exp, c_ast.Idt):
        # 我们要解决的问题是 变量的load应当被提出来到一个单独的逻辑中
        result.extend(codegen_address(ctx, exp))
        result.extend(codegen_ast2ir_load(exp.type))
    elif isinstance(exp, c_ast.Call):
        # 1.准备参数
        for inarg in exp.inargs:
            result.extend(codegen_ast2ir_exp(ctx, inarg))
            # 压栈
            result.extend(codegen_ast2ir_reg_save(Register(RegNo.A0)))
        # 2.反向出栈
        for i in range(len(exp.inargs)-1, -1, -1):
            reg = list(RegNo)[i]
            result.extend(codegen_ast2ir_reg_load(Register(reg)))
        # 3.生成调用标签
        if not isinstance(exp.func_source, c_ast.Idt):
            raise Exception('')
        result.append(CALL(exp.func_source.idt.value))
    else:
        raise Exception('')
    return result

def codegen_ast2ir_load(t: ctype.CType) -> list[IR]:
    if isinstance(t, ctype.I64) or isinstance(t, ctype.I32):
        return [LD(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if isinstance(t, ctype.Ptr):
        return [LD(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if isinstance(t, ctype.Ary):
        return []
    raise Exception('')

def codegen_ast2ir_retcontent(ctx: CodegenContext) -> list[IR]:
    # 返回的操作
    # 1.sp = fp
    # 2.fp出栈
    # 3.ra出栈
    # 4.ret
    irs: list[IR] = [
        Label(f'.L.{ctx.func_name}.return'),
        ADDI(Register(RegNo.SP), Register(RegNo.SP), str(ctx.frame_length)),
        MV(Register(RegNo.SP), Register(RegNo.FP)),
    ]
    irs.extend(codegen_ast2ir_reg_load(Register(RegNo.FP)))
    irs.extend(codegen_ast2ir_reg_load(Register(RegNo.RA)))
    irs.append(RET())
    return irs

def codegen_ast2ir(ast: list[c_ast.VarDefsStmt]) -> list[IR]:
    ctx = CodegenContext()
    irs: list[IR] = []
    for item in ast:
        irs.extend(codegen_ast2ir_global_vardefs(ctx, item))
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
            elif isinstance(ir, BEQZ):
                code += f"    beqz {ir.src.no.name.lower()}, {ir.dest}\n"
            elif isinstance(ir, CALL):
                code += f"    call {ir.dest}\n"
            elif isinstance(ir, MV):
                code += f"    mv {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, LA):
                code += f"    la {ir.dest.no.name.lower()}, {ir.label}\n"
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
    return code

def codegen(ast: list[c_ast.VarDefsStmt]) -> str:
    irs = codegen_ast2ir(ast)
    code = codegen_ir2asm(irs)
    return code
