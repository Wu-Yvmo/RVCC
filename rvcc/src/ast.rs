use std::{cell::RefCell, clone, collections::HashMap, rc::Rc};
extern crate serde;
extern crate serde_json;

use serde::Serialize;

use crate::r#type::{self, StorageAttr};

#[derive(Serialize)]
pub struct Program {
    pub vardefs: Vec<VarDefsStmt>,
    // 提供对全局变量的跟踪，这是变量的兜底，所有函数、类型的查找都会在这里实现
    pub vartrackers: Vec<Rc<RefCell<NameTracker>>>,
    /// 所有出现过的字符串
    pub strs: Vec<String>,
}

/// 和类型查询相关的逻辑
impl Program {
    pub fn exist_var_name(&self, name: String) -> bool {
        for vartracker in self.vartrackers.iter().rev() {
            if vartracker.borrow().has_varinfo(name.clone()) {
                return true;
            }
        }
        false
    }
    // 查找变量类型
    pub fn get_var_type(&self, name: String) -> r#type::Type {
        for vartracker in self.vartrackers.iter().rev() {
            if vartracker.borrow().has_varinfo(name.clone()) {
                return vartracker.borrow().get_varinfo(name).t;
            }
        }
        panic!("no varinfo: {}", name)
    }
    /// 判断是否存在名为name的类型
    pub fn exist_type_name(&self, name: String) -> bool {
        for vartracker in self.vartrackers.iter().rev() {
            if vartracker.borrow().has_type_name(name.clone()) {
                return true;
            }
        }
        false
    }
    // 获取名为name的类型，name所指的类型应当由typedef获取
    pub fn get_type_by_name(&self, name: String) -> r#type::Type {
        for vartracker in self.vartrackers.iter().rev() {
            if vartracker.borrow().has_type_name(name.clone()) {
                return vartracker.borrow().get_type_name(name);
            }
        }
        panic!("no typeinfo: {}", name)
    }
}

/// 名称跟踪器
#[derive(Serialize)]
pub struct NameTracker {
    pub varinfos: Vec<VarInfo>,
    pub names: HashMap<String, r#type::Type>
}

impl NameTracker {
    pub fn create() -> Self {
        Self {
            varinfos: vec![],
            names: HashMap::new()
        }
    }
    pub fn push_varinfo(&mut self, varinfo: VarInfo) {
        self.varinfos.push(varinfo);
    }
    pub fn get_varinfo(&self, name: String) -> VarInfo {
        self.varinfos.iter().find(|v| v.name == name).unwrap().clone()
    }
    pub fn has_varinfo(&self, name: String) -> bool {
        for varinfo in &self.varinfos {
            if varinfo.name == name {
                return true;
            }
        }
        return false;
    }
    pub fn push_type_name(&mut self, name: String, t: r#type::Type) {
        self.names.insert(name, t);
    }
    pub fn get_type_name(&self, name: String) -> r#type::Type {
        self.names.get(&name).unwrap().clone()
    }
    pub fn has_type_name(&self, name: String) -> bool {
        self.names.contains_key(&name)
    }
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct VarInfo {
    pub storage_attr: StorageAttr,
    pub t: r#type::Type,
    pub name: String,
    pub offset: usize,
}

impl VarInfo {
    /// 根据类型和名称创建一个没有偏移量信息的VarInfo
    pub fn create(storage_attr: StorageAttr, t: r#type::Type, n: String) -> Self {
        VarInfo { 
            storage_attr,
            t, 
            name: n, 
            offset: 0 
        }
    }
}

// 提问：如何将函数定义和常规的声明融合起来？
#[derive(Serialize)]
#[derive(Clone)]
pub struct VarDefsStmt {
    pub vardefs: Vec<VarDef>,
    // 函数体 当为Some时是函数定义 当为None时为变量定义/函数定义
    // 实际它应当是一个Block，但是我们选择放宽约束
    pub body: Option<Box<Stmt>>,
}

// 对vardef的定义是：不负责存储类型，只存储变量的名称和初始化表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct VarDef {
    pub name: String,
    pub init: Option<Exp>
}

