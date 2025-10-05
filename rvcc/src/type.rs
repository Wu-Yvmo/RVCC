use serde::Serialize;

extern crate serde;
extern crate serde_json;

#[derive(Clone)]
#[derive(Serialize)]
pub enum Type {
    VOID,
    I8(I8),
    I16(I16),
    I32(I32),
    I64(I64),
    Array(Array),
    Function(Function),
    Pointer(Pointer),
    Enum(Enum),
    Union(Union),
    Struct(Struct),
}

impl Type {
    pub fn is_function(&self) -> bool {
        match self {
            Type::Function(_) => true,
            _ => false,
        }
    }
    pub fn as_function(&self) -> Function {
        match self {
            Type::Function(f) => f.clone(),
            _ => panic!("not a function")
        }
    }
}

impl Type {
    pub fn create_void() -> Self {
        Type::VOID
    }
    pub fn create_i8() -> Self {
        Type::I8(I8{})
    }
    pub fn create_i16() -> Self {
        Type::I16(I16{})
    }
    pub fn create_i32() -> Self {
        Type::I32(I32{})
    }
    pub fn create_i64() -> Self {
        Type::I64(I64{})
    }
}

impl Type {
    pub fn create_ptr_of(element_type: Box<Type>) -> Self {
        Type::Pointer(Pointer{element_type})
    }
}

/// 存储属性
#[derive(Clone)]
#[derive(Serialize)]
pub enum StorageAttr {
    /// 全局变量
    Global,
    /// 局部变量
    Local,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I8 {
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I16 {
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I32 {
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I64 {
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Array {
    pub index: usize,
    pub element_type: Box<Type>,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Function {
    pub params: Vec<(String, Box<Type>)>,
    pub return_type: Box<Type>,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Pointer {
    pub element_type: Box<Type>,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Enum {}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Union {}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Struct {}