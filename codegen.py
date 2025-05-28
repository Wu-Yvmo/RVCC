import c_ast
import c_type
from ir import *
from typing import * # type: ignore

import utils
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

# 我觉得应该考虑把代码生成和全局变量生成分开算
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
        # 字符串常量
        # .0 原始字符串 .1字符串标签
        self.str_labels: dict[str, str] = {}
        # 字符串计数器
        self.str_counter = 0
    
    def init_frame_length(self, vardefs: c_ast.VarDefsStmt):
        # 现在是对整个函数进行初始化
        # 要对传入的参数也进行编址
        functype = vardefs.var_describes[0].get_type()
        if not isinstance(functype, c_type.Func):
            raise Exception('')
        frame_0: list[varinfo.VarInfo] = []
        # 这里必须获得FuncVarDescribe 应当进行特殊处理 难搞 给函数类型中添加名称字段
        for param in functype.args:
            vi = varinfo.VarInfo(param[0])
            vi.t = param[1]
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
        # 按照测试用例的要求，变量在栈上的存储方式是类似数组的
        # 什么情况？你差不多得了奥
        for varinfo in blkstmt.varinfos[::-1]:
            if varinfo.t is None:
                raise Exception('')
            self.frame_length += varinfo.t.length()
            self.frame_length = utils.align2(self.frame_length, varinfo.t.align())
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
                if isinstance(stmt.init, c_ast.VarDefsStmt):
                    for varinfo in stmt.varinfos[::-1]:
                        if varinfo.t is None:
                            raise Exception('')
                        self.frame_length += varinfo.t.length()
                        self.frame_length = utils.align2(self.frame_length, varinfo.t.align())
                        varinfo.offset = self.frame_length
                if isinstance(stmt.body, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.body)
            elif isinstance(stmt, c_ast.WhileStmt):
                if isinstance(stmt.body, c_ast.BlkStmt):
                    self.__init_frame_length_blkstmt(stmt.body)
            elif isinstance(stmt, c_ast.RetStmt):
                if stmt.value is not None:
                    self.__init_frame_length_exp(stmt.value)
            elif isinstance(stmt, c_ast.ExpStmt):
                # 表达式也要进行变量扫描
                self.__init_frame_length_exp(stmt.exp)
        self.frame_length = utils.align2(self.frame_length, 16)
    
    def __init_frame_length_exp(self, exp: c_ast.Exp):
        if isinstance(exp, c_ast.BinExp):
            self.__init_frame_length_exp(exp.l)
            self.__init_frame_length_exp(exp.r)
        elif isinstance(exp, c_ast.UExp):
            # 只有sizeof的右侧会出现Stmt 不需要分配内存
            if isinstance(exp.exp, c_ast.Stmt):
                if isinstance(exp.exp, c_ast.VarDefsStmt):
                    pass
            else:
                self.__init_frame_length_exp(exp.exp)
        elif isinstance(exp, c_ast.BlkExp):
            if not isinstance(exp.stmt, c_ast.BlkStmt):
                raise Exception('')
            self.__init_frame_length_blkstmt(exp.stmt)
        elif isinstance(exp, c_ast.Call):
            self.__init_frame_length_exp(exp.func_source)
            for arg in exp.inargs:
                self.__init_frame_length_exp(arg)
        elif isinstance(exp, c_ast.CastExp):
            self.__init_frame_length_exp(exp.exp)
    
    def enter_scope(self, varinfos: list[varinfo.VarInfo]):
        self.frame_tracker.append(varinfos)

    def exit_scope(self):
        self.frame_tracker.pop()

    def query_var(self, name: str) -> int:
        for frame in self.frame_tracker[::-1]:
            for vi in frame:
                if vi.name == name:
                    return vi.offset
        raise Exception(f'{name} not match')
    
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

