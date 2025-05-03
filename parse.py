import ctokenize
from typing import * # type: ignore
import ctoken
import c_ast
import varinfo

# parse上下文管理器
class ParseContext:
    def __init__(self, tokens: List[ctoken.CToken]):
        super().__init__()
        self.tokens = tokens
    
    def end(self) -> bool:
        return len(self.tokens) == 0
    
    def current(self) -> ctoken.CToken:
        return self.tokens[0]
    
    def iter(self):
        self.tokens = self.tokens[1:]

def parse(tokens: List[ctoken.CToken]) -> c_ast.Stmt:
    ctx = ParseContext(tokens)
    return parse_stmt(ctx)

def parse_exp(ctx: ParseContext) -> c_ast.Exp:
    return parse_binexp_asn(ctx)

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
        return c_ast.Num(int(t.value))
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        ctx.iter()
        exp = parse_exp(ctx)
        ctx.iter()
        return exp
    elif ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
        i = ctx.current()
        ctx.iter()
        return c_ast.Idt(i)
    raise Exception(f'meet token: {ctx.current().token_type.name}')

def parse_uexp(ctx: ParseContext) -> c_ast.Exp:
    if ctx.current().token_type == ctoken.CTokenType.OP_ADD or ctx.current().token_type == ctoken.CTokenType.OP_SUB:
        bop = parse_binop(ctx)
        uop = c_ast.binop2uop(bop)
        return c_ast.UExp(uop, parse_uexp(ctx))
    return parse_num(ctx)
# * /
def parse_binexp_mul(ctx: ParseContext) -> c_ast.Exp:
    l = parse_uexp(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_MUL or ctx.current().token_type == ctoken.CTokenType.OP_DIV):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_uexp(ctx))
    return l

# + -
def parse_binexp_add(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_mul(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_ADD or ctx.current().token_type == ctoken.CTokenType.OP_SUB):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_mul(ctx))
    return l

def parse_binexp_lt(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_add(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_LT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_LE or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GE):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_add(ctx))
    return l

def parse_binexp_eq(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_lt(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_EQ or 
                             ctx.current().token_type == ctoken.CTokenType.OP_NE):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_lt(ctx))
    return l

def parse_binexp_asn(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_eq(ctx)
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        l = c_ast.BinExp(l, c_ast.BinOp.ASN, parse_binexp_asn(ctx))
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
    stmts: list[c_ast.Stmt] = []
    ctx.iter()
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
        stmts.append(parse_stmt(ctx))
    ctx.iter()
    blkstmt = c_ast.BlkStmt(stmts)
    # 扫描变量并添加到 整体Var中
    for stmt in blkstmt.stmts:
        if isinstance(stmt, c_ast.VarDefsStmt):
            for vardef in stmt.var_defs:
                vi = varinfo.VarInfo(vardef.name.value)
                blkstmt.varinfos.append(vi)
    return blkstmt

# 我们应当在parse的时候完成变量编址吗？
def parse_stmt_vardefs(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter() # 注意目前我们跳过了类型
    vardefs: list[c_ast.VarDef] = []
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        vardefs.append(parse_vardef(ctx))
        if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
            ctx.iter()
    ctx.iter()
    return c_ast.VarDefsStmt(vardefs)

def parse_vardef(ctx: ParseContext) -> c_ast.VarDef:
    name = ctx.current()
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        exp = parse_exp(ctx)
        return c_ast.VarDef(name, exp)
    return c_ast.VarDef(name, None)

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

if __name__ == '__main__':
    tokens = ctokenize.tokenize('')
    ast = parse(tokens)
    print('Hello, world')
