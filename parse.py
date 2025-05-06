import ctokenize
from typing import * # type: ignore
import ctoken
import c_ast
import ctype
import varinfo

# parse上下文管理器
class ParseContext:
    def __init__(self, tokens: List[ctoken.CToken]):
        super().__init__()
        self.tokens = tokens
        self.type_tracker: list[dict[str, ctype.CType]] = []
    
    def end(self) -> bool:
        return len(self.tokens) == 0
    
    def current(self) -> ctoken.CToken:
        return self.tokens[0]
    
    def iter(self):
        self.tokens = self.tokens[1:]
    
    def enter_scope(self):
        self.type_tracker.append({})

    def exit_scope(self):
        self.type_tracker.pop()
    
    def register_var_type(self, name: str, t: ctype.CType):
        self.type_tracker[-1][name] = t

    def query_var_type(self, name: str) -> ctype.CType:
        for frame in self.type_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'var {name} has no match')

def parse(tokens: List[ctoken.CToken]) -> list[c_ast.VarDefsStmt]:
    ctx = ParseContext(tokens)
    ctx.enter_scope()
    vardefs_stmts: list[c_ast.VarDefsStmt] = []
    while not ctx.end():
        vardefs = parse_stmt_vardefs(ctx)
        if not isinstance(vardefs, c_ast.VarDefsStmt):
            raise Exception()
        vardefs_stmts.append(vardefs)
    ctx.exit_scope()
    return vardefs_stmts

def parse_exp(ctx: ParseContext) -> c_ast.Exp:
    e = parse_binexp_asn(ctx)
    add_type(ctx, e)
    return e

def parse_binop(ctx: ParseContext) -> c_ast.BinOp:
    tt = ctx.current().token_type
    ctx.iter()
    if tt == ctoken.CTokenType.OP_ADD:
        return c_ast.BinOp.ADD
    elif tt == ctoken.CTokenType.OP_SUB:
        return c_ast.BinOp.SUB
    elif tt == ctoken.CTokenType.OP_MUL:
        return c_ast.BinOp.MUL
    elif tt == ctoken.CTokenType.OP_DIV:
        return c_ast.BinOp.DIV
    elif tt == ctoken.CTokenType.OP_BITS_AND:
        return c_ast.BinOp.BITS_AND
    elif tt == ctoken.CTokenType.OP_EQ:
        return c_ast.BinOp.EQ
    elif tt == ctoken.CTokenType.OP_NE:
        return c_ast.BinOp.NE
    elif tt == ctoken.CTokenType.OP_LT:
        return c_ast.BinOp.LT
    elif tt == ctoken.CTokenType.OP_LE:
        return c_ast.BinOp.LE
    elif tt == ctoken.CTokenType.OP_GT:
        return c_ast.BinOp.GT
    elif tt == ctoken.CTokenType.OP_GE:
        return c_ast.BinOp.GE
    raise Exception()

def parse_num(ctx: ParseContext) -> c_ast.Exp:
    if ctx.current().token_type == ctoken.CTokenType.NUMBER:
        t = ctx.current()
        ctx.iter()
        e = c_ast.Num(int(t.value))
        add_type(ctx, e)
        return e
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        ctx.iter()
        exp = parse_exp(ctx)
        ctx.iter()
        return exp
    elif ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
        i = ctx.current()
        ctx.iter()
        e = c_ast.Idt(i)
        add_type(ctx, e)
        # 对函数调用的情况做处理
        if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
            ctx.iter()
            inargs: list[c_ast.Exp] = []
            while ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
                inargs.append(parse_exp(ctx))
                if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                    ctx.iter()
            ctx.iter()
            e = c_ast.Call(e, inargs)
            add_type(ctx, e)
        return e
    raise Exception(f'meet token: {ctx.current().token_type.name}')

