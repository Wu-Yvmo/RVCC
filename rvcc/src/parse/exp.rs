use crate::{ast::{self, Program}, parse::{parse_blk_stmt, ParseContext}, token, r#type::{self, I32}, utils};
// 我们要实现的exp的解析，无非是递归的处理下面的情况：
// expr = assign ("," expr)?
//
// assign = conditional (assignOp assign)?
//
// conditional = logOr ("?" expr ":" conditional)?
//
// logOr = logAnd ("||" logAnd)*
//
// logAnd = bitOr ("&&" bitOr)*
//
// bitOr = bitXor ("|" bitXor)*
//
// bitXor = bitAnd ("^" bitAnd)*
//
// bitAnd = equality ("&" equality)*
//
// assignOp = "=" | "+=" | "-=" | "*=" | "/=" | "%=" | "&=" | "|=" | "^="
//          | "<<=" | ">>="
//
// equality = relational ("==" relational | "!=" relational)*
//
// relational = shift ("<" shift | "<=" shift | ">" shift | ">=" shift)*
//
// shift = add ("<<" add | ">>" add)*
//
// add = mul ("+" mul | "-" mul)*
//
// mul = cast ("*" cast | "/" cast | "%" cast)*
//
// cast = "(" typeName ")" cast | unary
//
// unary = ("+" | "-" | "*" | "&" | "!" | "~") cast
//     | ("++" | "--") unary
//     | postfix
//
// postfix = primary ( "(" funcArgs? ")" | "[" expr "]" | "." ident)* | "->" ident | "++" | "--")*
//
// primary = "(" "{" stmt+ "}" ")"
//         | "(" expr ")"
//         | "sizeof" "(" typeName ")"
//         | "sizeof" unary
//         | ident
//         | str
//         | num

// expr = assign ("," expr)?
pub fn parse_exp(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// assign = conditional (assignOp assign)?
pub fn parse_assign(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// conditional = logOr ("?" expr ":" conditional)?
pub fn parse_conditional(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// logOr = logAnd ("||" logAnd)*
pub fn parse_logic_or(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// logAnd = bitOr ("&&" bitOr)*
pub fn parse_logic_and(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// bitOr = bitXor ("|" bitXor)*
pub fn parse_bit_or(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// bitXor = bitAnd ("^" bitAnd)*
pub fn parse_bit_xor(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// bitAnd = equality ("&" equality)*
pub fn parse_bit_and(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// assignOp = "=" | "+=" | "-=" | "*=" | "/=" | "%=" | "&=" | "|=" | "^="
//     | "<<=" | ">>="
pub fn parse_assigns(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// equality = relational ("==" relational | "!=" relational)*
pub fn parse_equality(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// relational = shift ("<" shift | "<=" shift | ">" shift | ">=" shift)*
pub fn parse_relational(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// shift = add ("<<" add | ">>" add)*
pub fn parse_shift(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// add = mul ("+" mul | "-" mul)*
pub fn parse_add(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// mul = cast ("*" cast | "/" cast | "%" cast)*
pub fn parse_mul(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// cast = "(" typeName ")" cast | unary
pub fn parse_cast(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// unary = ("+" | "-" | "*" | "&" | "!" | "~") cast
//     | ("++" | "--") unary
//     | "sizeof" "(" typeName ")"
//     | "sizeof" unary
//     | postfix
// 我的猜测是，这里的对typename的解析应该是不好用的部分。
pub fn parse_unary(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// postfix = primary ( "(" funcArgs? ")" | "[" expr "]" | "." ident)* | "->" ident | "++" | "--")*
pub fn parse_postfix(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}

// primary = "(" "{" stmt+ "}" ")"
//         | "(" expr ")"
//         | ident
//         | str
//         | num
pub fn parse_primary(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    match ctx.current().token_type {
        token::TokenType::PC_L_CURLY_BRACKET => {
            let mut blk_exp = ast::Exp::BlkExp(ast::BlkExp{
                blk: Box::new(match parse_blk_stmt(ctx, program) {
                    ast::Stmt::Blk(blk) => blk,
                    _ => panic!("must be blkstmt")
                }),
                t: None
            });
            do_cast_if_necessary(&mut blk_exp);
            add_type(program, &mut blk_exp);
            blk_exp
        }
        token::TokenType::PC_L_ROUND_BRACKET => {
            ctx.jump();
            let mut e = parse_exp(ctx, program);
            ctx.jump();
            do_cast_if_necessary(&mut e);
            add_type(program, &mut e);
            e 
        }
        token::TokenType::IDENTIFIER => {
            utils::make_sure(program.exist_var_name(ctx.current().content.clone()), "no such var");
            let mut ident = ast::Exp::IdentExp(ast::IdentExp{
                ident: ctx.current().content.clone(),
                t: None,
            });
            ctx.jump();
            do_cast_if_necessary(&mut ident);
            add_type(program, &mut ident);
            ident
        }
        token::TokenType::STRING => {
            let cooked = utils::eval_str(ctx.current().content.clone());
            ctx.jump();
            let mut str_ltr = ast::Exp::StrLtrExp(ast::StrLtrExp{
                content: cooked.clone(),
                t: None,
            });
            program.strs.push({
                let mut cooked_str = "".to_string();
                for c in cooked.iter() {
                    cooked_str.push(*c);
                }
                cooked_str
            });
            do_cast_if_necessary(&mut str_ltr);
            add_type(program, &mut str_ltr);
            str_ltr
        }
        token::TokenType::NUMBER => {
            let num = utils::eval_i(ctx.current().content.clone());
            let mut num = ast::Exp::NumLtrExp(ast::NumLtrExp{
                value: num,
                t: None,
            });
            do_cast_if_necessary(&mut num);
            add_type(program, &mut num);
            num
        }
        _ => panic!("unknown token type")
    }
}

/// # 功能描述
/// 向表达式添加类型，该类型从表达式的左右子表达式推导得到。在调用该函数前，
/// 必须保证表达式已经被调用do_cast_if_necessary
pub fn add_type(program: &Program, e: &mut ast::Exp)  {
    match e {
        ast::Exp::BExp(bexp) => {
            // todo:在add_type这里本来是需要根据指针的类型来修改bexp的类型的
            bexp.t = Some(bexp.l.get_type());
        }
        ast::Exp::UExp(uexp) => {
            uexp.t = Some(uexp.sub.get_type());
        }
        ast::Exp::TripleExp(triple_exp) => {
            triple_exp.t = Some(triple_exp.true_branch.get_type());
        }
        ast::Exp::TypeCastExp(type_cast_exp) => {
            type_cast_exp.t = Some(type_cast_exp.target_type.clone());
        }
        ast::Exp::NumLtrExp(num_ltr_exp) => {
            num_ltr_exp.t = Some(if num_ltr_exp.value as u32 as usize == num_ltr_exp.value {
                r#type::Type::create_i32()
            } else {
                r#type::Type::create_i64()
            });
        }
        ast::Exp::StrLtrExp(str_ltr_exp) => {
            str_ltr_exp.t = Some(r#type::Type::create_ptr_of(Box::new(r#type::Type::create_i8())));
        }
        ast::Exp::CharLtrExp(char_ltr_exp) => {
            char_ltr_exp.t = Some(r#type::Type::create_i8());
        }
        ast::Exp::IdentExp(ident_exp) => {
            // 这里显然要用到program,把它添加进来
            let t = program.get_var_type(ident_exp.ident.clone());
            ident_exp.t = Some(t);
        }
        ast::Exp::CallExp(call_exp) => {
            let callable_t = call_exp.callable.get_type();
            let function_t = callable_t.as_function();
            call_exp.t = Some(function_t.return_type.as_ref().clone());
        }
        ast::Exp::BlkExp(blk_exp) => {
            if blk_exp.blk.stmts.len() == 0 {
                blk_exp.t = Some(r#type::Type::create_void());
                return;
            }
            match blk_exp.blk.stmts.last().unwrap() {
                ast::Stmt::Exp(exp) => blk_exp.t = Some(exp.exp.get_type()),
                _ => blk_exp.t = Some(r#type::Type::VOID)
            };
        }
        ast::Exp::Sizeof(sizeof_exp) => {
            sizeof_exp.t = Some(r#type::Type::create_i32());
        }
    }
}

/// # 功能描述
/// 当表达式两侧的类型不一致时，执行转换
pub fn do_cast_if_necessary(e: &mut ast::Exp) {
    match e {
        ast::Exp::BExp(bexp) => {
            let t = type_align(bexp.l.get_type(), bexp.r.get_type());
            // 处理左子表达式的类型转换
            if !same_type(t.clone(), bexp.l.get_type()) {
                let l = bexp.l.clone();
                bexp.l = Box::new(ast::Exp::TypeCastExp(ast::TypeCastExp{
                    exp: l,
                    target_type: t.clone(),
                    t: Some(t.clone()),
                }));
            }
            // 处理右子表达式的类型转换
            if !same_type(t.clone(), bexp.r.get_type()) {
                let r = bexp.r.clone();
                bexp.r = Box::new(ast::Exp::TypeCastExp(ast::TypeCastExp{
                    exp: r,
                    target_type: t.clone(),
                    t: Some(t.clone()),
                }));
            }
            bexp.t = Some(t.clone());
        }
        ast::Exp::UExp(_) => (),
        ast::Exp::TripleExp(triple_exp) => {
            let t = type_align(triple_exp.true_branch.get_type(), triple_exp.false_branch.get_type());
            // 处理true_branch到t的类型转换
            if !same_type(t.clone(), triple_exp.true_branch.get_type()) {
                let true_branch = triple_exp.true_branch.clone();
                triple_exp.true_branch = Box::new(ast::Exp::TypeCastExp(ast::TypeCastExp{
                    exp: true_branch,
                    target_type: t.clone(),
                    t: Some(t.clone()),
                }));
            }
            // 处理false_branch到t的类型转换
            if !same_type(t.clone(), triple_exp.false_branch.get_type()) {
                let false_branch = triple_exp.false_branch.clone();
                triple_exp.false_branch = Box::new(ast::Exp::TypeCastExp(ast::TypeCastExp{
                    exp: false_branch,
                    target_type: t.clone(),
                    t: Some(t.clone()),
                }));
            }
            triple_exp.t = Some(t.clone());
        }
        ast::Exp::TypeCastExp(_) => (),
        ast::Exp::NumLtrExp(_) => (),
        ast::Exp::StrLtrExp(_) => (),
        ast::Exp::CharLtrExp(_) => (),
        ast::Exp::IdentExp(_) => (),
        ast::Exp::CallExp(call_exp) => {
            // 
            todo!()
        }
        ast::Exp::BlkExp(_) => (),
        ast::Exp::Sizeof(_) => (),
    }
}

/// # 功能描述
/// 判断类型l和类型r是不是相同的类型。如果相同，
fn same_type(l: r#type::Type, r: r#type::Type) -> bool {
    match (l, r) {
        (r#type::Type::VOID, r#type::Type::VOID) => true,
        (r#type::Type::I64(_), r#type::Type::I64(_)) => true,
        (r#type::Type::I32(_), r#type::Type::I32(_)) => true,
        (r#type::Type::I16(_), r#type::Type::I16(_)) => true,
        (r#type::Type::I8(_), r#type::Type::I8(_)) => true,
        _ => false
    }
}

/// # 功能描述
/// 类型对齐。该函数的作用范围是整型。在调用该函数时，需要确保函数两侧的结果是可以对齐的
fn type_align(l: r#type::Type, r: r#type::Type) -> r#type::Type {
    match (l, r) {
        // 如果两侧有任何一个为VOID，那么变量就对齐到VOID
        (r#type::Type::VOID, _) => r#type::Type::VOID,
        (_, r#type::Type::VOID) => r#type::Type::VOID,
        // l为I64
        (r#type::Type::I64(..), r#type::Type::I64(..)) => r#type::Type::create_i64(),
        (r#type::Type::I64(..), r#type::Type::I32(..)) => r#type::Type::create_i64(),
        (r#type::Type::I64(..), r#type::Type::I16(..)) => r#type::Type::create_i64(),
        (r#type::Type::I64(..), r#type::Type::I8(..)) => r#type::Type::create_i64(),
        // l为I32
        (r#type::Type::I32(..), r#type::Type::I64(..)) => r#type::Type::create_i64(),
        (r#type::Type::I32(..), r#type::Type::I32(..)) => r#type::Type::create_i32(),
        (r#type::Type::I32(..), r#type::Type::I16(..)) => r#type::Type::create_i32(),
        (r#type::Type::I32(..), r#type::Type::I8(..)) => r#type::Type::create_i32(),
        // l为I16
        (r#type::Type::I16(..), r#type::Type::I64(..)) => r#type::Type::create_i64(),
        (r#type::Type::I16(..), r#type::Type::I32(..)) => r#type::Type::create_i32(),
        (r#type::Type::I16(..), r#type::Type::I16(..)) => r#type::Type::create_i16(),
        (r#type::Type::I16(..), r#type::Type::I8(..)) => r#type::Type::create_i16(),
        // l为I8
        (r#type::Type::I8(..), r#type::Type::I64(..)) => r#type::Type::create_i64(),
        (r#type::Type::I8(..), r#type::Type::I32(..)) => r#type::Type::create_i32(),
        (r#type::Type::I8(..), r#type::Type::I16(..)) => r#type::Type::create_i16(),
        (r#type::Type::I8(..), r#type::Type::I8(..)) => r#type::Type::create_i8(),
        _ => panic!("unknown type")
    }
}

// 关于do_convert_if_necessary和add_type的关系
// 考虑指针运算的情况下：
// 对于do_convert_if_necessary：

// 对指针运算的处理
// 我相信在下标运算中，就应当在转译为*(base + offset * elem_size)
// 时进行特殊处理
// add_type不需要进行左子表达式和右子表达式的处理
// 需要对offset * elem_size进行add_type
// 需要对*(..)进行add_type
// 手动添加base + offset * elem_size的类型