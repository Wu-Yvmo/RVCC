use crate::{ast::{self, Program}, parse::{is_type_prefix, parse_vardefs_stmt, ParseContext}, token};

pub fn parse_stmt(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    match ctx.current().token_type {
        // break
        token::TokenType::KEY_BREAK => todo!(),
        // continue
        token::TokenType::KEY_CONTINUE => todo!(),
        // goto
        token::TokenType::KEY_GOTO => todo!(),
        // if
        token::TokenType::KEY_IF => todo!(),
        // while
        token::TokenType::KEY_WHILE => todo!(),
        // for
        token::TokenType::KEY_FOR => todo!(),
        // return
        token::TokenType::KEY_RETURN => todo!(),
        // Blk 代码块
        token::TokenType::PC_L_CURLY_BRACKET => todo!(),
        // vardefs
        _ if is_type_prefix(ctx, program) => ast::Stmt::VarDefs(Box::new(parse_vardefs_stmt(ctx, program))),
        // codetag
        token::TokenType::IDENTIFIER if ctx.next().token_type == token::TokenType::PC_COLON  => todo!(),
        // exp
        _ => todo!(),
    }
}

pub fn parse_stmt_break(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    ctx.jump();
    ast::Stmt::Break
}

pub fn parse_stmt_continue(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    ctx.jump();
    ast::Stmt::Continue
}

pub fn parse_stmt_goto(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    ctx.jump();
    let target_name = ctx.current().content.clone();
    ctx.jump();
    ast::Stmt::GoTo(ast::GoToStmt{
        target_name
    })
}

pub fn parse_stmt_if(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_while(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_for(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_return(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_blk(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_codetag(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_stmt_exp(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}