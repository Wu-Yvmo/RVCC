use std::collections::HashMap;

use crate::token;
use crate::token::Token;
use crate::utils;
use crate::parse;

struct TokenizeContext{
    chars: Vec<char>,
    index: usize,
    keyword_type: HashMap<String, token::TokenType>
}

impl TokenizeContext {
    /// 构造tokenize所用到的上下文
    fn create(code: &str) -> Self {
        let ctx = Self{
            chars: code.chars().collect(),
            index: 0,
            keyword_type: HashMap::from([
                ("switch".to_string(), token::TokenType::KEY_SWITCH),
                ("case".to_string(), token::TokenType::KEY_CASE),
                ("default".to_string(), token::TokenType::KEY_DEFAULT),
                ("break".to_string(), token::TokenType::KEY_BREAK),
                ("continue".to_string(), token::TokenType::KEY_CONTINUE),
                ("goto".to_string(), token::TokenType::KEY_GOTO),
                ("static".to_string(), token::TokenType::KEY_STATIC),
                ("struct".to_string(), token::TokenType::KEY_STRUCT),
                ("union".to_string(), token::TokenType::KEY_UNION),
                ("enum".to_string(), token::TokenType::KEY_ENUM),
                ("typedef".to_string(), token::TokenType::KEY_TYPEDEF),
                ("sizeof".to_string(), token::TokenType::KEY_SIZEOF),
                ("if".to_string(), token::TokenType::KEY_IF),
                ("else".to_string(), token::TokenType::KEY_ELSE),
                ("for".to_string(), token::TokenType::KEY_FOR),
                ("while".to_string(), token::TokenType::KEY_WHILE),
                ("return".to_string(), token::TokenType::KEY_RETURN),
                ("_Bool".to_string(), token::TokenType::KEY__BOOL),
                ("long".to_string(), token::TokenType::KEY_LONG),
                ("int".to_string(), token::TokenType::KEY_INT),
                ("short".to_string(), token::TokenType::KEY_SHORT),
                ("char".to_string(), token::TokenType::KEY_CHAR),
                ("void".to_string(), token::TokenType::KEY_VOID),
            ])
        };
        ctx
    }
    /// 返回当前字符
    fn current(&self) -> char {
        self.chars[self.index]
    }
    /// 返回下一个字符
    fn next(&self) -> char {
        utils::make_sure(self.index + 1 < self.chars.len(), "out of range");
        self.chars[self.index+1]
    }
    /// 判断是否已经结束
    fn end(&self) -> bool {
        self.chars.len() == self.index
    }
    /// 无条件跳过1个字符
    fn jump_any(&mut self) {
        utils::make_sure(!self.end(), "out of range");
        self.index += 1;
    }
    /// 跳过指定的字符，当前字符不是给定字符时，报错
    fn jump(&mut self, to_jump: char) {
        utils::make_sure(!self.end(), "out of range");
        utils::make_sure(self.current() == to_jump, "unexpected character");
        self.jump_any();
    }
    /// 跳过前缀的空白字符
    fn jump_spaces(&mut self) {
        while !self.end() && self.current().is_whitespace() {
            self.jump_any();
        }
    }
}

