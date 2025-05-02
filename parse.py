import ctokenize
from typing import * # type: ignore
import ctoken
import cast
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

def parse(tokens: List[ctoken.CToken]) -> cast.Stmt:
    ctx = ParseContext(tokens)
    return parse_stmt(ctx)

def parse_exp(ctx: ParseContext) -> cast.Exp:
    return parse_binexp_asn(ctx)

def parse_binop(ctx: ParseContext) -> cast.BinOp:
    tt = ctx.current().token_type
    ctx.iter()
    if tt == ctoken.CTokenType.OP_ADD:
        return cast.BinOp.ADD
    elif tt == ctoken.CTokenType.OP_SUB:
        return cast.BinOp.SUB
    elif tt == ctoken.CTokenType.OP_MUL:
        return cast.BinOp.MUL
    elif tt == ctoken.CTokenType.OP_DIV:
        return cast.BinOp.DIV
    elif tt == ctoken.CTokenType.OP_EQ:
        return cast.BinOp.EQ
    elif tt == ctoken.CTokenType.OP_NE:
        return cast.BinOp.NE
    elif tt == ctoken.CTokenType.OP_LT:
        return cast.BinOp.LT
    elif tt == ctoken.CTokenType.OP_LE:
        return cast.BinOp.LE
    elif tt == ctoken.CTokenType.OP_GT:
        return cast.BinOp.GT
    elif tt == ctoken.CTokenType.OP_GE:
        return cast.BinOp.GE
    raise Exception()

def parse_num(ctx: ParseContext) -> cast.Exp:
    if ctx.current().token_type == ctoken.CTokenType.NUMBER:
        t = ctx.current()
        ctx.iter()
        return cast.Num(int(t.value))
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        ctx.iter()
        exp = parse_exp(ctx)
        ctx.iter()
        return exp
    elif ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
        i = ctx.current()
        ctx.iter()
        return cast.Idt(i)
    raise Exception(f'meet token: {ctx.current().token_type.name}')

def parse_uexp(ctx: ParseContext) -> cast.Exp:
    if ctx.current().token_type == ctoken.CTokenType.OP_ADD or ctx.current().token_type == ctoken.CTokenType.OP_SUB:
        bop = parse_binop(ctx)
        uop = cast.binop2uop(bop)
        return cast.UExp(uop, parse_uexp(ctx))
    return parse_num(ctx)
# * /
def parse_binexp_mul(ctx: ParseContext) -> cast.Exp:
    l = parse_uexp(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_MUL or ctx.current().token_type == ctoken.CTokenType.OP_DIV):
        op = parse_binop(ctx)
        l = cast.BinExp(l, op, parse_uexp(ctx))
    return l

# + -
def parse_binexp_add(ctx: ParseContext) -> cast.Exp:
    l = parse_binexp_mul(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_ADD or ctx.current().token_type == ctoken.CTokenType.OP_SUB):
        op = parse_binop(ctx)
        l = cast.BinExp(l, op, parse_binexp_mul(ctx))
    return l

def parse_binexp_lt(ctx: ParseContext) -> cast.Exp:
    l = parse_binexp_add(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_LT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_LE or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GT or 
                             ctx.current().token_type == ctoken.CTokenType.OP_GE):
        op = parse_binop(ctx)
        l = cast.BinExp(l, op, parse_binexp_add(ctx))
    return l

def parse_binexp_eq(ctx: ParseContext) -> cast.Exp:
    l = parse_binexp_lt(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_EQ or 
                             ctx.current().token_type == ctoken.CTokenType.OP_NE):
        op = parse_binop(ctx)
        l = cast.BinExp(l, op, parse_binexp_lt(ctx))
    return l

def parse_binexp_asn(ctx: ParseContext) -> cast.Exp:
    l = parse_binexp_eq(ctx)
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        l = cast.BinExp(l, cast.BinOp.ASN, parse_binexp_asn(ctx))
    return l

# 跳过前缀的分号
def ltrim(ctx: ParseContext) -> None:
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()

def parse_stmt(ctx: ParseContext) -> cast.Stmt:
    ltrim(ctx)
    if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
        return parse_stmt_blk(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_INT:
        return parse_stmt_vardefs(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_RETURN:
        return parse_stmt_ret(ctx)
    return parse_stmt_exp(ctx)

def parse_stmt_exp(ctx: ParseContext) -> cast.Stmt:
    stmt_exp = cast.ExpStmt(parse_exp(ctx))
    ltrim(ctx)
    return stmt_exp

def parse_stmt_blk(ctx: ParseContext) -> cast.Stmt:
    stmts: list[cast.Stmt] = []
    ctx.iter()
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
        stmts.append(parse_stmt(ctx))
    ctx.iter()
    ltrim(ctx)
    blkstmt = cast.BlkStmt(stmts)
    # 扫描变量并添加到 整体Var中
    for stmt in blkstmt.stmts:
        if isinstance(stmt, cast.VarDefsStmt):
            for vardef in stmt.var_defs:
                vi = varinfo.VarInfo(vardef.name.value)
                blkstmt.varinfos.append(vi)
    return blkstmt

# 我们应当在parse的时候完成变量编址吗？
def parse_stmt_vardefs(ctx: ParseContext) -> cast.Stmt:
    ctx.iter() # 注意目前我们跳过了类型
    vardefs: list[cast.VarDef] = []
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        vardefs.append(parse_vardef(ctx))
        if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
            ctx.iter()
    ltrim(ctx)
    return cast.VarDefsStmt(vardefs)

def parse_vardef(ctx: ParseContext) -> cast.VarDef:
    name = ctx.current()
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        exp = parse_exp(ctx)
        return cast.VarDef(name, exp)
    return cast.VarDef(name, None)

def parse_stmt_ret(ctx: ParseContext) -> cast.Stmt:
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ltrim(ctx)
        return cast.RetStmt(None)
    value = parse_exp(ctx)
    ltrim(ctx)
    return cast.RetStmt(value)

if __name__ == '__main__':
    tokens = ctokenize.tokenize('')
    ast = parse(tokens)
    print('Hello, world')