# 函数定义的代码生成
def codegen_ast2ir_code_emit(ctx: CodegenContext, vardefsstmts: list[c_ast.VarDefsStmt]) -> list[IR]:
    irs: list[IR] = [PreOrder('text', '')]
    for vardefs in vardefsstmts:
        # 跳过所有非函数定义的item 这里有问题
        if not (len(vardefs.var_describes) == 1 and vardefs.var_describes[0].body is not None):
            continue
        # 处理函数定义
        ctx.func_name = vardefs.var_describes[0].get_name()
        # 生成全局声明和函数开头
        # 如果函数返回值有static修饰 就不提供.globl修饰
        ft = vardefs.var_describes[0].get_type()
        if not isinstance(ft, c_type.Func):
            raise Exception('')
        # 如果main的ret类型有static修饰 就不生成globl标签
        if not ft.ret.static:
            irs.append(PreOrder('globl', vardefs.var_describes[0].get_name()))
        irs.append(Label(vardefs.var_describes[0].get_name()))
        # 2.生成函数入口的保存操作
        #   ra寄存器压栈
        irs.extend(codegen_ast2ir_reg_push(Register(RegNo.RA)))
        #   fp寄存器压栈
        irs.extend(codegen_ast2ir_reg_push(Register(RegNo.FP)))
        #   sp复制到fp中
        irs.append(MV(Register(RegNo.FP), Register(RegNo.SP)))
        # 初始化栈帧
        if not isinstance(vardefs.var_describes[0].get_type(), c_type.Func):
            raise Exception('')
        # if vardefs.var_describes[0].body is None:
        #     raise Exception('')
        ctx.init_frame_length(vardefs)
        # sp按照当前的栈帧大小对齐后增长
        irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), str(-ctx.frame_length)))
        # 把寄存器中的内容复制到栈帧中
        # 具体的执行办法是：a0到a6全部压栈
        # 然后依次出栈到a0
        # 然而不是所有的函数定义都以函数描述收场
        functype = vardefs.var_describes[0].get_type()
        if not isinstance(functype, c_type.Func):
            raise Exception('')
        for i in range(len(functype.args)):
            reg = list(RegNo)[i]
            irs.extend(codegen_ast2ir_reg_push(Register(reg)))
        for i in range(len(functype.args))[::-1]:
            # 生成变量地址
            irs.extend(codegen_address(ctx, functype.args[i][0]))
            # 将变量地址移动到a1
            irs.append(MV(Register(RegNo.A1), Register(RegNo.A0)))
            irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.A0)))
            # 将变量的值存储到0(a1)中
            # 获取当前param的类型
            t = functype.args[i][1]
            irs.extend(codegen_ast2ir_store(t))
        # 3.生成函数体
        irs.extend(codegen_ast2ir_stmt(ctx, vardefs.var_describes[0].body))
        # 4.生成ret逻辑
        irs.extend(codegen_ast2ir_retcontent(ctx))
    return irs

def codegen_ast2ir_data_emit(ctx: CodegenContext, vardefsstmts: list[c_ast.VarDefsStmt]) -> list[IR]:
    irs: list[IR] = [PreOrder('data', '')]
    for vardefsstmt in vardefsstmts:
        # 一个问题是 我们现在要考虑研究一下函数声明
        # 如果不是函数定义
        if not vardefsstmt.is_funcdef():
            irs.extend(codegen_ast2ir_data_emit_glbvars(ctx, vardefsstmt))
        irs.extend(codegen_ast2ir_data_emit_str_vardefsstmt(ctx, vardefsstmt))
    return irs

