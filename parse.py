import ctokenize
from typing import * # type: ignore
import ctoken
import c_ast
import c_type
import varinfo

# parse上下文管理器
class ParseContext:
    def __init__(self, tokens: List[ctoken.CToken]):
        super().__init__()
        self.tokens = tokens
        self.type_tracker: list[dict[str, c_type.CType]] = []
        # enum union 和 typedef使用同一个tracker?
        self.struct_label_tracker: list[dict[str, c_type.CType]] = []
        self.enum_label_tracker: list[dict[str, c_type.CType]] = []
        self.union_label_tracker: list[dict[str, c_type.CType]] = []
        self.typedef_label_tracker: list[dict[str, c_type.CType]] = []
    
    def end(self) -> bool:
        return len(self.tokens) == 0
    
    def current(self) -> ctoken.CToken:
        return self.tokens[0]
    
    def iter(self):
        self.tokens = self.tokens[1:]
    
    def enter_scope(self):
        self.type_tracker.append({})
        self.struct_label_tracker.append({})
        self.enum_label_tracker.append({})
        self.union_label_tracker.append({})
        self.typedef_label_tracker.append({})

    def exit_scope(self):
        self.type_tracker.pop()
        self.struct_label_tracker.pop()
        self.enum_label_tracker.pop()
        self.union_label_tracker.pop()
        self.typedef_label_tracker.pop()
    
    def register_var_type(self, name: str, t: c_type.CType):
        self.type_tracker[-1][name] = t

    def query_var_type(self, name: str) -> c_type.CType:
        for frame in self.type_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'var {name} has no match')
    
    def register_struct_label(self, name: str, t: c_type.CType):
        self.struct_label_tracker[-1][name] = t
    
    def query_struct_type(self, name: str) -> c_type.CType:
        for frame in self.struct_label_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'struct {name} has no match')
    
    def register_union_label(self, name: str, t: c_type.CType):
        self.union_label_tracker[-1][name] = t
    
    def query_union_type(self, name: str) -> c_type.CType:
        for frame in self.union_label_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'union {name} has no match')

def parse(raw_tokens: list[ctoken.CToken]) -> list[c_ast.VarDefsStmt]:
    tokens: list[ctoken.CToken] = []
    for raw_token in raw_tokens:
        if raw_token.token_type == ctoken.CTokenType.COMMENT_SINGLE_LINE or raw_token.token_type == ctoken.CTokenType.COMMENT_MULTI_LINE:
            continue
        tokens.append(raw_token)
    ctx = ParseContext(tokens)
    ctx.enter_scope()
    # 在全局变量作用域中添加assert 和 printf
    ctx.register_var_type('assert', c_type.Func([c_type.I64(), c_type.I64(), c_type.Ptr(c_type.I8())], c_type.Void()))
    ctx.register_var_type('printf', c_type.Func([c_type.Ptr(c_type.I8())], c_type.Void()))
    vardefs_stmts: list[c_ast.VarDefsStmt] = []
    while not ctx.end():
        vardefs = parse_stmt_vardefs(ctx)
        if not isinstance(vardefs, c_ast.VarDefsStmt):
            raise Exception()
        vardefs_stmts.append(vardefs)
        if vardefs.is_funcdef():
            continue
        # 不是函数定义 将类型额外设置为globl
        for vardescribe in vardefs.var_describes:
            ctx.query_var_type(vardescribe.get_name()).glb = True
    ctx.exit_scope()
    return vardefs_stmts

def parse_exp(ctx: ParseContext) -> c_ast.Exp:
    e = parse_binexp_comma(ctx)
    add_type(ctx, e)
    return e

