import ctokenize
from typing import * # type: ignore
import ctoken
import c_ast
import c_type
import utils
import varinfo

# parse上下文管理器
class ParseContext:
    def __init__(self, tokens: List[ctoken.CToken]):
        super().__init__()
        self.tokens = tokens
        self.type_tracker: list[dict[str, c_type.CType]] = []
        self.ret_type: c_type.CType|None = None
        # enum union 和 typedef使用同一个tracker
        self.struct_label_tracker: list[dict[str, c_type.CType]] = []
        self.union_label_tracker: list[dict[str, c_type.CType]] = []
        self.typedef_label_tracker: list[dict[str, c_type.CType]] = []
        # enum 
        self.enum_tracker: list[dict[str, tuple[str, int]]] = []
    
    def end(self) -> bool:
        return len(self.tokens) == 0
    
    def current(self) -> ctoken.CToken:
        return self.tokens[0]
    
    def next(self) -> ctoken.CToken:
        return self.tokens[1]
    
    def iter(self):
        self.tokens = self.tokens[1:]
    
    def enter_scope(self):
        self.type_tracker.append({})
        self.struct_label_tracker.append({})
        self.union_label_tracker.append({})
        self.typedef_label_tracker.append({})
        self.enum_tracker.append({})

    def exit_scope(self):
        self.type_tracker.pop()
        self.struct_label_tracker.pop()
        self.union_label_tracker.pop()
        self.typedef_label_tracker.pop()
        self.enum_tracker.pop()
    
    def register_var_type(self, name: str, t: c_type.CType):
        self.type_tracker[-1][name] = t

    def query_var_type(self, name: str) -> c_type.CType:
        for frame in self.type_tracker[::-1]:
            if name in frame:
                return frame[name]
        err = ''
        for frame in self.type_tracker:
            for k, v in frame.items():
                err += f'{k}: {v}'
        raise Exception(f'var {name} has no match, err: {err}')
    
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
    
    def register_typedef_type(self, name: str, t: c_type.CType):
        self.typedef_label_tracker[-1][name] = t

    def query_typedef_type(self, name: str) -> c_type.CType:
        for frame in self.typedef_label_tracker[::-1]:
            if name in frame:
                return frame[name]
        raise Exception(f'typedef {name} has no match')
    
    def register_enum_label(self, name: str, v: int):
        self.enum_tracker[-1][name] = (name, v)
        
    def query_enum_value(self, name: str) -> int:
        for frame in self.enum_tracker[::-1]:
            if name in frame:
                return frame[name][1]
        raise Exception(f'enum {name} has no match')
    
    def has_typedef_type(self, name: str) -> bool:
        for frame in self.typedef_label_tracker[::-1]:
            if name in frame:
                return True
        return False
    
    def has_enum_label(self, name: str) -> bool:
        for frame in self.enum_tracker[::-1]:
            if name in frame:
                return True
        return False