pub fn tokenize(code: String) -> parse::ParseContext {
    let mut ctx = TokenizeContext::create(&code);
    let mut tokens: Vec<token::Token> = Vec::new();
    ctx.jump_spaces();
    while !ctx.end() {
        tokens.push(match ctx.current() {
            'a'..='z'|'A'..='Z'|'_' => tokenize_prefix_word(&mut ctx),
            '+' => tokenize_prefix_add(&mut ctx),
            '-' => tokenize_prefix_sub(&mut ctx),
            '*' => tokenize_prefix_mul(&mut ctx),
            '/' => tokenize_prefix_div(&mut ctx),
            '%' => tokenize_prefix_rem(&mut ctx),
            '(' => tokenize_prefix_bracket_l_round(&mut ctx),
            ')' => tokenize_prefix_bracket_r_round(&mut ctx),
            '{' => tokenize_prefix_bracket_l_curly(&mut ctx),
            '}' => tokenize_prefix_bracket_r_curly(&mut ctx),
            '[' => tokenize_prefix_bracket_l_square(&mut ctx),
            ']' => tokenize_prefix_bracket_r_square(&mut ctx),
            ':' => tokenize_prefix_colon(&mut ctx),
            ';' => tokenize_prefix_semicolon(&mut ctx),
            ',' => tokenize_prefix_comma(&mut ctx),
            '=' => tokenize_prefix_asn(&mut ctx),
            '0'..='9' => tokenize_prefix_digit(&mut ctx),
            '!' => tokenize_prefix_sigh(&mut ctx),
            '&' => tokenize_prefix_and(&mut ctx),
            '|' => tokenize_prefix_or(&mut ctx),
            '^' => tokenize_prefix_xor(&mut ctx),
            '<' => tokenize_prefix_lt(&mut ctx),
            '>' => tokenize_prefix_gt(&mut ctx),
            '?' => tokenize_prefix_question(&mut ctx),
            '"' => tokenize_prefix_double_quote(&mut ctx),
            _ => panic!("unexpected situation")
        });
        ctx.jump_spaces();
    }
    parse::ParseContext::create(tokens)
}

/// 处理剩余字符串前缀为[a-zA-Z_]的情况
/// 
/// 可能产生的token类型有：IDENTIFIER和所有关键字
fn tokenize_prefix_word(ctx: &mut TokenizeContext) -> token::Token {
    let is_leagal_word_content = |c: char| {
        c.is_alphanumeric() || c == '_'
    };
    let mut content: String = String::new();
    while !ctx.end() && is_leagal_word_content(ctx.current()) {
        content.push(ctx.current());
        ctx.jump_any();
    }
    // 构建token
    match ctx.keyword_type.get(&content) {
        Some(keyword_type) => token::Token::create(*keyword_type, content),
        None => token::Token::create(token::TokenType::IDENTIFIER, content),
    }
}

/// 处理剩余字符前缀为+的情况
/// 
/// 可能的token有：
/// * `+` => add
/// * `+=` => add_asn
/// * `++` => add_add
fn tokenize_prefix_add(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('+');
    if ctx.end() {
        return Token::create(token::TokenType::OP_ADD, "+".to_string());
    }
    if ctx.current() == '+' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_ADD_ADD, "++".to_string());
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_ADD_ASN, "+=".to_string());
    }
    Token::create(token::TokenType::OP_ADD, "+".to_string())
}

/// 处理剩余字符前缀为-的情况
/// 
/// 可能的token有：
/// * `-` => sub
/// * `-=` => sub_asn
/// * `--` => sub_sub
fn tokenize_prefix_sub(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('-');
    if ctx.end() {
        return Token::create(token::TokenType::OP_SUB, "-".to_string());
    }
    if ctx.current() == '-' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_SUB_SUB, "--".to_string());
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_SUB_ASN, "-=".to_string());
    }
    Token::create(token::TokenType::OP_SUB, "-".to_string())
}

/// 处理剩余字符前缀为*的情况
/// 
/// 可能的token有：
/// * `*` => mul
/// * `*=` => mul_asn
fn tokenize_prefix_mul(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('*');
    if ctx.end() {
        return Token::create(token::TokenType::OP_MUL, "*".to_string());
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_MUL_ASN, "*=".to_string());
    }
    Token::create(token::TokenType::OP_MUL, "*".to_string())
}