def parse_exp_disable_comma(ctx: ParseContext) -> c_ast.Exp:
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
    e: c_ast.Exp|None = None
    if ctx.current().token_type == ctoken.CTokenType.NUMBER:
        t = ctx.current()
        ctx.iter()
        e = c_ast.Num(int(t.value))
        add_type(ctx, e)
    elif ctx.current().token_type == ctoken.CTokenType.STRING:
        t = ctx.current()
        ctx.iter()
        e = c_ast.Str(t.value[1:len(t.value)-1])
        add_type(ctx, e)
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        ctx.iter()
        if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
            # 语句表达式
            stmt = parse_stmt(ctx)
            e = c_ast.BlkExp(stmt)
            add_type(ctx, e)
        else:
            e = parse_exp(ctx)
        ctx.iter()
    elif ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
        i = ctx.current()
        ctx.iter()
        e = c_ast.Idt(i)
        add_type(ctx, e)
    else:
        raise Exception(f'{ctx.current().token_type} {e}')
    # 对函数调用的情况做处理
    while ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET or \
        ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET or \
        ctx.current().token_type == ctoken.CTokenType.PC_POINT or \
        ctx.current().token_type == ctoken.CTokenType.OP_R_ARROW:
        # 数组下标
        if ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET:
            ctx.iter()
            idx = parse_exp(ctx)
            ctx.iter()
            # e[idx]中，必须满足 'e是指针/数组，idx是整形' 或 'e是整形，idx是指针'
            if (not isinstance(e.type, c_type.Ary) and not isinstance(e.type, c_type.Ptr)) and \
                (not isinstance(idx.type, c_type.Ary) and not isinstance(idx.type, c_type.Ptr)):
                raise Exception(f'index error: {e.type}, {e}, {idx.type}, {idx}')
            # 分别处理 整型[指针/数组] 和 指针/数组[整型] 的情况
            # 处理 整型[指针/数组] 的情况
            if isinstance(idx.type, c_type.Ary) or isinstance(idx.type, c_type.Ptr):
                # 构造常量
                const_num = c_ast.Num(idx.type.base.length())
                add_type(ctx, const_num)
                # 常量乘以偏移量
                offset = c_ast.BinExp(e, c_ast.BinOp.MUL, const_num)
                add_type(ctx, offset)
                e = c_ast.BinExp(offset, c_ast.BinOp.ADD, idx)
                add_type(ctx, e)
                e = c_ast.UExp(c_ast.UOp.DEREF, e)
                add_type(ctx, e)
                continue
            # 处理 指针/数组[整型] 的情况
            if not isinstance(e.type, c_type.Ary) and not isinstance(e.type, c_type.Ptr):
                raise Exception('')
            const_num = c_ast.Num(e.type.base.length())
            add_type(ctx, const_num)
            # 常量乘以偏移量
            offset = c_ast.BinExp(idx, c_ast.BinOp.MUL, const_num)
            add_type(ctx, offset)
            e = c_ast.BinExp(e, c_ast.BinOp.ADD, offset)
            add_type(ctx, e)
            e = c_ast.UExp(c_ast.UOp.DEREF, e)
            add_type(ctx, e)
            continue
        # 处理 . 访问操作符
        if ctx.current().token_type == ctoken.CTokenType.PC_POINT:
            # 这个逻辑是如何实现的呢？
            ctx.iter()
            want = ctx.current()
            ctx.iter()
            e = c_ast.BinExp(e, c_ast.BinOp.ACS, c_ast.Idt(want))
            add_type(ctx, e)
            continue
        # 处理-> 访问操作符
        if ctx.current().token_type == ctoken.CTokenType.OP_R_ARROW:
            ctx.iter()
            want = ctx.current()
            ctx.iter()
            # 构造解引用表达式
            deref = c_ast.UExp(c_ast.UOp.DEREF, e)
            add_type(ctx, deref)
            # 构造访问表达式
            e = c_ast.BinExp(deref, c_ast.BinOp.ACS, c_ast.Idt(want))
            add_type(ctx, e)
            continue
        # 处理函数调用
        ctx.iter()
        inargs: list[c_ast.Exp] = []
        while ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
            inargs.append(parse_exp_disable_comma(ctx))
            if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                ctx.iter()
        ctx.iter()
        e = c_ast.Call(e, inargs)
        add_type(ctx, e)
    return e