# 思考：我们的函数将如何被调用？
# 思路：作为单独的data_emit
# 也就是说 入口是从vardefsstmt入的
# 下面几个函数主要用来扫描生成所有的字符串标签
def codegen_ast2ir_data_emit_str_stmt(ctx: CodegenContext, stmt: c_ast.Stmt) -> list[IR]:
    if isinstance(stmt, c_ast.BlkStmt):
        return codegen_ast2ir_data_emit_str_blkstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.VarDefsStmt):
        return codegen_ast2ir_data_emit_str_vardefsstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.RetStmt):
        return codegen_ast2ir_data_emit_str_retstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.IfStmt):
        return codegen_ast2ir_data_emit_str_ifstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.ForStmt):
        return codegen_ast2ir_data_emit_str_forstmt(ctx, stmt)
    elif isinstance(stmt, c_ast.WhileStmt):
        return codegen_ast2ir_data_emit_str_whilestmt(ctx, stmt)
    elif isinstance(stmt, c_ast.ExpStmt):
        return codegen_ast2ir_data_emit_str_expstmt(ctx, stmt)
    raise Exception('')

def codegen_ast2ir_data_emit_str_blkstmt(ctx: CodegenContext, blkstmt: c_ast.BlkStmt) -> list[IR]:
    irs: list[IR] = []
    for stmt in blkstmt.stmts:
        if isinstance(stmt, c_ast.TypedefStmt):
            continue
        irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, stmt))
    return irs

def codegen_ast2ir_data_emit_str_vardefsstmt(ctx: CodegenContext, vardefsstmt: c_ast.VarDefsStmt) -> list[IR]:
    irs: list[IR] = []
    # 函数定义
    if vardefsstmt.is_funcdef():
        if not isinstance(vardefsstmt.var_describes[0], c_ast.FuncVarDescribe) or vardefsstmt.var_describes[0].body is None:
            raise Exception('')
        body = vardefsstmt.var_describes[0].body
        irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, body))
        return irs
    # 变量定义
    for vardescribe in vardefsstmt.var_describes:
        if vardescribe.init is None:
            continue
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, vardescribe.init))
    return irs

def codegen_ast2ir_data_emit_str_retstmt(ctx: CodegenContext, ifstmt: c_ast.RetStmt) -> list[IR]:
    if ifstmt.value is None:
        return []
    return codegen_ast2ir_data_emit_str_exp(ctx, ifstmt.value)

def codegen_ast2ir_data_emit_str_ifstmt(ctx: CodegenContext, ifstmt: c_ast.IfStmt) -> list[IR]:
    irs: list[IR] = []
    irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, ifstmt.cond))
    irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, ifstmt.t))
    if ifstmt.f is not None:
        irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, ifstmt.f))
    return irs

def codegen_ast2ir_data_emit_str_forstmt(ctx: CodegenContext, forstmt: c_ast.ForStmt) -> list[IR]:
    irs: list[IR] = []
    if forstmt.init is not None:
        if isinstance(forstmt.init, c_ast.VarDefsStmt):
            irs.extend(codegen_ast2ir_data_emit_str_vardefsstmt(ctx, forstmt.init))
        elif isinstance(forstmt.init, c_ast.ExpStmt):
            irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, forstmt.init))
    if forstmt.cond is not None:
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, forstmt.cond))
    if forstmt.step is not None:
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, forstmt.step))
    irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, forstmt.body))
    return irs

def codegen_ast2ir_data_emit_str_whilestmt(ctx: CodegenContext, whilestmt: c_ast.WhileStmt) -> list[IR]:
    irs: list[IR] = []
    irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, whilestmt.cond))
    irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, whilestmt.body))
    return irs

def codegen_ast2ir_data_emit_str_expstmt(ctx: CodegenContext, expstmt: c_ast.ExpStmt) -> list[IR]:
    irs: list[IR] = []
    irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, expstmt.exp))
    return irs