def parse(raw_tokens: list[ctoken.CToken]) -> list[c_ast.VarDefsStmt]:
    tokens: list[ctoken.CToken] = []
    for raw_token in raw_tokens:
        if raw_token.token_type == ctoken.CTokenType.COMMENT_SINGLE_LINE or raw_token.token_type == ctoken.CTokenType.COMMENT_MULTI_LINE:
            continue
        tokens.append(raw_token)
    ctx = ParseContext(tokens)
    ctx.enter_scope()
    # 在全局变量作用域中添加 assert 和 printf
    ctx.register_var_type('assert', c_type.Func([('', c_type.I32()), ('', c_type.I32()), ('', c_type.Ptr(c_type.I8()))], c_type.Void()))
    ctx.register_var_type('printf', c_type.Func([('', c_type.Ptr(c_type.I8()))], c_type.Void()))
    vardefs_stmts: list[c_ast.VarDefsStmt] = []
    while not ctx.end():
        if ctx.current().token_type == ctoken.CTokenType.KEY_TYPEDEF:
            # 处理typedef
            # 这里就没必要注册结果了
            parse_stmt_typedef(ctx)
            continue
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
    elif tt == ctoken.CTokenType.OP_ASN:
        return c_ast.BinOp.ASN
    elif tt == ctoken.CTokenType.OP_ADD_ASN:
        return c_ast.BinOp.ADD_ASN
    elif tt == ctoken.CTokenType.OP_SUB_ASN:
        return c_ast.BinOp.SUB_ASN
    elif tt == ctoken.CTokenType.OP_MUL_ASN:
        return c_ast.BinOp.MUL_ASN
    elif tt == ctoken.CTokenType.OP_DIV_ASN:
        return c_ast.BinOp.DIV_ASN
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
    elif ctx.current().token_type == ctoken.CTokenType.LETTER:
        t = ctx.current()
        ctx.iter()
        e = c_ast.Ltr(t.value[1:len(t.value)-1])
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
        # 如果是enum标签 就解析为数字
        if ctx.has_enum_label(i.value):
            e = c_ast.Num(ctx.query_enum_value(i.value))
            add_type(ctx, e)
        else:
            e = c_ast.Idt(i)
            add_type(ctx, e)
    else:
        raise Exception(f'{ctx.current().token_type} {e}')
    # 对函数调用的情况做处理
    while ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET or \
    ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET or \
    ctx.current().token_type == ctoken.CTokenType.PC_POINT or \
    ctx.current().token_type == ctoken.CTokenType.OP_R_ARROW or \
    ctx.current().token_type == ctoken.CTokenType.OP_ADD_ADD or \
    ctx.current().token_type == ctoken.CTokenType.OP_SUB_SUB:
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
        # 处理 -> 访问操作符
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
        # 处理exp++
        if ctx.current().token_type == ctoken.CTokenType.OP_ADD_ADD:
            ctx.iter()
            op = c_ast.BinOp.ADD_ASN
            const_length = c_ast.Num(1)
            if isinstance(e.type, c_type.Ptr) or isinstance(e.type, c_type.Ary):
                const_length = c_ast.Num(e.type.base.length())
            add_type(ctx, const_length)
            e = c_ast.BinExp(e, op, const_length)
            add_type(ctx, e)
            e = c_ast.BinExp(e, c_ast.BinOp.SUB, const_length)
            add_type(ctx, e)
            continue
        # 处理exp--
        if ctx.current().token_type == ctoken.CTokenType.OP_SUB_SUB:
            ctx.iter()
            op = c_ast.BinOp.SUB_ASN
            const_length = c_ast.Num(1)
            if isinstance(e.type, c_type.Ptr) or isinstance(e.type, c_type.Ary):
                const_length = c_ast.Num(e.type.base.length())
            add_type(ctx, const_length)
            e = c_ast.BinExp(e, op, const_length)
            add_type(ctx, e)
            e = c_ast.BinExp(e, c_ast.BinOp.ADD, const_length)
            add_type(ctx, e)
            continue
        # 处理函数调用
        func_type = e.type
        if e.type is None or not isinstance(func_type, c_type.Func):
            raise Exception('')
        ctx.iter()
        # 解析函数调用
        inargs: list[c_ast.Exp] = []
        while ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
            inargs.append(parse_exp_disable_comma(ctx))
            if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                ctx.iter()
        # 根据函数类型中的入参构造类型转换
        correct_inargs: list[c_ast.Exp] = []
        for i in range(len(inargs)):
            if i >= len(func_type.args):
                raise Exception(f'{e} {func_type.args}')
            inarg_t = inargs[i].type
            if inarg_t is None:
                raise Exception('')
            if not c_type.same_type(func_type.args[i][1], inarg_t):
                new_inarg = c_ast.CastExp(inargs[i], func_type.args[i][1])
                add_type(ctx, new_inarg)
                correct_inargs.append(new_inarg)
            else:
                correct_inargs.append(inargs[i])
        ctx.iter()
        e = c_ast.Call(e, correct_inargs)
        add_type(ctx, e)
    return e

# 解析强制类型转换
def parse_cast_exp(ctx: ParseContext) -> c_ast.Exp:
    # 需要提供上下文支持 is_type_prefix要重构
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET and is_type_prefix(ctx, ctx.next()):
        # 是类型转换 (type)cast_exp
        ctx.iter()
        t = parse_type(ctx)
        ctx.iter()
        e = parse_cast_exp(ctx)
        e = c_ast.CastExp(e, t)
        add_type(ctx, e)
        return e
    # 否则就是常规的uexp
    return parse_uexp(ctx)

# 解析+ - sizeof
def parse_uexp(ctx: ParseContext) -> c_ast.Exp:
    # 另外需要考虑sizeof的情况
    if ctx.current().token_type == ctoken.CTokenType.OP_ADD or \
    ctx.current().token_type == ctoken.CTokenType.OP_SUB or \
    ctx.current().token_type == ctoken.CTokenType.OP_BITS_AND or \
    ctx.current().token_type == ctoken.CTokenType.OP_MUL or \
    ctx.current().token_type == ctoken.CTokenType.OP_ADD_ADD or \
    ctx.current().token_type == ctoken.CTokenType.OP_SUB_SUB:
        # 处理 ++exp的情况
        if ctx.current().token_type == ctoken.CTokenType.OP_ADD_ADD:
            ctx.iter()
            op = c_ast.BinOp.ADD_ASN
            sub = parse_uexp(ctx)
            const_length = c_ast.Num(1)
            # 指针修正
            if isinstance(sub.type, c_type.Ptr) or isinstance(sub.type, c_type.Ary):
                const_length = c_ast.Num(sub.type.base.length())
            add_type(ctx, const_length)
            e = c_ast.BinExp(sub, op, const_length)
            add_type(ctx, e)
            return e
        # 处理 --exp的情况
        if ctx.current().token_type == ctoken.CTokenType.OP_SUB_SUB:
            ctx.iter()
            op = c_ast.BinOp.SUB_ASN
            sub = parse_uexp(ctx)
            const_length = c_ast.Num(1)
            # 指针修正
            if isinstance(sub.type, c_type.Ptr) or isinstance(sub.type, c_type.Ary):
                const_length = c_ast.Num(sub.type.base.length())
            add_type(ctx, const_length)
            e = c_ast.BinExp(sub, op, const_length)
            add_type(ctx, e)
            return e
        bop = parse_binop(ctx)
        uop = c_ast.binop2uop(bop)
        e = c_ast.UExp(uop, parse_uexp(ctx))
        add_type(ctx, e)
        return e
    if ctx.current().token_type == ctoken.CTokenType.KEY_SIZEOF:
        ctx.iter()
        # 括号开头
        if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
            # 读 ( 括号
            ctx.iter()
            e = None
            # 如果是类型开头 则解析类型
            if is_type_prefix(ctx, ctx.current()):
                e = parse_stmt_vardefs(ctx, disable_frame_injection=True)
            else:
                e = parse_exp(ctx)
            # 读 ) 括号
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

