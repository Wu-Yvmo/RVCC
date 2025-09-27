use rvcc::tokenize;
use rvcc::parse;
use serde::Serialize;

pub fn main() {
    println!("Hello, world!");
    // let tokens = tokenize::tokenize("int main() { return 0; }".to_string());
    let ast = parse::parse("int a;".to_string());
    println!("{}", serde_json::to_string_pretty(&ast).unwrap())
}