def parse_uexp(ctx: ParseContext) -> c_ast.Exp:
    # 另外需要考虑sizeof的情况
    if (ctx.current().token_type == ctoken.CTokenType.OP_ADD or 
        ctx.current().token_type == ctoken.CTokenType.OP_SUB or 
        ctx.current().token_type == ctoken.CTokenType.OP_BITS_AND or 
        ctx.current().token_type == ctoken.CTokenType.OP_MUL):
        bop = parse_binop(ctx)
        uop = c_ast.binop2uop(bop)
        e = c_ast.UExp(uop, parse_uexp(ctx))
        add_type(ctx, e)
        return e
    if ctx.current().token_type == ctoken.CTokenType.KEY_SIZEOF:
        ctx.iter()
        # 括号开头
        if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
            ctx.iter()
            e = parse_exp(ctx)
            ctx.iter()
            e = c_ast.UExp(c_ast.UOp.SIZEOF, e)
            add_type(ctx, e)
            return e
        # 表达式开头（不是括号开头）
        e = parse_uexp(ctx)
        e = c_ast.UExp(c_ast.UOp.SIZEOF, e)
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
        # l 指针 r 非指针
        if isinstance(l.l.type, c_type.Ptr) and not isinstance(l.r.type, c_type.Ptr):
            const_len = c_ast.Num(l.l.type.base.length())
            add_type(ctx, const_len)
            neo_r = c_ast.BinExp(l.r, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_r)
            l.r = neo_r
        # l 非指针 r 指针
        elif not isinstance(l.l.type, c_type.Ptr) and isinstance(l.r.type, c_type.Ptr):
            const_len = c_ast.Num(l.r.type.length())
            add_type(ctx, const_len)
            neo_l = c_ast.BinExp(l.l, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_l)
            l.l = neo_l
        # l 指针 r指针
        elif isinstance(l.l.type, c_type.Ptr) and isinstance(l.r.type, c_type.Ptr):
            if not l.op == c_ast.BinOp.SUB:
                raise Exception(f'pointer calc error: {l.op}')
            add_type(ctx, l)
            const_len = c_ast.Num(l.l.type.base.length())
            add_type(ctx, const_len)
            l = c_ast.BinExp(l, c_ast.BinOp.DIV, const_len)
        elif isinstance(l.l.type, c_type.Ary) and not isinstance(l.r.type, c_type.Ary):
            const_len = c_ast.Num(l.l.type.base.length())
            add_type(ctx, const_len)
            neo_r = c_ast.BinExp(l.r, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_r)
            l.r = neo_r
        elif not isinstance(l.l.type, c_type.Ary) and isinstance(l.r.type, c_type.Ary):
            const_len = c_ast.Num(l.r.type.length())
            add_type(ctx, const_len)
            neo_l = c_ast.BinExp(l.l, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_l)
            l.l = neo_l
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