# 解析 * /
def parse_binexp_mul(ctx: ParseContext) -> c_ast.Exp:
    l = parse_cast_exp(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_MUL or 
                             ctx.current().token_type == ctoken.CTokenType.OP_DIV):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_cast_exp(ctx))
        universal_convert(ctx, l)
        add_type(ctx, l)
    return l

# 解析 + -
# 思考：+-比较复杂 类型转换应该是怎样的？
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
            add_type(ctx, l)
        # l 非指针 r 指针
        elif not isinstance(l.l.type, c_type.Ptr) and isinstance(l.r.type, c_type.Ptr):
            const_len = c_ast.Num(l.r.type.length())
            add_type(ctx, const_len)
            neo_l = c_ast.BinExp(l.l, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_l)
            l.l = neo_l
            add_type(ctx, l)
        # l 指针 r指针
        elif isinstance(l.l.type, c_type.Ptr) and isinstance(l.r.type, c_type.Ptr):
            if not l.op == c_ast.BinOp.SUB:
                raise Exception(f'pointer calc error: {l.op}')
            add_type(ctx, l)
            const_len = c_ast.Num(l.l.type.base.length())
            add_type(ctx, const_len)
            l = c_ast.BinExp(l, c_ast.BinOp.DIV, const_len)
            add_type(ctx, l)
        elif isinstance(l.l.type, c_type.Ary) and not isinstance(l.r.type, c_type.Ary):
            const_len = c_ast.Num(l.l.type.base.length())
            add_type(ctx, const_len)
            neo_r = c_ast.BinExp(l.r, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_r)
            l.r = neo_r
            add_type(ctx, l)
        elif not isinstance(l.l.type, c_type.Ary) and isinstance(l.r.type, c_type.Ary):
            const_len = c_ast.Num(l.r.type.length())
            add_type(ctx, const_len)
            neo_l = c_ast.BinExp(l.l, c_ast.BinOp.MUL, const_len)
            add_type(ctx, neo_l)
            l.l = neo_l
            add_type(ctx, l)
        else: # 为什么会报错？
            universal_convert(ctx, l)
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
        universal_convert(ctx, l)
        add_type(ctx, l)
    return l

# 求兼容类型
def type_compatibalize(l: c_type.CType, r: c_type.CType) -> c_type.CType:
    # 其实我不是很理解这一步 但是原作者提供了 我们也跟进
    if isinstance(l, c_type.Ptr) or isinstance(l, c_type.Ary):
        return c_type.Ptr(l.base)
    if isinstance(l, c_type.I64) or isinstance(r, c_type.I64):
        return c_type.I64()
    return c_type.I32()

# 处理通用表达式类型转换的逻辑
def universal_convert(ctx: ParseContext, e: c_ast.Exp):
    # binexp
    if isinstance(e, c_ast.BinExp):
        if e.l.type is None or e.r.type is None:
            raise Exception(f'{e} {e.l} {e.r}')
        type_compatible = type_compatibalize(e.l.type, e.r.type)
        if not c_type.same_type(e.l.type, type_compatible):
            e.l = c_ast.CastExp(e.l, type_compatible)
            add_type(ctx, e.l)
        if not c_type.same_type(e.r.type, type_compatible):
            e.r = c_ast.CastExp(e.r, type_compatible)
            add_type(ctx, e.r)
    # 处理 单目运算符-的类型转换 我有个问题：为什么要把-转换成i32或者i64?
    if isinstance(e, c_ast.UExp):
        # 对neg进行处理。 困难是什么？
        if not isinstance(e.exp, c_ast.Exp):
            return
        if e.exp.type is None:
            raise Exception('')
        type_compatible = type_compatibalize(c_type.I32(), e.exp.type)
        if not c_type.same_type(e.exp.type, type_compatible):
            e.exp = c_ast.CastExp(e.exp, type_compatible)
            add_type(ctx, e.exp)

