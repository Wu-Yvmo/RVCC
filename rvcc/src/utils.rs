/// 确保条件为真，否则panic
pub fn make_sure(to_make: bool, msg: &str) {
    if !to_make {
        panic!("{}", msg);
    }
}

pub fn eval_i(content: String) -> usize {
    todo!()
}

/// # 功能描述
/// 对原始字符串进行处理，将转义字符转为正确的值。
/// 

// \a	警报（响铃）	产生一声蜂鸣或系统提示音。	7
// \b	退格	将光标回退一个位置。	8
// \f	换页	将光标移动到下一页（用于打印机）。在终端上通常表现为清屏。	12
// \n	换行	将光标移动到下一行的开头。这是最常用的换行符。	10
// \r	回车	将光标移动到当前行的开头，不换到下一行。	13
// \t	水平制表符	将光标移动到下一个水平制表位（通常是8个字符的倍数）。	9
// \v	垂直制表符	将光标移动到下一个垂直制表位。	11
// \\	反斜杠	表示一个字面的反斜杠字符 \。	92
// \'	单引号	表示一个字面的单引号字符 '。用于字符常量中。	39
// \"	双引号	表示一个字面的双引号字符 "。用于字符串常量中。	34
// \?	问号	表示一个字面的问号字符 ?。主要用于避免三字符组（trigraphs）的误解析。	63
// \0	空字符（NULL）	表示字符串的结束标志。	0
pub fn eval_str(content: String) -> Vec<char> {
    let chars = content.chars().collect::<Vec<char>>();
    let mut cooked: Vec<char> = vec![];
    let mut index = 0;
    loop {
        if index >= chars.len() {
            break;
        }
        if chars[index] == '\\' {
            index += 1;
            match chars[index] {
                'a' => cooked.push(7 as char),
                'b' => cooked.push(8 as char),
                'f' => cooked.push(12 as char),
                'n' => cooked.push('\n'),
                'r' => cooked.push('\r'),
                't' => cooked.push('\t'),
                'v' => cooked.push(11 as char),
                '\\' => cooked.push('\\'),
                '\'' => cooked.push('\''),
                '\"' => cooked.push('\"'),
                '?' => cooked.push('?'),
                '0' => cooked.push('\0'),
                _ => cooked.push(chars[index]),
            };
            index += 1;
            continue;
        }
        cooked.push(chars[index]);
        index += 1;
    }
    cooked
}