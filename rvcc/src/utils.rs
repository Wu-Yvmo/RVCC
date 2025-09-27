/// 确保条件为真，否则panic
pub fn make_sure(to_make: bool, msg: &str) {
    if !to_make {
        panic!("{}", msg);
    }
}

pub fn eval_i(content: String) -> usize {
    todo!()
}