def parse_binexp_comma(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_asn(ctx)
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
        ctx.iter()
        l = c_ast.BinExp(l, c_ast.BinOp.COMMA, parse_binexp_asn(ctx))
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
    elif ctx.current().token_type == ctoken.CTokenType.KEY_INT or \
        ctx.current().token_type == ctoken.CTokenType.KEY_CHAR or \
        ctx.current().token_type == ctoken.CTokenType.KEY_STRUCT or \
        ctx.current().token_type == ctoken.CTokenType.KEY_UNION or \
        ctx.current().token_type == ctoken.CTokenType.KEY_ENUM:
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
                vi.t = vardef.get_type()
                blkstmt.varinfos.append(vi)
    ctx.exit_scope()
    return blkstmt

# 现在要处理的问题是：分别parse为vardefs function 和 声明
# 注册变量类型的过程发生在哪里？我觉得应该发生在blk内部
def parse_stmt_vardefs(ctx: ParseContext, disable_frame_injection: bool = False) -> c_ast.Stmt:
    t = parse_type(ctx)
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        return c_ast.VarDefsStmt(t, [])
    vardescribes: list[c_ast.VarDescribe] = [parse_vardescribe(ctx, t)]
    # 如果我们解析了一个函数定义，那就应当注册函数名到type_tracker中 然后直接返回
    if vardescribes[0].is_funcdef():
        # 把函数名注册为函数变量
        ctx.register_var_type(vardescribes[0].get_name(), vardescribes[0].get_type())
        return c_ast.VarDefsStmt(t, vardescribes)
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        vardescribes.append(parse_vardescribe(ctx, t))
    ctx.iter()
    if not disable_frame_injection:
        for vardescribe in vardescribes:
            ctx.register_var_type(vardescribe.get_name(), vardescribe.get_type())
    return c_ast.VarDefsStmt(t, vardescribes)

# 这里的处理会很复杂
def parse_type(ctx: ParseContext) -> c_type.CType:
    if ctx.current().token_type == ctoken.CTokenType.KEY_INT:
        ctx.iter()
        return c_type.I64()
    if ctx.current().token_type == ctoken.CTokenType.KEY_CHAR:
        ctx.iter()
        return c_type.I8()
    if ctx.current().token_type == ctoken.CTokenType.KEY_STRUCT:
        ctx.iter()
        label: None|str = None
        if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
            label = ctx.current().value
            ctx.iter()
        items: list[tuple[str, c_type.CType]] = []
        # 说明我们是要使用已有的struct 而不是构造新的struct
        if ctx.current().token_type != ctoken.CTokenType.PC_L_CURLY_BRACKET:
            if label is None:
                raise Exception('')
            return ctx.query_struct_type(label)
        ctx.iter()
        # 这里的逻辑有问题 我们不知道是要构造新的struct还是使用老的struct
        while ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
            vardefsstmt = parse_stmt_vardefs(ctx, disable_frame_injection=True)
            if not isinstance(vardefsstmt, c_ast.VarDefsStmt):
                raise Exception('')
            for vardescribe in vardefsstmt.var_describes:
                items.append((vardescribe.get_name(), vardescribe.get_type()))
        ctx.iter()
        # 构造结构体类型
        cunion_t = c_type.CStruct(label, items)
        # 存在一个可感知的名称 将label注册到struct的tracker中
        if label is not None:
            ctx.register_struct_label(label, cunion_t)
        return cunion_t
    if ctx.current().token_type == ctoken.CTokenType.KEY_UNION:
        ctx.iter()
        label: None|str = None
        if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
            label = ctx.current().value
            ctx.iter()
        items: list[tuple[str, c_type.CType]] = []
        # 说明我们是要使用已有的struct 而不是构造新的struct
        if ctx.current().token_type != ctoken.CTokenType.PC_L_CURLY_BRACKET:
            if label is None:
                raise Exception('')
            return ctx.query_union_type(label)
        ctx.iter()
        # 这里的逻辑有问题 我们不知道是要构造新的struct还是使用老的struct
        while ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
            vardefsstmt = parse_stmt_vardefs(ctx, disable_frame_injection=True)
            if not isinstance(vardefsstmt, c_ast.VarDefsStmt):
                raise Exception('')
            for vardescribe in vardefsstmt.var_describes:
                items.append((vardescribe.get_name(), vardescribe.get_type()))
        ctx.iter()
        # 构造结构体类型
        cunion_t = c_type.CUnion(label, items)
        # 存在一个可感知的名称 将label注册到struct的tracker中
        if label is not None:
            ctx.register_union_label(label, cunion_t)
        return cunion_t
    if ctx.current().token_type == ctoken.CTokenType.KEY_ENUM:
        pass
    raise Exception(f'{ctx.current().token_type} {ctx.current().token_type}')

def parse_vardescribe(ctx: ParseContext, t: c_type.CType) -> c_ast.VarDescribe:
    # 应当把初始化值的初始化提前到那个什么地方中
    vardescribe = parse_vardescribe_prefix(ctx, t)
    if not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        vardescribe.init = parse_exp_disable_comma(ctx)
    return vardescribe

def parse_vardescribe_prefix(ctx: ParseContext, t: c_type.CType) -> c_ast.VarDescribe:
    if ctx.current().token_type == ctoken.CTokenType.OP_MUL:
        ctx.iter()
        cur_vardescribe = parse_vardescribe_prefix(ctx, t)
        cur_vardescribe.t = c_type.Ptr(cur_vardescribe.get_type())
        return cur_vardescribe
    return parse_vardescribe_suffix(ctx, t)

# 后缀
# suffix应当在处理完所有的代码后进行suffix处理
def parse_vardescribe_suffix(ctx: ParseContext, t: c_type.CType) -> c_ast.VarDescribe:
    # 对常规的vardescribe进行parse
    name = ctx.current()
    ctx.iter()
    normal: c_ast.VarDescribe = c_ast.NormalVarDescribe(name, None)
    normal.t = t
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        return parse_vardescribe_suffix_func(ctx, normal)
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET:
        return parse_vardescribe_suffix_ary(ctx, normal)
    return normal

def parse_vardescribe_suffix_ary(ctx: ParseContext, original_vardescribe: c_ast.VarDescribe) -> c_ast.VarDescribe:
    # 对常规的vardescribe进行parse
    ctx.iter()
    idx = int(ctx.current().value)
    ctx.iter()
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        sub_vardescribe = parse_vardescribe_suffix_func(ctx, original_vardescribe)
        sub_t = sub_vardescribe.get_type()
        cur_t = c_type.Ary(sub_t, idx)
        cur_vardescribe = c_ast.AryVarDescribe(original_vardescribe, idx)
        cur_vardescribe.t = cur_t
        return cur_vardescribe
    elif ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET:
        sub_vardescribe = parse_vardescribe_suffix_ary(ctx, original_vardescribe)
        sub_t = sub_vardescribe.get_type()
        cur_t = c_type.Ary(sub_t, idx)
        cur_vardescribe = c_ast.AryVarDescribe(original_vardescribe, idx)
        cur_vardescribe.t = cur_t
        return cur_vardescribe
    # 到这里说明这是数组修饰符的终点了，在original_vardescribe的基础上构建数组类型
    cur_vardescribe = c_ast.AryVarDescribe(original_vardescribe, idx)
    cur_vardescribe.t = c_type.Ary(original_vardescribe.get_type(), idx)
    return cur_vardescribe


def parse_vardescribe_suffix_func(ctx: ParseContext,  original_vardescribe: c_ast.VarDescribe) -> c_ast.VarDescribe:
    ctx.iter()
    params: list[c_ast.VarDefsStmt] = []
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
        params.append(parse_param(ctx))
        if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
            ctx.iter()
    ctx.iter()
    # 对params的所有item进行处理
    params_types: list[c_type.CType] = []
    for param in params:
        params_type = param.var_describes[0].get_type()
        params_types.append(params_type)
    body: c_ast.Stmt|None = None
    if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
        # 正在解析函数定义，在正式解析前需要把所有的变量都注册到query中
        ctx.register_var_type(original_vardescribe.get_name(), c_type.Func(params_types, original_vardescribe.get_type()))
        # 问题：为什么解析不到类型？
        ctx.enter_scope()
        # 将函数定义的所有入参都注册到query中
        for param in params:
            ctx.register_var_type(param.var_describes[0].get_name(), param.var_describes[0].get_type())
        body = parse_stmt_blk(ctx)
        ctx.exit_scope()
        neo_original_vardescribe = c_ast.FuncVarDescribe(original_vardescribe, params, body)
        neo_original_vardescribe.t = c_type.Func(params_types, original_vardescribe.get_type())
        # 因为解析完函数体后已经没有必要继续 试图解析剩余的修饰了，这里直接return
        return neo_original_vardescribe
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        sub_vardescribe = parse_vardescribe_suffix_func(ctx, original_vardescribe)
        sub_t = sub_vardescribe.get_type()
        cur_t = c_type.Func(params_types, sub_t)
        cur_vardescribe = c_ast.FuncVarDescribe(original_vardescribe, params, None)
        cur_vardescribe.t = cur_t
        return cur_vardescribe
    if ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET:
        sub_vardescribe = parse_vardescribe_suffix_ary(ctx, original_vardescribe)
        sub_t = sub_vardescribe.get_type()
        cur_t = c_type.Func(params_types, sub_t)
        cur_vardescribe = c_ast.FuncVarDescribe(original_vardescribe, params, None)
        cur_vardescribe.t = cur_t
        return cur_vardescribe
    # 说明已经是函数声明的结尾了，应当使用original_describe构造函数声明
    neo_original_vardescribe = c_ast.FuncVarDescribe(original_vardescribe, params, None)
    neo_original_vardescribe.t = c_type.Func(params_types, original_vardescribe.get_type())
    return neo_original_vardescribe

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
        exp.type = c_type.I64()
    elif isinstance(exp, c_ast.Str):
        exp.type = c_type.Ary(c_type.I8(), len(exp.value) + 1)
    elif isinstance(exp, c_ast.BlkExp):
        if not isinstance(exp.stmt, c_ast.BlkStmt):
            raise Exception('')
        if len(exp.stmt.stmts) == 0:
            exp.type = c_type.Void()
            return
        # 如果最后一个stmt是exp_stmt 就获得该exp的类型
        if isinstance(exp.stmt.stmts[-1], c_ast.ExpStmt):
            exp.type = exp.stmt.stmts[-1].exp.type
        # 如果最后一个stmt不是exp_stmt 就赋值为void
        else:
            exp.type = c_type.Void()
    elif isinstance(exp, c_ast.Idt):
        exp.type = ctx.query_var_type(exp.idt.value)
    elif isinstance(exp, c_ast.Call):
        func_type = exp.func_source.type
        if not isinstance(func_type, c_type.Func):
            raise Exception(f'{exp} {exp.func_source}')
        exp.type = func_type.ret
    elif isinstance(exp, c_ast.BinExp):
        if exp.op == c_ast.BinOp.ADD:
            if isinstance(exp.l.type, c_type.Ptr) and not isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.l.type
            elif not isinstance(exp.l.type, c_type.Ptr) and isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.r.type
            elif isinstance(exp.l.type, c_type.Ary) and not isinstance(exp.r.type, c_type.Ary):
                exp.type = c_type.Ptr(exp.l.type.base)
            elif not isinstance(exp.l.type, c_type.Ary) and isinstance(exp.r.type, c_type.Ary):
                exp.type = c_type.Ptr(exp.r.type.base)
            else:
                exp.type = c_type.I64()
        elif exp.op == c_ast.BinOp.SUB:
            if isinstance(exp.l.type, c_type.Ptr) and not isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.l.type
            elif isinstance(exp.l.type, c_type.Ptr) and isinstance(exp.r.type, c_type.Ptr):
                exp.type = c_type.I64()
            else:
                exp.type = c_type.I64()
        elif exp.op == c_ast.BinOp.MUL:
            exp.type = c_type.I64()
        elif exp.op == c_ast.BinOp.DIV:
            exp.type = c_type.I64()
        elif (exp.op == c_ast.BinOp.EQ or exp.op == c_ast.BinOp.NE or exp.op == c_ast.BinOp.LT or 
              exp.op == c_ast.BinOp.LE or exp.op == c_ast.BinOp.GT or exp.op == c_ast.BinOp.GE):
            exp.type = c_type.I64()
        elif exp.op == c_ast.BinOp.ASN:
            exp.type = exp.l.type
        elif exp.op == c_ast.BinOp.COMMA:
            exp.type = exp.r.type
        elif exp.op == c_ast.BinOp.ACS:
            if not isinstance(exp.r, c_ast.Idt):
                raise Exception(f'{exp} {exp.r}')
            if isinstance(exp.l.type, c_type.CStruct):
                exp.type = exp.l.type.subtype(exp.r.idt.value)
            elif isinstance(exp.l.type, c_type.CUnion):
                exp.type = exp.l.type.subtype(exp.r.idt.value)
            else:
                raise Exception('')
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
            exp.type = c_type.Ptr(exp.exp.type)
        elif exp.op == c_ast.UOp.DEREF:
            if not isinstance(exp.exp.type, c_type.Ptr) and not isinstance(exp.exp.type, c_type.Ary):
                raise Exception(f'{exp.exp} {exp.exp.type}')
            exp.type = exp.exp.type.base
        elif exp.op == c_ast.UOp.SIZEOF:
            exp.type = c_type.I64()
        else:
            raise Exception('')

if __name__ == '__main__':
    tokens = ctokenize.tokenize('int main() {return 1;}')
    ast = parse(tokens)
    print('Hello, world')

# 我在思考的是 是不是应当修改获取变量地址的路径 而不是从parse_context中获取？