use serde::Serialize;

extern crate serde;
extern crate serde_json;

#[derive(Clone)]
#[derive(Serialize)]
pub enum Type {
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
    pub fn to_string(&self) -> String {
        todo!()
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
    pub storage_attr: StorageAttr,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I16 {
    pub storage_attr: StorageAttr,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I32 {
    pub storage_attr: StorageAttr,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct I64 {
    pub storage_attr: StorageAttr,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Array {
    pub storage_attr: StorageAttr,
    pub index: usize,
    pub element_type: Box<Type>,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Function {
    pub storage_attr: StorageAttr,
    pub params: Vec<(String, Box<Type>)>,
    pub return_type: Box<Type>,
}

#[derive(Clone)]
#[derive(Serialize)]
pub struct Pointer {
    pub storage_attr: StorageAttr,
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