def parse_uexp(ctx: ParseContext) -> c_ast.Exp:
    if (ctx.current().token_type == ctoken.CTokenType.OP_ADD or 
        ctx.current().token_type == ctoken.CTokenType.OP_SUB or 
        ctx.current().token_type == ctoken.CTokenType.OP_BITS_AND or 
        ctx.current().token_type == ctoken.CTokenType.OP_MUL):
        bop = parse_binop(ctx)
        uop = c_ast.binop2uop(bop)
        e = c_ast.UExp(uop, parse_uexp(ctx))
        add_type(ctx, e)
        return e
    return parse_num(ctx)
# * /
def parse_binexp_mul(ctx: ParseContext) -> c_ast.Exp:
    l = parse_uexp(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_MUL or 
                             ctx.current().token_type == ctoken.CTokenType.OP_DIV):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_uexp(ctx))
        add_type(ctx, l)
    return l

# + -
def parse_binexp_add(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_mul(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_ADD or 
                             ctx.current().token_type == ctoken.CTokenType.OP_SUB):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_mul(ctx))
        # 在这里进行指针运算的修正
        # （暂时还没有做）
        if isinstance(l.l.type, ctype.Ptr) and not isinstance(l.r.type, ctype.Ptr):
            literal_8 = c_ast.Num(8)
            add_type(ctx, literal_8)
            neo_r = c_ast.BinExp(l.r, c_ast.BinOp.MUL, literal_8)
            add_type(ctx, neo_r)
            l.r = neo_r
        elif not isinstance(l.l.type, ctype.Ptr) and isinstance(l.r.type, ctype.Ptr):
            literal_8 = c_ast.Num(8)
            add_type(ctx, literal_8)
            neo_l = c_ast.BinExp(l.l, c_ast.BinOp.MUL, literal_8)
            add_type(ctx, neo_l)
            l.l = neo_l
        elif isinstance(l.l.type, ctype.Ptr) and isinstance(l.r.type, ctype.Ptr):
            if not l.op == c_ast.BinOp.SUB:
                raise Exception(f'pointer calc error: {l.op}')
            literal_8 = c_ast.Num(8)
            add_type(ctx, literal_8)
            l = c_ast.BinExp(l, c_ast.BinOp.DIV, literal_8)
        add_type(ctx, l)
    return l

# # 修正指针运算，构造为新的表达式
# def pointer_calc_recorrect(l: c_ast.Exp, r: c_ast.Exp) -> c_ast.Exp:
#     pass

def parse_binexp_lt(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_add(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_LT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_LE or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GE):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_add(ctx))
        add_type(ctx, l)
    return l

def parse_binexp_eq(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_lt(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_EQ or 
                             ctx.current().token_type == ctoken.CTokenType.OP_NE):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_lt(ctx))
        add_type(ctx, l)
    return l