/// 处理剩余字符前缀为'/'的情况
/// 
/// 可能的token有：
/// * `/` => add
/// * `/=` => add_asn
/// * `/*..*/` => multi_line_commit
/// * `//..` => single_line_commit
fn tokenize_prefix_div(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('/');
    if ctx.end() {
        return Token::create(token::TokenType::OP_DIV, "/".to_string());
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_DIV_ASN, "/=".to_string());
    }
    if ctx.current() == '*' {
        ctx.jump_any();
        let mut content = "/*".to_string();
        while !ctx.end() {
            // 循环跳出
            if ctx.current() == '*' && ctx.next() == '/' {
                ctx.jump_any();
                ctx.jump_any();
                content.push_str("*/");
                break;
            }
            content.push(ctx.current());
            ctx.jump_any();
        }
        return Token::create(token::TokenType::COMMENT_MULTI_LINE, content)
    }
    if ctx.current() == '/' {
        ctx.jump_any();
        let mut content = "//".to_string();
        while !ctx.end() {
            if ctx.current() == '\n' {
                ctx.jump_any();
                break;
            }
            content.push(ctx.current());
            ctx.jump_any();
        }
        return Token::create(token::TokenType::COMMENT_SINGLE_LINE, content)
    }
    Token::create(token::TokenType::OP_DIV, "/".to_string())
}

/// 处理剩余字符前缀为%的情况
/// 
/// 可能的token有：
/// * `%` => add
/// * `%=` => add_asn
fn tokenize_prefix_rem(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('%');
    if ctx.end() {
        return Token::create(token::TokenType::OP_REM, '%'.to_string())
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_REM_ASN, "%=".to_string())
    }
    Token::create(token::TokenType::OP_REM, '%'.to_string())
}

/// 处理剩余字符前缀为'('的情况
/// 
/// 可能的token有：
/// * `(` => l_round_bracket
fn tokenize_prefix_bracket_l_round(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('(');
    Token::create(token::TokenType::PC_L_ROUND_BRACKET, '('.to_string())
}

/// 处理剩余字符前缀为')'的情况
/// 
/// 可能的token有：
/// * `)` => r_round_bracket
fn tokenize_prefix_bracket_r_round(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump(')');
    Token::create(token::TokenType::PC_R_ROUND_BRACKET, ')'.to_string())
}

/// 处理剩余字符前缀为'{'的情况
/// 
/// 可能的token有：
/// * `{` => l_curly_bracket
fn tokenize_prefix_bracket_l_curly(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('{');
    Token::create(token::TokenType::PC_L_CURLY_BRACKET, '{'.to_string())
}

/// 处理剩余字符前缀为'}'的情况
/// 
/// 可能的token有：
/// * `}` => r_curly_bracket
fn tokenize_prefix_bracket_r_curly(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('}');
    Token::create(token::TokenType::PC_R_CURLY_BRACKET, '}'.to_string())
}

/// 处理剩余字符前缀为'['的情况
/// 
/// 可能的token有：
/// * `[` => l_square_bracket
fn tokenize_prefix_bracket_l_square(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('[');
    Token::create(token::TokenType::PC_L_SQUARE_BRACKET, '['.to_string())
}

/// 处理剩余字符前缀为']'的情况
/// 
/// 可能的token有：
/// * `]` => r_square_bracket
fn tokenize_prefix_bracket_r_square(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump(']');
    Token::create(token::TokenType::PC_R_SQUARE_BRACKET, ']'.to_string())
}

/// 处理剩余字符前缀为':'的情况
/// 
/// 可能的token有：
/// * `:` => colon
fn tokenize_prefix_colon(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump(':');
    Token::create(token::TokenType::PC_COLON, ':'.to_string())
}

/// 处理剩余字符前缀为';'的情况
/// 
/// 可能的token有：
/// * `;` => semicolon
fn tokenize_prefix_semicolon(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump(';');
    Token::create(token::TokenType::PC_SEMICOLON, ';'.to_string())
}

/// 处理剩余字符前缀为','的情况
/// 
/// 可能的token有：
/// * `,` => comma
fn tokenize_prefix_comma(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump(',');
    Token::create(token::TokenType::PC_COMMA, ','.to_string())
}

/// 处理剩余字符前缀为'='的情况
/// 
/// 可能的token有：
/// * `=` => asn
/// * `==` => eq
fn tokenize_prefix_asn(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('=');
    if ctx.end() {
        return Token::create(token::TokenType::OP_ASN, '='.to_string())
    }
    if ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_ASN, "==".to_string())
    }
    Token::create(token::TokenType::OP_ASN, '='.to_string())
}