# 思考：提供类型提升的逻辑 先计算l和r的类型提升结果 按照是否相同来进行类型转换
def parse_binexp_eq(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_lt(ctx)
    while not ctx.end() and (ctx.current().token_type == ctoken.CTokenType.OP_EQ or 
                             ctx.current().token_type == ctoken.CTokenType.OP_NE):
        op = parse_binop(ctx)
        l = c_ast.BinExp(l, op, parse_binexp_lt(ctx))
        # 执行转换的构造 如果有必要
        universal_convert(ctx, l)
        # 进行类型提升
        add_type(ctx, l)
    return l

# 现在要引进对+= -= *= /= 的支持
def parse_binexp_asn(ctx: ParseContext) -> c_ast.Exp:
    l = parse_binexp_eq(ctx)
    while not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN or \
    ctx.current().token_type == ctoken.CTokenType.OP_ADD_ASN or \
    ctx.current().token_type == ctoken.CTokenType.OP_SUB_ASN or \
    ctx.current().token_type == ctoken.CTokenType.OP_MUL_ASN or \
    ctx.current().token_type == ctoken.CTokenType.OP_DIV_ASN:
        # 相应的 这里的类型处理也需要重构
        op = parse_binop(ctx)
        r = parse_binexp_asn(ctx)
        if l.type is None or r.type is None:
            raise Exception('')
        # 讨论：= 和+= -=的不同是什么？= 的类型转换是，右强转到左。+= 的不同是什么？要考虑指针运算的偏移量修改。
        # int = long -> int = (int)long
        # ptr += 1 -> ptr += 1 * 8
        # 我觉得有必要分开处理
        # 如果r的类型和l不相同 则构建类型转换
        if op == c_ast.BinOp.ASN:
            if not c_type.same_type(l.type, r.type):
                r = c_ast.CastExp(r, l.type)
                add_type(ctx, r)
            l = c_ast.BinExp(l, op, r)
            add_type(ctx, l)
        elif op == c_ast.BinOp.ADD_ASN:
            # 对指针/数组的处理：exp1 += exp2 -> exp1 += exp2 * exp1.base.length()
            if isinstance(l.type, c_type.Ptr) or isinstance(l.type, c_type.Ary):
                # 构造 const_length
                const_length = c_ast.Num(l.type.base.length())
                add_type(ctx, const_length)
                # 构造 exp2 * const_length
                r = c_ast.BinExp(r, c_ast.BinOp.MUL, const_length)
                # 处理可能需要的类型转换
                # universal_convert(ctx, r)
                add_type(ctx, r)
                # 构造 exp1 += exp2 * const_length
                l = c_ast.BinExp(l, op, r)
                add_type(ctx, l)
            # 常规情况
            else:
                # 构造 exp1 += exp2
                l = c_ast.BinExp(l, op, r)
                add_type(ctx, l)
        elif op == c_ast.BinOp.SUB_ASN:
            # 对指针/数组的处理：exp1 += exp2 -> exp1 += exp2 * exp1.base.length()
            if isinstance(l.type, c_type.Ptr) or isinstance(l.type, c_type.Ary):
                # 构造 const_length
                const_length = c_ast.Num(l.type.base.length())
                add_type(ctx, const_length)
                # 构造 exp2 * const_length
                r = c_ast.BinExp(r, c_ast.BinOp.MUL, const_length)
                # 处理可能需要的类型转换
                # universal_convert(ctx, r)
                add_type(ctx, r)
                # 构造 exp1 -= exp2 * const_length
                l = c_ast.BinExp(l, op, r)
                add_type(ctx, l)
            # 常规情况
            else:
                # 构造 exp1 -= exp2
                l = c_ast.BinExp(l, op, r)
                add_type(ctx, l)
        elif op == c_ast.BinOp.MUL_ASN:
            # 不存在指针相关的特化。所以直接构造并处理转换。
            l = c_ast.BinExp(l, op, r)
            # universal_convert(ctx, l)
            add_type(ctx, l)
        elif op == c_ast.BinOp.DIV_ASN:
            # 不存在指针相关的特化。所以直接构造并处理转换。
            l = c_ast.BinExp(l, op, r)
            # universal_convert(ctx, l)
            add_type(ctx, l)
        else:
            raise Exception(f'invalid operator: {op}')
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
    elif is_type_prefix(ctx, ctx.current()):
        result = parse_stmt_vardefs(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_RETURN:
        result = parse_stmt_ret(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_IF:
        result = parse_stmt_if(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_FOR:
        result = parse_stmt_for(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_WHILE:
        result = parse_stmt_while(ctx)
    elif ctx.current().token_type == ctoken.CTokenType.KEY_TYPEDEF:
        result = parse_stmt_typedef(ctx)
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
# 换用neo_parse_vardescribe
def parse_stmt_vardefs(ctx: ParseContext, disable_frame_injection: bool = False) -> c_ast.Stmt:
    t = parse_type(ctx)
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        return c_ast.VarDefsStmt(t, [])
    vardescribes: list[c_ast.VarDescribe] = [neo_parse_vardescribe(ctx, t, disable_frame_injection)]
    # 如果我们解析了一个函数定义，那就应当注册函数名到type_tracker中 然后直接返回
    if isinstance(vardescribes[0].get_type(), c_type.Func) and vardescribes[0].body is not None:
        # 把函数名注册为函数变量
        ctx.register_var_type(vardescribes[0].get_name(), vardescribes[0].get_type())
        return c_ast.VarDefsStmt(t, vardescribes)
    # 常规定义
    while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON and ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
        ctx.iter()
        vardescribes.append(neo_parse_vardescribe(ctx, t, disable_frame_injection))
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
    return c_ast.VarDefsStmt(t, vardescribes)

def is_type_prefix(ctx: ParseContext, tk: ctoken.CToken) -> bool:
    '''
    描述: 判断是否为类型前缀
    param  ctx: 解析上下文
    return 布尔值
    '''
    t = tk.token_type
    return is_integer_prefix(ctx, tk) or \
        t == ctoken.CTokenType.KEY_VOID or \
        t == ctoken.CTokenType.KEY_STRUCT or \
        t == ctoken.CTokenType.KEY_UNION or \
        t == ctoken.CTokenType.KEY_ENUM or \
        ctx.has_typedef_type(tk.value)
        # ctx.has_enum(tk.value)

def is_integer_prefix(ctx: ParseContext, tk: ctoken.CToken) -> bool:
    '''
    描述：判断是否为整型前缀
    param  ctx: 解析上下文
    return 布尔值
    '''
    t = tk.token_type
    return t == ctoken.CTokenType.KEY_LONG or \
        t == ctoken.CTokenType.KEY_INT or \
        t == ctoken.CTokenType.KEY_SHORT or \
        t == ctoken.CTokenType.KEY_CHAR or \
        t == ctoken.CTokenType.KEY__BOOL

# 修改方向：提供对static的支持
# 我要问的是：应当如何对parse_stmt_vardefs提供支持？我们需要把static给添加到VarDescribe的特性中
def parse_type(ctx: ParseContext) -> c_type.CType:
    '''
    描述：对type进行parse
    param  ctx: 解析上下文
    return 所解析得到的类型
    '''
    # 对前置的static 进行处理
    # 在integer中对static进行处理
    # 在parse结束后对static进行处理
    # 不需要修改struct 、union 中的static 设定 
    # 在add_type的时候（也就是计算表达式时完成修改）
    static_ctr = 0
    if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC:
        static_ctr += 1
        ctx.iter()
    if is_integer_prefix(ctx, ctx.current()):
        # 按顺序解析所有的操作空间
        long_ctr, int_ctr, short_ctr, char_ctr, _bool_ctr = 0, 0, 0, 0, 0
        while is_integer_prefix(ctx, ctx.current()) or ctx.current().token_type == ctoken.CTokenType.KEY_STATIC:
            t = ctx.current().token_type
            if t == ctoken.CTokenType.KEY_LONG:
                long_ctr += 1
            elif t == ctoken.CTokenType.KEY_INT:
                int_ctr += 1
            elif t == ctoken.CTokenType.KEY_SHORT:
                short_ctr += 1
            elif t == ctoken.CTokenType.KEY_CHAR:
                char_ctr += 1
            elif t == ctoken.CTokenType.KEY__BOOL:
                _bool_ctr += 1
            elif t == ctoken.CTokenType.KEY_STATIC:
                static_ctr += 1
            ctx.iter()
        if long_ctr >= 1:
            t = c_type.I64()
            if static_ctr > 0:
                t.static = True
            return t
        if short_ctr == 1:
            t = c_type.I16()
            if static_ctr > 0:
                t.static = True
            return t
        if int_ctr == 1:
            t = c_type.I32()
            if static_ctr > 0:
                t.static = True
            return t
        if char_ctr == 1:
            t = c_type.I8()
            if static_ctr > 0:
                t.static = True
            return t
        if _bool_ctr == 1:
            t = c_type.Bool()
            if static_ctr > 0:
                t.static = True
            return t
        raise Exception('not expected')
    # 处理void
    if ctx.current().token_type == ctoken.CTokenType.KEY_VOID:
        ctx.iter()
        t = c_type.Void()
        # 处理static
        if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
            t.static = True
            ctx.iter()
        return t
    # 处理struct
    if ctx.current().token_type == ctoken.CTokenType.KEY_STRUCT:
        # 处理static (未完成)
        # 读取struct
        ctx.iter()
        label: None|str = None
        # 读取可能存在的label
        if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
            label = ctx.current().value
            ctx.iter()
        items: list[tuple[str, c_type.CType]] = []
        # 说明我们是要使用已有的struct 而不是构造新的struct 此时可能是 struct t static
        if ctx.current().token_type != ctoken.CTokenType.PC_L_CURLY_BRACKET:
            if label is None:
                raise Exception('')
            t = ctx.query_struct_type(label)
            # 如果当前是static
            if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
                ctx.iter()
                t.static = True
                return t
            return t
        # 读取{
        ctx.iter()
        while ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
            vardefsstmt = parse_stmt_vardefs(ctx, disable_frame_injection=True)
            if not isinstance(vardefsstmt, c_ast.VarDefsStmt):
                raise Exception('')
            for vardescribe in vardefsstmt.var_describes:
                items.append((vardescribe.get_name(), vardescribe.get_type()))
        # 读取}
        ctx.iter()
        # 构造结构体类型
        cstruct_t = c_type.CStruct(label, items)
        # 处理可能遇到的static
        if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
            cstruct_t.static = True
            ctx.iter()
        # 存在一个可感知的名称 将label注册到struct的tracker中
        if label is not None:
            ctx.register_struct_label(label, cstruct_t)
        return cstruct_t
    # 处理union
    if ctx.current().token_type == ctoken.CTokenType.KEY_UNION:
        ctx.iter()
        label: None|str = None
        # 读取可能存在的union label, 下面会使用它从ctx中索取已有类型
        if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
            label = ctx.current().value
            ctx.iter()
        # 说明我们是要使用已有的struct 而不是构造新的struct
        if ctx.current().token_type != ctoken.CTokenType.PC_L_CURLY_BRACKET:
            if label is None:
                raise Exception('')
            t = ctx.query_union_type(label)
            # 处理可能出现的static标识符
            if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
                ctx.iter()
                t.static = True
            return t
        # 跳过{
        ctx.iter()
        items: list[tuple[str, c_type.CType]] = []
        while ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
            vardefsstmt = parse_stmt_vardefs(ctx, disable_frame_injection=True)
            if not isinstance(vardefsstmt, c_ast.VarDefsStmt):
                raise Exception('')
            for vardescribe in vardefsstmt.var_describes:
                items.append((vardescribe.get_name(), vardescribe.get_type()))
        # 跳过}
        ctx.iter()
        # 构造结构体类型
        cstruct_t = c_type.CUnion(label, items)
        # 处理可能遇到的static
        if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
            cstruct_t.static = True
            ctx.iter()
        # 存在一个可感知的名称 将label注册到struct的tracker中
        if label is not None:
            ctx.register_union_label(label, cstruct_t)
        return cstruct_t
    # 处理enum
    if ctx.current().token_type == ctoken.CTokenType.KEY_ENUM:
        # 跳过enum
        ctx.iter()
        # 我们不在乎某个enum的名称
        if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
            ctx.iter()
        # 没有左花括号 我们是在使用已有的enum
        if ctx.current().token_type != ctoken.CTokenType.PC_L_CURLY_BRACKET:
            return c_type.I32()
        # 解析enum的每个item
        # 读取{
        ctx.iter()
        # enum条目计数器 比较可惜的是 暂时没提供对enum label的支持 思考提供这个功能
        cur_enum_val = 0
        while ctx.current().token_type != ctoken.CTokenType.PC_R_CURLY_BRACKET:
            name = ctx.current().value
            ctx.iter()
            if ctx.current().token_type == ctoken.CTokenType.OP_ASN:
                ctx.iter()
                cur_enum_val = int(ctx.current().value)
                ctx.iter()
            if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                ctx.iter()
            ctx.register_enum_label(name, cur_enum_val)
            cur_enum_val += 1
        # 读取}
        ctx.iter()
        return c_type.I32()
    # 没有匹配项 从typedef中找
    cur_tk = ctx.current()
    ctx.iter()
    t = ctx.query_typedef_type(cur_tk.value)
    # 处理可能出现的static
    if ctx.current().token_type == ctoken.CTokenType.KEY_STATIC or static_ctr > 0:
        t.static = True
        ctx.iter()
    return t

def parse_param(ctx: ParseContext) -> c_ast.VarDefsStmt:
    t = parse_type(ctx)
    vardescribes: list[c_ast.VarDescribe] = [neo_parse_vardescribe(ctx, t)]
    return c_ast.VarDefsStmt(t, vardescribes)

def neo_parse_vardescribe(ctx: ParseContext, deep_type: c_type.CType, disalbe_type_register: bool = False) -> c_ast.VarDescribe:
    var_describe = neo_parse_vardescribe_prefix(ctx)
    neo_vardescribe_add_type(ctx, var_describe, deep_type)
    if not disalbe_type_register:
        ctx.register_var_type(var_describe.get_name(), var_describe.get_type())
    # 对可能出现的赋值进行处理
    if not ctx.end() and ctx.current().token_type == ctoken.CTokenType.OP_ASN:
        ctx.iter()
        # 考虑类型转换。
        init = parse_exp_disable_comma(ctx)
        # t 和get_type()的区别是什么？
        if init.type is None:
            raise Exception(f'{var_describe} {var_describe.t} {init.type}')
        if not c_type.same_type(var_describe.get_type(), init.type):
            init = c_ast.CastExp(init, var_describe.get_type())
            add_type(ctx, init)
        var_describe.init = init
        return var_describe
    if not ctx.end() and ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
        if not isinstance(var_describe.get_type(), c_type.Func):
            raise Exception(f'{var_describe.t}')
        t = var_describe.get_type()
        if not isinstance(t, c_type.Func):
            raise Exception(f'{t}')
        ctx.ret_type = t.ret
        body = parse_stmt(ctx)
        var_describe.body = body
        return var_describe
    return var_describe

def neo_parse_vardescribe_prefix(ctx: ParseContext) -> c_ast.VarDescribe:
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        ctx.iter()
        privilege_vardescribe = neo_parse_vardescribe_prefix(ctx)
        ctx.iter()
        cur_vardescribe = neo_parse_vardescribe_suffix(ctx, privilege_vardescribe)
        return cur_vardescribe
    if ctx.current().token_type == ctoken.CTokenType.OP_MUL:
        ctx.iter()
        r_vardescribe = neo_parse_vardescribe_prefix(ctx)
        cur_vardescribe = c_ast.PtrVarDescribe(r_vardescribe)
        return cur_vardescribe
    if ctx.current().token_type == ctoken.CTokenType.IDENTIFIER:
        n_vardescribe = c_ast.NormalVarDescribe(ctx.current(), None)
        ctx.iter()
        cur_vardescribe = neo_parse_vardescribe_suffix(ctx, n_vardescribe)
        return cur_vardescribe
    # 不应该提供ghost?
    # 不对 应该提供 但是不应该在什么地方提供？
    g_vardescribe = c_ast.GhostVarDescribe(None)
    cur_vardescribe = neo_parse_vardescribe_suffix(ctx, g_vardescribe)
    return cur_vardescribe

def neo_parse_vardescribe_suffix(ctx: ParseContext, vardescribe: c_ast.VarDescribe) -> c_ast.VarDescribe:
    # 不应当在这里试图对=进行捕获
    # vardescribe是我们已经拥有的（它会是normal_vardescribe）
    # 函数定义（或是声明）
    if ctx.current().token_type == ctoken.CTokenType.PC_L_ROUND_BRACKET:
        # 在解析之前应当把自己注册到作用域中
        # 问题就出在这里
        ctx.iter()
        params: list[c_ast.VarDefsStmt] = []
        while not ctx.end() and ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
            params.append(parse_param(ctx))
            if ctx.current().token_type == ctoken.CTokenType.PC_COMMA:
                ctx.iter()
        ctx.iter()
        # 提问：这是不是说明 不应当在这个阶段获取body?
        # body: c_ast.Stmt|None = None
        if ctx.current().token_type == ctoken.CTokenType.PC_L_CURLY_BRACKET:
            # body = parse_stmt(ctx)
            # 因为解析完函数体后已经没有必要继续 试图解析剩余的修饰了，这里直接return
            # 这是一个例外，其他情况下我们都应当继续递归parse的
            # 直接返回 因为已经调用完了
            return c_ast.FuncVarDescribe(vardescribe, params, None)
        func_vardescribe = c_ast.FuncVarDescribe(vardescribe, params, None)
        # 继续解析
        return neo_parse_vardescribe_suffix(ctx, func_vardescribe)
    if ctx.current().token_type == ctoken.CTokenType.PC_L_SQUARE_BRACKET:
        ctx.iter()
        idx = int(ctx.current().value)
        ctx.iter()
        ctx.iter()
        ary_vardescribe = c_ast.AryVarDescribe(vardescribe, idx)
        # 继续解析
        return neo_parse_vardescribe_suffix(ctx, ary_vardescribe)
    return vardescribe

def neo_vardescribe_add_type(ctx: ParseContext, vardescribe: c_ast.VarDescribe, deep_type: c_type.CType):
    # vardescribe是FuncVarDescribe，构造函数类型
    if isinstance(vardescribe, c_ast.FuncVarDescribe):
        # 对函数的参数进行类型解析
        params_type: list[tuple[str, c_type.CType]] = []
        for param in vardescribe.params:
            neo_vardescribe_add_type(ctx, param.var_describes[0], param.btype)
            params_type.append((param.var_describes[0].get_name(), param.var_describes[0].get_type()))
        # 构造函数签名
        deep_type = c_type.Func(params_type, deep_type)
        # 对函数的 函数提供源头进行类型解析
        neo_vardescribe_add_type(ctx, vardescribe.vardescribe, deep_type)
        return
    # vardescribe是数组类型，构造数组类型
    if isinstance(vardescribe, c_ast.AryVarDescribe):
        # 构造数组类型
        deep_type = c_type.Ary(deep_type, vardescribe.length)
        # 对数组修饰的变量进行类型解析
        neo_vardescribe_add_type(ctx, vardescribe.vardescribe, deep_type)
        return
    # vardescribe是Ptr类型，构造指针类型
    if isinstance(vardescribe, c_ast.PtrVarDescribe):
        # 构造指针类型
        deep_type = c_type.Ptr(deep_type)
        # 对指针修饰的变量进行类型解析
        neo_vardescribe_add_type(ctx, vardescribe.vardescribe, deep_type)
        return
    # 如果是normal 就直接设置类型为deep_type
    if isinstance(vardescribe, c_ast.NormalVarDescribe) or isinstance(vardescribe, c_ast.GhostVarDescribe):
        vardescribe.t = deep_type
        return
    raise Exception('')

# 解析return表达式
# 需要跟踪当前解析函数的类型
def parse_stmt_ret(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    if ctx.current().token_type == ctoken.CTokenType.PC_SEMICOLON:
        ctx.iter()
        return c_ast.RetStmt(None)
    value = parse_exp(ctx)
    if ctx.ret_type is None or value.type is None:
        raise Exception('')
    # 进行类型兼容 有这个必要吗？
    # type_compatibalize(ctx.ret_type, value.type)
    # 枚举值进行类型转换的地方有问题
    if not c_type.same_type(ctx.ret_type, value.type):
        value = c_ast.CastExp(value, ctx.ret_type)
        add_type(ctx, value)
    ctx.iter()
    return c_ast.RetStmt(value)

def parse_stmt_if(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    cond = parse_exp(ctx)
    t = parse_stmt(ctx)
    if ctx.current().token_type == ctoken.CTokenType.KEY_ELSE:
        ctx.iter()
        f = parse_stmt(ctx) # 有这样的情况吗
        return c_ast.IfStmt(cond, t, f)
    return c_ast.IfStmt(cond, t, None)

def parse_stmt_for(ctx: ParseContext) -> c_ast.Stmt:
    # 进入作用域
    ctx.enter_scope()
    # 可以选择修改for的init结构，比如变成VarDefsStmt|Exp|None
    # 跳过'for'
    ctx.iter()
    # 跳过(
    ctx.iter()
    # 解析init. init可以是：1）空 2）VarDefsStmt 3）Exp
    init: None|c_ast.VarDefsStmt|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        # init是VarDefsStmt
        if is_type_prefix(ctx, ctx.current()):
            init_vardefs_stmt = parse_stmt_vardefs(ctx)
            if not isinstance(init_vardefs_stmt, c_ast.VarDefsStmt):
                raise Exception('')
            init = init_vardefs_stmt
        # init 是Exp
        else:
            init = parse_exp(ctx)
            ctx.iter()
    # init 为空. 跳过分号
    else:
        ctx.iter()
    # 解析cond. cond可以是：1)空 2)Exp
    cond: None|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_SEMICOLON:
        cond = parse_exp(ctx)
    ctx.iter()
    # 解析step. step可以是：1)空 2)Exp
    step: None|c_ast.Exp = None
    if ctx.current().token_type != ctoken.CTokenType.PC_R_ROUND_BRACKET:
        step = parse_exp(ctx)
    ctx.iter()
    # 解析for的主体部分
    body = parse_stmt(ctx)
    # 退出作用域
    ctx.exit_scope()
    # 构造For的AST
    for_ast = c_ast.ForStmt(init, cond, step, body)
    # 将init中所有的变量注册到for_ast的varinfos字段中
    if not init is None and isinstance(init, c_ast.VarDefsStmt):
        for vardescribe in init.var_describes:
            vi = varinfo.VarInfo(vardescribe.get_name())
            vi.t = vardescribe.get_type()
            for_ast.varinfos.append(vi)
    return for_ast

def parse_stmt_while(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    cond = parse_exp(ctx)
    body = parse_stmt(ctx)
    return c_ast.WhileStmt(cond, body)

def parse_stmt_typedef(ctx: ParseContext) -> c_ast.Stmt:
    ctx.iter()
    vardefs = parse_stmt_vardefs(ctx, disable_frame_injection=True)
    if not isinstance(vardefs, c_ast.VarDefsStmt):
        raise Exception('')
    # 判断一下需不需要一个兼容typedef t;的分支
    for vardescribe in vardefs.var_describes:
        ctx.register_typedef_type(vardescribe.get_name(), vardescribe.get_type())
    return c_ast.TypedefStmt()

# 下面的代码我完全没有审阅 重新观察 等待修改
def add_type(ctx: ParseContext, exp: c_ast.Exp):
    if isinstance(exp, c_ast.Num):
        if utils.i32_sufficient(int(exp.value)):
            exp.type = c_type.I32()
        else:
            exp.type = c_type.I64()
    elif isinstance(exp, c_ast.Str):
        exp.type = c_type.Ary(c_type.I8(), len(exp.value) + 1)
    elif isinstance(exp, c_ast.Ltr):
        exp.type = c_type.I8()
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
        # 加法
        if exp.op == c_ast.BinOp.ADD:
            # 指针 + 非指针
            if isinstance(exp.l.type, c_type.Ptr) and not isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.l.type
            # 非指针 + 指针
            elif not isinstance(exp.l.type, c_type.Ptr) and isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.r.type
            # 数组 + 非数组
            elif isinstance(exp.l.type, c_type.Ary) and not isinstance(exp.r.type, c_type.Ary):
                exp.type = c_type.Ptr(exp.l.type.base)
            # 非数组 + 数组
            elif not isinstance(exp.l.type, c_type.Ary) and isinstance(exp.r.type, c_type.Ary):
                exp.type = c_type.Ptr(exp.r.type.base)
            else:
                exp.type = exp.l.type
        elif exp.op == c_ast.BinOp.SUB:
            if isinstance(exp.l.type, c_type.Ptr) and not isinstance(exp.r.type, c_type.Ptr):
                exp.type = exp.l.type
            elif isinstance(exp.l.type, c_type.Ptr) and isinstance(exp.r.type, c_type.Ptr):
                exp.type = c_type.I64()
            else:
                exp.type = exp.l.type
        elif exp.op == c_ast.BinOp.MUL:
            exp.type = exp.l.type
        elif exp.op == c_ast.BinOp.DIV:
            exp.type = exp.l.type
        elif (exp.op == c_ast.BinOp.EQ or exp.op == c_ast.BinOp.NE or exp.op == c_ast.BinOp.LT or 
              exp.op == c_ast.BinOp.LE or exp.op == c_ast.BinOp.GT or exp.op == c_ast.BinOp.GE):
            exp.type = c_type.I64()
        elif exp.op == c_ast.BinOp.ASN or exp.op == c_ast.BinOp.ADD_ASN or exp.op == c_ast.BinOp.SUB_ASN or exp.op == c_ast.BinOp.MUL_ASN or exp.op == c_ast.BinOp.DIV_ASN:
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
        # sizeof的右侧如果是Stmt那么不需要进行类型处理
        # 这里有问题
        if exp.op == c_ast.UOp.SIZEOF:
            exp.type = c_type.I32()
            return
        if isinstance(exp.exp, c_ast.Stmt):
            raise Exception('')
        if exp.exp.type is None:
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
        else:
            raise Exception('')
    elif isinstance(exp, c_ast.CastExp):
        exp.type = exp.cast_to
    else:
        raise Exception('')

if __name__ == '__main__':
    tokens = ctokenize.tokenize('int main() {return 1;}')
    ast = parse(tokens)
    print('Hello, world')

# 我在思考的是 是不是应当修改获取变量地址的路径 而不是从parse_context中获取？