def parse_binexp_asn(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_eq(ctx)
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        l = c_ast.BinExp(l, c_ast.BinOp.ASN, parse_binexp_asn(ctx))
        add_type(ctx, l)
    return l

# 跳过前缀的分号
def ltrim(ctx: ParseContext):
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()

def parse_stmt(ctx: ParseContext) -> c_ast.Stmt:
    ltrim(ctx)
    result: None|c_ast.Stmt = None
    if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
        result = parse_stmt_blk(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_INT:
        result = parse_stmt_vardefs(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_RETURN:
        result = parse_stmt_ret(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_IF:
        result = parse_stmt_if(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_FOR:
        result = parse_stmt_for(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_WHILE:
        result = parse_stmt_while(ctx)
    else:
        result = parse_stmt_exp(ctx)
    ltrim(ctx)
    return result

def parse_stmt_exp(ctx: ParseContext) -> c_ast.Stmt:
    stmt_exp = c_ast.ExpStmt(parse_exp(ctx))
    ltrim(ctx)
    return stmt_exp

def parse_stmt_blk(ctx: ParseContext) -> c_ast.Stmt:
    ctx.enter_scope()
    stmts: list[c_ast.Stmt] = []
    ctx.iter()
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
        stmts.append(parse_stmt(ctx))
    ctx.iter()
    blkstmt = c_ast.BlkStmt(stmts)
    # 扫描变量并添加到 整体Var中
    for stmt in blkstmt.stmts:
        if isinstance(stmt, c_ast.VarDefsStmt):
            for vardef in stmt.var_describes:
                vi = varinfo.VarInfo(vardef.get_name())
                blkstmt.varinfos.append(vi)
    ctx.exit_scope()
    return blkstmt

# 现在要处理的问题是：分别parse为vardefs function 和 声明
# 注册变量类型的过程发生在哪里？我觉得应该发生在blk内部
def parse_stmt_vardefs(ctx: ParseContext) -> c_ast.Stmt:
    t = parse_type(ctx)
    vardescribes: list[c_ast.VarDescribe] = [parse_vardescribe(ctx, t)]
    # 如果我们解析了一个函数定义，那就应当直接返回
    if vardescribes[0].is_funcdef():
        # 把函数名注册为函数变量
        ctx.register_var_type(vardescribes[0].get_name(), vardescribes[0].get_type())
        return c_ast.VarDefsStmt(t, vardescribes)
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        vardescribes.append(parse_vardescribe(ctx, t))
    ctx.iter()
    for vardescribe in vardescribes:
        ctx.register_var_type(vardescribe.get_name(), vardescribe.get_type())
    return c_ast.VarDefsStmt(t, vardescribes)

def parse_type(ctx: ParseContext) -> ctype.CType:
    if ctx.current().token_type == ctoken.CTokenType.KEY_INT:
        ctx.iter()
        return ctype.I64()
    raise Exception('')

def parse_vardescribe(ctx: ParseContext, t: ctype.CType) -> c_ast.VarDescribe:
    return parse_vardescribe_prefix(ctx, t)

def parse_vardescribe_prefix(ctx: ParseContext, t: ctype.CType) -> c_ast.VarDescribe:
    if ctx.current().token_type == ctoken.CTokenType.OP_MUL:
        t = ctype.Ptr(t)
        ctx.iter()
        return parse_vardescribe_prefix(ctx, t)
    return parse_vardescribe_suffix(ctx, t)

# 后缀
def parse_vardescribe_suffix(ctx: ParseContext, t: ctype.CType) -> c_ast.VarDescribe:
    # 对常规的vardescribe进行parse
    name = ctx.current()
    ctx.iter()
    normal: c_ast.VarDescribe = c_ast.NormalVarDescribe(name, None)
    normal.t = t
    if ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        normal.init = parse_exp(ctx)
        return normal
    elif ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        return normal
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        # 对函数进行parse
        ctx.iter()
        params: list[c_ast.VarDefsStmt] = []
        while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
            params.append(parse_param(ctx))
            if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                ctx.iter()
        ctx.iter()
        # 对param的所有item进行处理
        params_types: list[ctype.CType] = []
        for param in params:
            params_type = param.var_describes[0].get_type()
            params_types.append(params_type)
        body: c_ast.Stmt|None = None
        if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
            # 正在解析函数体，在正式解析前需要把所有的变量都注册到query中
            ctx.enter_scope()
            for param in params:
                ctx.register_var_type(param.var_describes[0].get_name(), param.var_describes[0].get_type())
            body = parse_stmt_blk(ctx)
            ctx.exit_scope()
            neo_normal = c_ast.FuncVarDescribe(normal, params, body)
            neo_normal.t = ctype.Func(params_types, normal.get_type())
            normal = neo_normal
        else:
            neo_normal = c_ast.FuncVarDescribe(normal, params, None)
            neo_normal.t = ctype.Func(params_types, normal.get_type())
            normal = neo_normal
    return normal

def parse_param(ctx: ParseContext) -> c_ast.VarDefsStmt:
    t = parse_type(ctx)
    vardescribes: list[c_ast.VarDescribe] = [parse_vardescribe(ctx, t)]
    return c_ast.VarDefsStmt(t, vardescribes)

def parse_stmt_ret(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        return c_ast.RetStmt(None)
    value = parse_exp(ctx)
    ctx.iter()
    return c_ast.RetStmt(value)

def parse_stmt_if(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    cond = parse_exp(ctx)
    t = parse_stmt(ctx)
    if ctx.current().token_type == ctoken.CTokenType.KEY_ELSE:
        ctx.iter()
        f = parse_stmt(ctx)
        return c_ast.IfStmt(cond, t, f)
    return c_ast.IfStmt(cond, t, None)

def parse_stmt_for(ctx: ParseContext) -> c_ast.Stmt:
    # 问题： ltrim会消耗多个token 应当把其他情况下的合理内容变成不合理内容？
    # 可以选择修改for的init结构，比如变成VarDefsStmt|Exp|None
    ctx.iter()
    ctx.iter()
    init: None|c_ast.VarDefsStmt|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        if ctx.current().token_type == ctoken.CTokenType.KEY_INT:
            tmp = parse_stmt_vardefs(ctx)
            if not isinstance(tmp, c_ast.VarDefsStmt):
                raise Exception('')
            init = tmp
        else:
            init = parse_exp(ctx)
            ctx.iter()
    else:
        ctx.iter()
    cond: None|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        cond = parse_exp(ctx)
    ctx.iter()
    step: None|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
        step = parse_exp(ctx)
    ctx.iter()
    body = parse_stmt(ctx)
    return c_ast.ForStmt(init, cond, step, body)

def parse_stmt_while(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    cond = parse_exp(ctx)
    body = parse_stmt(ctx)
    return c_ast.WhileStmt(cond, body)

# 下面的代码我完全没有审阅 重新观察 等待修改
def add_type(ctx: ParseContext, exp: c_ast.Exp):
    if isinstance(exp, c_ast.Num):
        exp.type = ctype.I64()
    elif isinstance(exp, c_ast.Idt):
        exp.type = ctx.query_var_type(exp.idt.value)
    elif isinstance(exp, c_ast.Call):
        func_type = exp.func_source.type
        if not isinstance(func_type, ctype.Func):
            raise Exception('')
        exp.type = func_type.ret
    elif isinstance(exp, c_ast.BinExp):
        if exp.op == c_ast.BinOp.ADD:
            if isinstance(exp.l.type, ctype.Ptr) and not isinstance(exp.r.type, ctype.Ptr):
                exp.type = exp.l.type
            elif not isinstance(exp.l.type, ctype.Ptr) and isinstance(exp.r.type, ctype.Ptr):
                exp.type = exp.r.type
            else:
                exp.type = ctype.I64()
        elif exp.op == c_ast.BinOp.SUB:
            if isinstance(exp.l.type, ctype.Ptr) and not isinstance(exp.r.type, ctype.Ptr):
                exp.type = exp.l.type
            elif isinstance(exp.l.type, ctype.Ptr) and isinstance(exp.r.type, ctype.Ptr):
                exp.type = ctype.I64()
            else:
                exp.type = ctype.I64()
        elif exp.op == c_ast.BinOp.MUL:
            exp.type = ctype.I64()
        elif exp.op == c_ast.BinOp.DIV:
            exp.type = ctype.I64()
        elif (exp.op == c_ast.BinOp.EQ or exp.op == c_ast.BinOp.NE or exp.op == c_ast.BinOp.LT or 
              exp.op == c_ast.BinOp.LE or exp.op == c_ast.BinOp.GT or exp.op == c_ast.BinOp.GE):
            exp.type = ctype.I64()
        elif exp.op == c_ast.BinOp.ASN:
            exp.type = exp.l.type
        else:
            raise Exception(f'unknown operator: {exp.op}')
    elif isinstance(exp, c_ast.UExp):
        if not exp.exp.type:
            raise Exception('')
        if exp.op == c_ast.UOp.ADD:
            exp.type = exp.exp.type
        elif exp.op == c_ast.UOp.SUB:
            exp.type = exp.exp.type
        elif exp.op == c_ast.UOp.REF:
            exp.type = ctype.Ptr(exp.exp.type)
        elif exp.op == c_ast.UOp.DEREF:
            if not isinstance(exp.exp.type, ctype.Ptr):
                raise Exception('')
            exp.type = exp.exp.type.base
        else:
            raise Exception('')

if __name__ == '__main__':
    tokens = ctokenize.tokenize('int main() {return 1;}')
    ast = parse(tokens)
    print('Hello, world')
