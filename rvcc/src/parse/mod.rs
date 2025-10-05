use std::cell::RefCell;
use std::collections::HashMap;
use std::collections::LinkedList;
use std::rc::Rc;
use std::vec;

use crate::ast;
use crate::ast::BlkStmt;
use crate::ast::Program;
use crate::ast::VarDef;
use crate::ast::VarDefsStmt;
use crate::ast::VarInfo;
use crate::ast::NameTracker;
use crate::token;
use crate::r#type;
use crate::r#type::I32;
use crate::r#type::I8;
use crate::utils;
use crate::tokenize;

mod stmt;
mod exp;

use stmt::*;
use exp::*;

pub struct ParseContext {
    pub tokens: Vec<token::Token>,
    index: usize,
    pub storage_attr: r#type::StorageAttr,
}

impl ParseContext {
    /// 构造函数
    pub fn create(tokens: Vec<token::Token>) -> Self {
        Self { 
            tokens, 
            index: 0,
            storage_attr: r#type::StorageAttr::Global
        }
    }
    /// 获取当前token
    pub fn current(&self) -> token::Token {
        utils::make_sure(self.index < self.tokens.len(), "token index out of range");
        self.tokens[self.index].clone()
    }
    pub fn next(&self) -> token::Token {
        utils::make_sure(self.index + 1 < self.tokens.len(), "token index out of range");
        self.tokens[self.index + 1].clone()
    }
    /// 跳过一个token
    pub fn jump(&mut self) {
        utils::make_sure(self.index < self.tokens.len(), "token index out of range");
        self.index += 1;
    }
    /// 判断是否已经结束
    pub fn end(&self) -> bool {
        self.index >= self.tokens.len()
    }
}

// 要抽象出来一个名为Program的结构体
// 目前我们的编译器只支持单文件
pub fn parse(code: String) -> ast::Program {
    // 词法分析
    let mut ctx = tokenize::tokenize(code);
    // 解析程序
    parse_program(&mut ctx)
}

// 将解析完的程序返回
pub fn parse_program(ctx: &mut ParseContext) -> ast::Program {
    // 解析程序项
    let mut program = ast::Program {
        vardefs: Vec::new(),
        vartrackers: vec![Rc::new(RefCell::new(NameTracker::create()))],
        strs: Vec::new(),
    };
    while !ctx.end() {
        let to_insert = parse_program_item(ctx, &mut program);
        program.vardefs.push(to_insert);
    }
    program
}

// 我们现在面临的问题是 如何跟踪已经存在的变量？
pub fn parse_program_item(ctx: &mut ParseContext, program: &mut Program) -> ast::VarDefsStmt {
    utils::make_sure(is_type_prefix(ctx, program), "must be type prefix");
    parse_vardefs_stmt(ctx, program)
}

// 我现在的问题是，到底是把信息存储在program中，还是存储在ctx中？
// 我认为应当存储在Program中

/// 判断是否为类型开头
/// 该函数的完善度很低。
pub fn is_type_prefix(ctx: &mut ParseContext, program: &Program) -> bool {
    ctx.current().token_type == token::TokenType::KEY_INT
}

/// 解析基础类型。
/// 完善程度很低。
pub fn parse_base_type(ctx: &mut ParseContext, program: &Program) -> r#type::Type {
    ctx.storage_attr = r#type::StorageAttr::Local;
    ctx.jump();
    let t = r#type::Type::I32(I32{});
    t
}

/// # 功能描述
/// 解析vardefsStmt stmt
/// 该函数被调用时，可能的解析对象是：
/// 1.变量定义 
/// 2.函数声明 
/// 3.函数定义
pub fn parse_vardefs_stmt(ctx: &mut ParseContext, program: &mut Program) -> VarDefsStmt {
    let base_type = parse_base_type(ctx, program);
    let mut vardefs: Vec<ast::VarDef> = vec![];
    // 现在要解决的是：符号信息放在哪里？
    // 放在Program中.
    // 符号注册在这里依然存在问题，没把函数本身注册进去
    while !ctx.end() && ctx.current().token_type != token::TokenType::PC_SEMICOLON {
        // 跳过可能存在的前缀
        if ctx.current().token_type == token::TokenType::PC_COMMA {
            ctx.jump();
        }
        let vardescribe = parse_vardescribe(ctx, program, base_type.clone());
        // 函数声明且后续token是'{'，说明接下来是一个函数定义.
        // 解析函数定义
        if vardescribe.1.is_function() && ctx.current().token_type == token::TokenType::PC_L_CURLY_BRACKET {
            // 把当前函数注册到VarTracker中
            program.vartrackers
                .last()
                .unwrap()
                .borrow_mut()
                .push_varinfo(ast::VarInfo::create(
                    ctx.storage_attr.clone(), 
                    vardescribe.1.clone(), 
                    vardescribe.0.clone()));
            // 1.基于Type创建TypeTracker
            let vartracker = Rc::new(RefCell::new(create_vartracker_from_function_type(vardescribe.1.as_function())));
            // 2.把保存有函数局部参数的VarTracker添加到program.vartrackers
            program.vartrackers.push(vartracker);
            // 3.解析函数体
            let body = parse_blk_stmt(ctx, program);
            // 4.创建函数定义
            let vardef = VarDef{
                name: vardescribe.0,
                init: None
            };
            let vardefs_stmt = ast::VarDefsStmt {
                vardefs: vec![vardef],
                body: Some(Box::new(body)),
            };
            // 弹出当前函数的VarTracker
            program.vartrackers.pop();
            // 返回函数定义
            return vardefs_stmt;
        }
        // 常规变量定义
        // 尝试解析变量的初始化表达式，如果存在则解析，否则设为None
        let init = match ctx.current().token_type {
            token::TokenType::OP_ASN => {
                ctx.jump();
                Some(parse_exp(ctx, program))
            }
            _ => None
        };
        let vardef = ast::VarDef {
            name: vardescribe.0.clone(),
            init,
        };
        vardefs.push(vardef);
        program.vartrackers
            .last_mut()
            .unwrap()
            .borrow_mut()
            .push_varinfo(ast::VarInfo::create(
                ctx.storage_attr.clone(), 
                vardescribe.1.clone(), 
                vardescribe.0.clone()));
    }
    // 跳过末尾的';'
    ctx.jump();
    VarDefsStmt {
        vardefs,
        body: None,
    }
}