/// 处理剩余字符前缀为'0'..='9'的情况
/// 
/// 可能的token有：
/// * 数字 => digit
/// 
/// 注意：当前没有提供对浮点数的支持
fn tokenize_prefix_digit(ctx: &mut TokenizeContext) -> token::Token {
    let mut content = "".to_string();
    while !ctx.end() && ctx.current().is_numeric() {
        content.push(ctx.current());
        ctx.jump_any();
    }
    Token::create(token::TokenType::NUMBER, content)
}

/// 处理剩余字符为'!'的情况
/// 
/// 可能的token有：
/// * `!` => not
/// * '!=' => ne
fn tokenize_prefix_sigh(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('|');
    if ctx.end() || ctx.current() != '=' {
        return Token::create(token::TokenType::OP_NEG, '|'.to_string())
    }
    ctx.jump('=');
    Token::create(token::TokenType::OP_NE, "!=".to_string())
}

/// 处理剩余字符为'&'的情况
/// 
/// 可能的token有：
/// * `&` => and
/// * `&&` => and_and
/// * `&=` => and_asn
fn tokenize_prefix_and(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('&');
    if !ctx.end() && ctx.current() == '&' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_LOGIC_AND, "&&".to_string())
    }
    if !ctx.end() && ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_BITS_AND_ASN, "&=".to_string())
    }
    return Token::create(token::TokenType::OP_BITS_AND, '&'.to_string())
}

/// 处理剩余字符为'|'的情况
/// 
/// 可能的token有：
/// * `|` => or
/// * `||` => or_or
/// * `|=` => or_asn
fn tokenize_prefix_or(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('|');
    if !ctx.end() && ctx.current() == '|' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_LOGIC_OR, "||".to_string())
    }
    if !ctx.end() && ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_BITS_OR_ASN, "|=".to_string())
    }
    Token::create(token::TokenType::OP_BITS_OR, '|'.to_string())
}

/// 处理剩余字符为'^'的情况
/// 
/// 可能的token有：
/// * `^` => xor
/// * `^=` => xor_asn
fn tokenize_prefix_xor(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('^');
    if !ctx.end() && ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_BITS_XOR_ASN, "^=".to_string())
    }
    Token::create(token::TokenType::OP_BITS_XOR, '^'.to_string())
}

/// 处理剩余字符为'<'的情况
/// 
/// 可能的token有：
/// * `<` => lt
/// * `<=` => le
fn tokenize_prefix_lt(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('<');
    if !ctx.end() && ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_LE, "<=".to_string())
    }
    Token::create(token::TokenType::OP_LT, '<'.to_string())
}

/// 处理剩余字符为'>'的情况
/// 
/// 可能的token有：
/// * `>` => gt
/// * `>=` => ge
fn tokenize_prefix_gt(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('>');
    if !ctx.end() && ctx.current() == '=' {
        ctx.jump_any();
        return Token::create(token::TokenType::OP_GE, ">=".to_string())
    }
    Token::create(token::TokenType::OP_GT, '>'.to_string())
}

/// 处理剩余字符为'?'的情况
/// 
/// 可能的token有：
/// * `?` => question
fn tokenize_prefix_question(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('?');
    Token::create(token::TokenType::PC_QUESTION, '?'.to_string())
}

fn tokenize_prefix_double_quote(ctx: &mut TokenizeContext) -> token::Token {
    ctx.jump('"');
    let mut content = "".to_string();
    while !ctx.end() && ctx.current() != '"' {
        content.push(ctx.current());
        ctx.jump_any();
    }
    ctx.jump('"');
    Token::create(token::TokenType::STRING, content)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn work() {
        let code = String::from("int a+++=//\n/**/ \"\"");
        let tokens = tokenize(code);
    }
    #[test]
    fn show_work_directory() {
        // 显示当前工作目录
        let path = std::env::current_dir().unwrap();
        println!("{}", path.display());
    }
    fn test_all() {
        // 
    }
}