def codegen_ast2ir_data_emit_str_exp(ctx: CodegenContext, exp: c_ast.Exp) -> list[IR]:
    if isinstance(exp, c_ast.Num):
        return []
    if isinstance(exp, c_ast.Str):
        irs: list[IR] = []
        if ctx.str_labels.get(exp.value) is not None:
            return []
        ctr = ctx.str_counter
        ctx.str_counter += 1
        str_label = f".L.str.{ctr}"
        ctx.str_labels[exp.value] = str_label
        irs.append(Label(str_label))
        for c in exp.value:
            irs.append(PreOrder('byte', f'{ord(c)}'))
        irs.append(PreOrder('byte', '0'))
        return irs
    if isinstance(exp, c_ast.BinExp):
        irs: list[IR] = []
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, exp.l))
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, exp.r))
        return irs
    if isinstance(exp, c_ast.UExp):
        # sizeof的变量不需要扫描字符串
        if isinstance(exp.exp, c_ast.Stmt):
            return []
        return codegen_ast2ir_data_emit_str_exp(ctx, exp.exp)
    if isinstance(exp, c_ast.Idt):
        return []
    # 为调用生成字符串IR
    if isinstance(exp, c_ast.Call):
        irs: list[IR] = []
        for inarg in exp.inargs:
            irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, inarg))
        return irs
    # 为语句表达式生成字符串IR
    if isinstance(exp, c_ast.BlkExp):
        irs: list[IR] = []
        irs.extend(codegen_ast2ir_data_emit_str_stmt(ctx, exp.stmt))
        return irs
    # 为类型转换表达式生成字符串IR
    if isinstance(exp, c_ast.CastExp):
        irs: list[IR] = []
        irs.extend(codegen_ast2ir_data_emit_str_exp(ctx, exp.exp))
        return irs
    if isinstance(exp, c_ast.Ltr):
        return []
    raise Exception('shouldn not run')

# 生成全局变量
def codegen_ast2ir_data_emit_glbvars(ctx: CodegenContext, vardefs: c_ast.VarDefsStmt) -> list[IR]:
    irs: list[IR] = []
    for vardescribe in vardefs.var_describes:
        # 遇到函数定义或声明时不生成 因为没什么好生成的
        if isinstance(vardescribe.get_type(), c_type.Func):
            continue
        irs.append(PreOrder('globl', f'{vardescribe.get_name()}'))
        irs.append(Label(f'{vardescribe.get_name()}'))
        irs.append(PreOrder('zero', f'{vardescribe.get_type().length()}'))
    return irs

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
    elif isinstance(stmt, c_ast.TypedefStmt):
        return []
    raise Exception('')

def codegen_ast2ir_expstmt(ctx: CodegenContext, expstmt: c_ast.ExpStmt) -> list[IR]:
    return codegen_ast2ir_exp(ctx, expstmt.exp)

def codegen_ast2ir_blkstmt(ctx: CodegenContext, blkstmt: c_ast.BlkStmt) -> list[IR]:
    ctx.enter_scope(blkstmt.varinfos)
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
            # 1. 生成初始化语句
            irs: list[IR] = []
            # 生成地址
            irs.extend(codegen_address(ctx, vardescribe.get_name()))
            # 压栈
            irs.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
            # 生成初始化值
            irs.extend(codegen_ast2ir_exp(ctx, vardescribe.init))
            # 出栈到a1
            irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.A1)))
            # 生成存储语句
            irs.extend(codegen_ast2ir_store(vardescribe.get_type()))
            return irs
        return []
    if isinstance(vardescribe, c_ast.FuncVarDescribe):
        pass
    if isinstance(vardescribe, c_ast.AryVarDescribe):
        if vardescribe.init is not None:
            # 1. 生成初始化语句
            irs: list[IR] = []
            # 生成地址
            irs.extend(codegen_address(ctx, vardescribe.get_name()))
            # 压栈
            irs.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
            # 生成初始化值
            irs.extend(codegen_ast2ir_exp(ctx, vardescribe.init))
            # 出栈到a1
            irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.A1)))
            # 生成存储语句
            irs.extend(codegen_ast2ir_store(vardescribe.get_type()))
            return irs
        return []
    if isinstance(vardescribe, c_ast.PtrVarDescribe):
        if vardescribe.init is not None:
            # 1. 生成初始化语句
            irs: list[IR] = []
            # 生成地址
            irs.extend(codegen_address(ctx, vardescribe.get_name()))
            # 压栈
            irs.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
            # 生成初始化值
            irs.extend(codegen_ast2ir_exp(ctx, vardescribe.init))
            # 出栈到a1
            irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.A1)))
            # 生成存储语句
            irs.extend(codegen_ast2ir_store(vardescribe.get_type()))
            return irs
        return []
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
    ctx.enter_scope(forstmt.varinfos)
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
    ctx.exit_scope()
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
def codegen_ast2ir_reg_push(reg: Register) -> list[IR]:
    irs: list[IR] = []
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '-8'))
    irs.append(SD(reg, '0', Register(RegNo.SP)))
    return irs