/// 语句
#[derive(Serialize)]
#[derive(Clone)]
pub enum Stmt {
    Break,
    Continue,
    CodeTag(CodeTagStmt),
    GoTo(GoToStmt),
    VarDefs(Box<VarDefsStmt>),
    If(IfStmt),
    While(WhileStmt),
    For(ForStmt),
    Return(ReturnStmt),
    Blk(BlkStmt),
    Exp(ExpStmt)
}

/// label语句
#[derive(Serialize)]
#[derive(Clone)]
pub struct CodeTagStmt {
    pub tag_name: String,
}

/// goto语句
#[derive(Serialize)]
#[derive(Clone)]
pub struct GoToStmt {
    pub target_name: String,
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct IfStmt {
    pub cond: Exp,
    pub true_branch: Box<Stmt>,
    pub false_branch: Option<Box<Stmt>>,
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct ForStmt {
    /// 初始化语句 我有问题：这里应当如何提供变量声明？
    pub init: ForInit,
    /// 条件
    pub cond: Exp,
    /// 更新
    pub update: Box<Stmt>,
    /// 循环体
    pub body: Box<Stmt>,
    /// 应对可能存在的变量定义
    pub var_tracker: Rc<RefCell<NameTracker>>,
}

#[derive(Serialize)]
#[derive(Clone)]
pub enum ForInit {
    /// 变量声明
    VarDecl(VarDefsStmt),
    /// 表达式
    Exp(Exp),
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct WhileStmt {
    pub cond: Exp,
    pub body: Box<Stmt>,
}

// 考虑添加变量表
#[derive(Serialize)]
#[derive(Clone)]
pub struct BlkStmt {
    pub stmts: Vec<Stmt>,
    pub vartracker: Rc<RefCell<NameTracker>>,
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct ReturnStmt {
    pub exp: Option<Exp>
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct ExpStmt {
    pub exp: Exp,
}

/// 表达式
#[derive(Serialize)]
#[derive(Clone)]
pub enum Exp {
    BExp(BExp),
    UExp(UExp),
    TripleExp(TripleExp),
    TypeCastExp(TypeCastExp),
    NumLtrExp(NumLtrExp),
    StrLtrExp(StrLtrExp),
    CharLtrExp(CharLtrExp),
    IdentExp(IdentExp),
    CallExp(CallExp),
    BlkExp(BlkExp),
    // 问题：sizeof里面填什么？
    Sizeof(SizeofExp),
}

impl Exp {
    /// 获取表达式的类型
    pub fn get_type(&self) -> r#type::Type {
        match self {
            Exp::BExp(bexp) => bexp.t.as_ref().unwrap().clone(),
            Exp::UExp(uexp) => uexp.t.as_ref().unwrap().clone(),
            Exp::TripleExp(triple_exp) => triple_exp.t.as_ref().unwrap().clone(),
            Exp::TypeCastExp(type_cast_exp) => type_cast_exp.t.as_ref().unwrap().clone(),
            Exp::NumLtrExp(num_ltr_exp) => num_ltr_exp.t.as_ref().unwrap().clone(),
            Exp::StrLtrExp(str_ltr_exp) => str_ltr_exp.t.as_ref().unwrap().clone(),
            Exp::CharLtrExp(char_ltr_exp) => char_ltr_exp.t.as_ref().unwrap().clone(),
            Exp::IdentExp(ident_exp) => ident_exp.t.as_ref().unwrap().clone(),
            Exp::CallExp(call_exp) => call_exp.t.as_ref().unwrap().clone(),
            Exp::BlkExp(blk_exp) => blk_exp.t.as_ref().unwrap().clone(),
            Exp::Sizeof(sizeof_exp) => sizeof_exp.t.as_ref().unwrap().clone(),
        }
    }
    /// 设置表达式的类型
    pub fn set_type(&mut self, t: r#type::Type) {
        match self {
            Exp::BExp(bexp) => bexp.t = Some(t),
            Exp::UExp(uexp) => uexp.t = Some(t),
            Exp::TripleExp(triple_exp) => triple_exp.t = Some(t),
            Exp::TypeCastExp(type_cast_exp) => type_cast_exp.t = Some(t),
            Exp::NumLtrExp(num_ltr_exp) => num_ltr_exp.t = Some(t),
            Exp::StrLtrExp(str_ltr_exp) => str_ltr_exp.t = Some(t),
            Exp::CharLtrExp(char_ltr_exp) => char_ltr_exp.t = Some(t),
            Exp::IdentExp(ident_exp) => ident_exp.t = Some(t),
            Exp::CallExp(call_exp) => call_exp.t = Some(t),
            Exp::BlkExp(blk_exp) => blk_exp.t = Some(t),
            Exp::Sizeof(sizeof_exp) => sizeof_exp.t = Some(t),
        }
    }
}

/// 用于双目表达式的双目运算符
#[allow(non_camel_case_types)]
#[derive(Serialize)]
#[derive(Clone)]
pub enum BOp {
    L_SHIFT,
    R_SHIFT,
    ADD,
    SUB,
    MUL,
    DIV,
    REM,
    EQ,
    NE,
    LT,
    LE,
    GT,
    GE,
    ASN,
    L_SHIFT_ASN,
    R_SHIFT_ASN,
    ADD_ASN,
    SUB_ASN,
    MUL_ASN,
    DIV_ASN,
    REM_ASN,
    BITS_AND_ASN,
    BITS_OR_ASN,
    BITS_XOR_ASN,
    LOGIC_AND,
    LOGIC_OR,
    BITS_AND,
    BITS_OR,
    BITS_XOR,
    COMMA,
    ACS,
}

/// 双目表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct BExp {
    pub l: Box<Exp>,
    pub op: BOp,
    pub r: Box<Exp>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 单目运算符 用于前缀单目表达式
#[allow(non_camel_case_types)]
#[derive(Serialize)]
#[derive(Clone)]
pub enum UOp {
    BITS_REVERSE,
    /// 按位取反
    NEG,
    ADD,
    SUB,
    NOT,
    /// 求地址
    REF,
    /// 解引用
    DEREF,
}

/// 前缀单目表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct UExp {
    pub op: UOp,
    pub sub: Box<Exp>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 三目表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct TripleExp {
    pub cond: Box<Exp>,
    pub true_branch: Box<Exp>,
    pub false_branch: Box<Exp>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 类型转换表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct TypeCastExp {
    pub exp: Box<Exp>,
    pub target_type: r#type::Type,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 整型字面量表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct NumLtrExp {
    pub value: usize,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 字符串字面量表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct StrLtrExp {
    pub content: Vec<char>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 字符字面量表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct CharLtrExp {
    pub c: char,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 标识符表达式
#[derive(Serialize)]
#[derive(Clone)]
pub struct IdentExp {
    pub ident: String,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// 函数调用表达式
#[derive(Serialize)]
#[derive(Clone)]
/// # 功能描述
/// 
/// # 成员描述
/// callable：经由求值后得到函数的表达式
/// 
/// arguments：函数调用中出现的参数
pub struct CallExp {
    pub callable: Box<Exp>,
    pub arguments: Vec<Exp>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

/// # 描述
/// 代码块表达式
/// 
/// # 注意
/// 代码块表达式的类型被定义为最后一个Stmt的类型
/// 
/// 如果:
/// 
/// 1.该Stmt是表达式，则代码块表达式的类型被规定为这个表达式的类型
/// 
/// 2.否则代码块表达式的类型被规定为VOID
#[derive(Serialize)]
#[derive(Clone)]
pub struct BlkExp {
    pub blk: Box<BlkStmt>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

#[derive(Serialize)]
#[derive(Clone)]
pub struct SizeofExp {
    pub content: Box<SizeofContent>,
    /// 表达式的类型
    pub t: Option<r#type::Type>,
}

#[derive(Serialize)]
#[derive(Clone)]
// 其实在ast中就不是很有必要存储sizeof的内容了，真正有用的就是这个类型。
// 这是一个应当在编译期就被计算出来的整型。
pub struct SizeofContent {
    pub targ_t: r#type::Type,
    pub t: r#type::Type,
}