/// 基于function type构造vartracker.
pub fn create_vartracker_from_function_type(f: r#type::Function) -> NameTracker {
    let mut varinfos: Vec<VarInfo> = vec![];
    for param in f.params {
        varinfos.push(VarInfo::create(r#type::StorageAttr::Local, param.1.as_ref().clone(), param.0));
    }
    NameTracker{ 
        varinfos,
        names: HashMap::new(),
    }
}

/// 这是一个临时的修饰符表达。用于记录发生在函数解析中遇到的操作。
enum VarDescribeDecorator {
    CONST,
    // *
    STAR,
    // 数组尺寸
    INDEX(usize),
    // 参数名 参数类型
    CALL(Vec<(String, r#type::Type)>),
}

// 问题：如何解决函数定义中的参数解析？
// 在解析函数定义时，需要把函数给的参数天假到符号表中
// 我们并不需要var_describe.我们直接把类型解析完毕。
// vardescribe并不决定是否天假形式参数到符号表中，在vardef的解析中确定。
pub fn parse_vardescribe(ctx: &mut ParseContext, program: &mut Program, mut base_type: r#type::Type) -> (String, r#type::Type) {
    let mut decorates: LinkedList<VarDescribeDecorator> = std::collections::LinkedList::new();
    let mut star_ctr = 0;
    while !ctx.end() && ctx.current().token_type == token::TokenType::OP_MUL {
        star_ctr += 1;
        ctx.jump();
    }
    // 解析变量名
    let name = if ctx.current().token_type == token::TokenType::IDENTIFIER {
        let n = ctx.current().content.clone();
        ctx.jump();
        n
    } else {
        "".to_string()
    };
    // 解析后缀
    while !ctx.end() {
        if ctx.current().token_type == token::TokenType::PC_L_SQUARE_BRACKET {
            decorates.push_front({
                ctx.jump();
                let idx = VarDescribeDecorator::INDEX(utils::eval_i(ctx.current().content.clone()));
                ctx.jump();
                idx
            });
            continue;
        }
        if ctx.current().token_type == token::TokenType::PC_L_ROUND_BRACKET {
            decorates.push_front(VarDescribeDecorator::CALL({
                // 跳过'('
                ctx.jump();
                // 解析函数参数
                let mut params: Vec<(String, r#type::Type)> = Vec::new();
                // 备份旧的storage_attr
                let old_storage_attr = ctx.storage_attr.clone();
                // 将storage_attr设置为local
                ctx.storage_attr = r#type::StorageAttr::Local;
                while !ctx.end() && ctx.current().token_type != token::TokenType::PC_R_ROUND_BRACKET {
                    if ctx.current().token_type == token::TokenType::PC_COMMA {
                        ctx.jump();
                    }
                    let bt = parse_base_type(ctx, program);
                    params.push(parse_vardescribe(ctx, program, bt));
                }
                // 恢复旧的storage_attr
                ctx.storage_attr = old_storage_attr;
                // 跳过')'
                ctx.jump();
                params
            }));
            continue;
        }
        break
    }
    // 将前置的star插入到decorates的队头
    for _ in 0..star_ctr {
        decorates.push_front(VarDescribeDecorator::STAR);
    }
    // 解析完成，按序构造类型
    for decorate in decorates {
        match decorate {
            // 常量
            VarDescribeDecorator::CONST => {
                todo!("haven't implemented const");
            }
            // 指针
            VarDescribeDecorator::STAR => {
                base_type = r#type::Type::Pointer(r#type::Pointer{
                    element_type: Box::new(base_type),
                });
            }
            // 数组
            VarDescribeDecorator::INDEX(idx) => {
                base_type = r#type::Type::Array(r#type::Array{
                    element_type: Box::new(base_type),
                    index: idx,
                });
            }
            // 函数
            VarDescribeDecorator::CALL(params) => {
                base_type = r#type::Type::Function(r#type::Function{
                    params: params.into_iter().map(|(name, ty)| (name, Box::new(ty))).collect(),
                    return_type: Box::new(base_type),
                });
            }
        }
    }
    (name, base_type)
}

// 非常原始的原型 仅供测试
pub fn parse_blk_stmt(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    ctx.jump();
    ctx.jump();
    return ast::Stmt::Blk(ast::BlkStmt{
        stmts: vec![],
        vartracker: Rc::new(RefCell::new(NameTracker::create()))
    })
}

pub fn parse_exp_stmt(ctx: &mut ParseContext, program: &mut Program) -> ast::Stmt {
    todo!()
}

pub fn parse_exp(ctx: &mut ParseContext, program: &mut Program) -> ast::Exp {
    todo!()
}