# 寄存器出栈
def codegen_ast2ir_reg_pop(reg: Register) -> list[IR]:
    irs: list[IR] = []
    irs.append(LD(reg, '0', Register(RegNo.SP)))
    irs.append(ADDI(Register(RegNo.SP), Register(RegNo.SP), '8'))
    return irs

# 为变量名和表达式提供寻址
def codegen_address(ctx: CodegenContext, to_address: str|c_ast.Exp) -> list[IR]:
    # 只有函数入参求值时会用到这个case
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
        if isinstance(to_address.exp, c_ast.Stmt):
            raise Exception('')
        irs.extend(codegen_ast2ir_exp(ctx, to_address.exp))
        return irs
    if isinstance(to_address, c_ast.BinExp) and to_address.op == c_ast.BinOp.COMMA:
        irs: List[IR] = []
        # 我们一般认为只有执行.l的表达式后才可能形成.r的正确地址
        irs.extend(codegen_ast2ir_exp(ctx, to_address.l))
        # 生成右子表达式的地址
        irs.extend(codegen_address(ctx, to_address.r))
        return irs
    if isinstance(to_address, c_ast.BinExp) and to_address.op == c_ast.BinOp.ACS:
        irs: List[IR] = []
        # 1.生成左子表达式的地址
        irs.extend(codegen_address(ctx, to_address.l))
        if not isinstance(to_address.r, c_ast.Idt):
            raise Exception('')
        # 是union就不需要求偏移地址了
        if isinstance(to_address.l.type, c_type.CUnion):
            return irs
        if not isinstance(to_address.l.type, c_type.CStruct):
            raise Exception('')
        # 加 上 成员的 偏移量
        irs.append(ADDI(Register(RegNo.A0), Register(RegNo.A0), str(to_address.l.type.offset(to_address.r.idt.value))))
        return irs
    raise Exception(f'can not be addressed: {to_address}')

def should_use_64bit(t: c_type.CType) -> bool:
    return isinstance(t, c_type.Ptr) or isinstance(t, c_type.Ary) or isinstance(t, c_type.I64)

def codegen_ast2ir_exp(ctx: CodegenContext, exp: c_ast.Exp) -> list[IR]:
    if exp.type is None:
        raise Exception(f'{exp}')
    result: list[IR] = []
    if isinstance(exp, c_ast.Num):
        result.append(LI(Register(RegNo.A0), str(exp.value)))
        return result
    elif isinstance(exp, c_ast.BlkExp):
        result.extend(codegen_ast2ir_stmt(ctx, exp.stmt))
        return result
    elif isinstance(exp, c_ast.BinExp):
        # 赋值表达式单独进行处理
        if exp.op == c_ast.BinOp.ASN:
            # 任何有左地址的都可以进行赋值运算
            # 1.生成左子表达式的地址
            result.extend(codegen_address(ctx, exp.l))
            # 2.a0压栈
            result.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
            # 3.生成右子表达式的值
            result.extend(codegen_ast2ir_exp(ctx, exp.r))
            # 4.出栈到a1
            result.extend(codegen_ast2ir_reg_pop(Register(RegNo.A1)))
            # 5.此时：a0寄存器保存运算结果 a1寄存器保存左子表达式的地址 操作：按照左子表达式的类型，将a0寄存器中的内容存储到内存中
            if exp.l.type is None:
                raise Exception('')
            result.extend(codegen_ast2ir_store(exp.l.type))
            return result
        if exp.op == c_ast.BinOp.ACS and isinstance(exp.l.type, c_type.CStruct):
            result.extend(codegen_address(ctx, exp))
            result.extend(codegen_ast2ir_load(exp.type))
            return result
        if exp.op == c_ast.BinOp.ACS and isinstance(exp.l.type, c_type.CUnion):
            result.extend(codegen_address(ctx, exp))
            result.extend(codegen_ast2ir_load(exp.type))
            return result
        # 1.生成右子表达式
        result.extend(codegen_ast2ir_exp(ctx, exp.r))
        # 2.入栈a0
        result.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
        # 2.生成左子表达式
        result.extend(codegen_ast2ir_exp(ctx, exp.l))
        # 出栈到a1
        result.extend(codegen_ast2ir_reg_pop(Register(RegNo.A1)))
        # 运算
        # 应当从运算的结果来考虑。如果运算结果是：long ptr ary，那么就应当选择64位指令
        if exp.op == c_ast.BinOp.ADD:
            if should_use_64bit(exp.type):
                result.append(ADD(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            else:
                result.append(ADDW(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.SUB:
            if should_use_64bit(exp.type):
                result.append(SUB(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            else:
                result.append(SUBW(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.MUL:
            if should_use_64bit(exp.type):
                result.append(MUL(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            else:
                result.append(MULW(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
        elif exp.op == c_ast.BinOp.DIV:
            if should_use_64bit(exp.type):
                result.append(DIV(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
            else:
                result.append(DIVW(Register(RegNo.A0), Register(RegNo.A0), Register(RegNo.A1)))
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
        elif exp.op == c_ast.BinOp.COMMA:
            # 因为执行后的结果是 左子表达式在a0 右子表达式在a1 所以执行一个MV指令
            result.append(MV(Register(RegNo.A0), Register(RegNo.A1)))
        else:
            raise Exception('')
    elif isinstance(exp, c_ast.UExp):
        # 额外处理 exp和其他的情况 是不是应该在parse阶段就完成sizeof的求值？
        if exp.op == c_ast.UOp.ADD:
            if not isinstance(exp.exp, c_ast.Exp):
                raise Exception('')
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
        elif exp.op == c_ast.UOp.SUB:
            if not isinstance(exp.exp, c_ast.Exp):
                raise Exception('')
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            if should_use_64bit(exp.type):
                result.append(NEG(Register(RegNo.A0), Register(RegNo.A0)))
            else:
                result.append(NEGW(Register(RegNo.A0), Register(RegNo.A0)))
        elif exp.op == c_ast.UOp.REF:
            if not isinstance(exp.exp, c_ast.Exp):
                raise Exception('')
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            result.extend(codegen_address(ctx, exp.exp))
        elif exp.op == c_ast.UOp.DEREF: # 那么问题就在于 任何情况下deref都应当直接load吗
            if not isinstance(exp.exp, c_ast.Exp):
                raise Exception('')
            result.extend(codegen_ast2ir_exp(ctx, exp.exp))
            if isinstance(exp.type, c_type.Ary):
                pass
            else:
                result.extend(codegen_ast2ir_load(exp.type))
        elif exp.op == c_ast.UOp.SIZEOF:
            t = None
            if isinstance(exp.exp, c_ast.Exp):
                if exp.exp.type is None:
                    raise Exception('')
                t = exp.exp.type.length()
            elif isinstance(exp.exp, c_ast.VarDefsStmt):
                t = exp.exp.var_describes[0].get_type().length()
            else:
                raise Exception('')
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
            result.extend(codegen_ast2ir_reg_push(Register(RegNo.A0)))
        # 2.反向出栈
        for i in range(len(exp.inargs)-1, -1, -1):
            reg = list(RegNo)[i]
            result.extend(codegen_ast2ir_reg_pop(Register(reg)))
        # 3.生成调用标签
        if not isinstance(exp.func_source, c_ast.Idt):
            raise Exception('')
        result.append(CALL(exp.func_source.idt.value))
    # 行为：加载字符串的地址到a0寄存器中
    elif isinstance(exp, c_ast.Str):
        result.append(LA(Register(RegNo.A0), ctx.str_labels[exp.value]))
    elif isinstance(exp, c_ast.CastExp):
        # 为类型转换生成代码
        # 生成子表达式
        irs = codegen_ast2ir_exp(ctx, exp.exp)
        # 只有从大转小的时候需要额外处理 因为扩增会在寄存器中自动完成
        conv_ir_table: dict[str, list[IR]] = {
            'i64->i32': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '32'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '32')
            ],
            'i64->i16': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '48'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '48')
            ],
            'i64->i8': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '56'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '56')
            ],
            'i32->i16': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '48'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '48')
            ],
            'i32->i8': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '56'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '56')
            ],
            'i16->i8': [
                SLLI(Register(RegNo.A0), Register(RegNo.A0), '56'),
                SRAI(Register(RegNo.A0), Register(RegNo.A0), '56')
            ]
        }
        # long -> int
        if isinstance(exp.cast_to, c_type.I32) and isinstance(exp.exp.type, c_type.I64):
            irs.extend(conv_ir_table['i64->i32'])
        # long -> short
        elif isinstance(exp.cast_to, c_type.I16) and isinstance(exp.exp.type, c_type.I64):
            irs.extend(conv_ir_table['i64->i16'])
        # long -> char
        elif isinstance(exp.cast_to, c_type.I8) and isinstance(exp.exp.type, c_type.I64):
            irs.extend(conv_ir_table['i64->i8'])
        # long -> _Bool
        elif isinstance(exp.cast_to, c_type.Bool) and isinstance(exp.exp.type, c_type.I64):
            irs.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        # int -> short
        elif isinstance(exp.cast_to, c_type.I16) and isinstance(exp.exp.type, c_type.I32):
            irs.extend(conv_ir_table['i32->i16'])
        # int -> char
        elif isinstance(exp.cast_to, c_type.I8) and isinstance(exp.exp.type, c_type.I32):
            irs.extend(conv_ir_table['i32->i8'])
        # int -> _Bool
        elif isinstance(exp.cast_to, c_type.Bool) and isinstance(exp.exp.type, c_type.I32):
            irs.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        # short -> char
        elif isinstance(exp.cast_to, c_type.I8) and isinstance(exp.exp.type, c_type.I16):
            irs.extend(conv_ir_table['i16->i8'])
        # short -> _Bool
        elif isinstance(exp.cast_to, c_type.Bool) and isinstance(exp.exp.type, c_type.I16):
            irs.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        # char -> _Bool
        elif isinstance(exp.cast_to, c_type.Bool) and isinstance(exp.exp.type, c_type.I8):
            irs.append(SNEZ(Register(RegNo.A0), Register(RegNo.A0)))
        return irs
    elif isinstance(exp, c_ast.Ltr):
        result.append(LI(Register(RegNo.A0), str(ord(exp.value[0]))))
        pass
    else:
        raise Exception('')
    return result

def codegen_ast2ir_load(t: c_type.CType) -> list[IR]:
    if isinstance(t, c_type.CStruct) or isinstance(t, c_type.CUnion) or isinstance(t, c_type.Ary):
        return []
    if isinstance(t, c_type.Ptr):
        return [LD(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if t.length() == 8:
        return [LD(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if t.length() == 4:
        return [LW(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if t.length() == 2:
        return [LH(Register(RegNo.A0), '0', Register(RegNo.A0))]
    if t.length() == 1:
        return [LB(Register(RegNo.A0), '0', Register(RegNo.A0))]
    raise Exception('')

# 默认要存储的值在a0中 而地址在a1中
def codegen_ast2ir_store(t: c_type.CType) -> list[IR]:
    if isinstance(t, c_type.CStruct) or isinstance(t, c_type.CUnion):
        irs: list[IR] = []
        for i in range(t.length()):
            irs.append(LI(Register(RegNo.T0), str(i)))
            irs.append(ADD(Register(RegNo.T0), Register(RegNo.A0), Register(RegNo.T0)))
            irs.append(LB(Register(RegNo.T1), '0', Register(RegNo.T0)))
            irs.append(LI(Register(RegNo.T0), str(i)))
            irs.append(ADD(Register(RegNo.T0), Register(RegNo.A1), Register(RegNo.T0)))
            irs.append(SB(Register(RegNo.T1), '0', Register(RegNo.T0)))
        return irs
    if t.length() == 8:
        return [SD(Register(RegNo.A0), '0', Register(RegNo.A1))]
    if t.length() == 4:
        return [SW(Register(RegNo.A0), '0', Register(RegNo.A1))]
    if t.length() == 2:
        return [SH(Register(RegNo.A0), '0', Register(RegNo.A1))]
    if t.length() == 1:
        return [SB(Register(RegNo.A0), '0', Register(RegNo.A1))]
    raise Exception(f'fuck, type is: {t}')

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
    irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.FP)))
    irs.extend(codegen_ast2ir_reg_pop(Register(RegNo.RA)))
    irs.append(RET())
    return irs

def codegen_ast2ir(ast: list[c_ast.VarDefsStmt]) -> list[IR]:
    ctx = CodegenContext()
    irs: list[IR] = []
    irs.extend(codegen_ast2ir_data_emit(ctx,ast))
    irs.extend(codegen_ast2ir_code_emit(ctx, ast))
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
            elif isinstance(ir, ADDW):
                code += f"    addw {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, SUB):
                code += f"    sub {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, SUBW):
                code += f"    subw {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, NEG):
                code += f"    neg {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, NEGW):
                code += f"    negw {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, MUL):
                code += f"    mul {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, MULW):
                code += f"    mulw {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, DIV):
                code += f"    div {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, DIVW):
                code += f"    divw {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, XOR):
                code += f"    xor {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, XORI):
                code += f"    xori {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, SLLI):
                code += f"    slli {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, SRAI):
                code += f"    srli {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}, {ir.value}\n"
            elif isinstance(ir, SEQZ):
                code += f"    seqz {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, SNEZ):
                code += f"    snez {ir.dest.no.name.lower()}, {ir.src.no.name.lower()}\n"
            elif isinstance(ir, SLT):
                code += f"    slt {ir.dest.no.name.lower()}, {ir.src1.no.name.lower()}, {ir.src2.no.name.lower()}\n"
            elif isinstance(ir, SD):
                code += f"    sd {ir.src.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, SW):
                code += f"    sw {ir.src.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, SH):
                code += f"    sh {ir.src.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, SB):
                code += f"    sb {ir.src.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, LD):
                code += f"    ld {ir.dest.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, LW):
                code += f"    lw {ir.dest.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, LH):
                code += f"    lh {ir.dest.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            elif isinstance(ir, LB):
                code += f"    lb {ir.dest.no.name.lower()}, {ir.offset}({ir.base.no.name.lower()})\n"
            else:
                raise Exception('')
    return code

def codegen(ast: list[c_ast.VarDefsStmt]) -> str:
    irs = codegen_ast2ir(ast)
    code = codegen_ir2asm(irs)
    return code
