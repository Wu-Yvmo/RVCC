from typing import * # type: ignore
import ctoken
import re
import sys

patterns = [(r'^static', ctoken.CTokenType.KEY_STATIC),
            (r'^typedef', ctoken.CTokenType.KEY_TYPEDEF),
            (r'^struct', ctoken.CTokenType.KEY_STRUCT),
            (r'^union', ctoken.CTokenType.KEY_UNION),
            (r'^enum', ctoken.CTokenType.KEY_ENUM),
            (r'^sizeof', ctoken.CTokenType.KEY_SIZEOF),
            (r'^if', ctoken.CTokenType.KEY_IF),
            (r'^else', ctoken.CTokenType.KEY_ELSE),
            (r'^for', ctoken.CTokenType.KEY_FOR),
            (r'^while', ctoken.CTokenType.KEY_WHILE),
            (r'^return', ctoken.CTokenType.KEY_RETURN),
            (r'^_Bool', ctoken.CTokenType.KEY__BOOL),
            (r'^long', ctoken.CTokenType.KEY_LONG),
            (r'^int', ctoken.CTokenType.KEY_INT),
            (r'^short', ctoken.CTokenType.KEY_SHORT),
            (r'^char', ctoken.CTokenType.KEY_CHAR),
            (r'^void', ctoken.CTokenType.KEY_VOID),
            (r'^[a-zA-Z_]+[a-zA-Z_0-9]*', ctoken.CTokenType.IDENTIFIER),
            # 10进制整型
            (r'^[1-9][0-9]*', ctoken.CTokenType.NUMBER),
            # 8进制整型
            (r'^0[0-9]*', ctoken.CTokenType.NUMBER),
            # 16进制整型
            (r'^(0(x|X))[0-9a-fA-F]+', ctoken.CTokenType.NUMBER),
            # 2进制整型
            (r'^(0(b|B))[01]+', ctoken.CTokenType.NUMBER),
            # (r'^"((\\\\)|(\\\")|([^\"\\s]))*"', ctoken.CTokenType.STRING), 不用
            (r'^==', ctoken.CTokenType.OP_EQ),
            (r'^!=', ctoken.CTokenType.OP_NE),
            (r'^<=', ctoken.CTokenType.OP_LE),
            (r'^<', ctoken.CTokenType.OP_LT),
            (r'^>=', ctoken.CTokenType.OP_GE),
            (r'^>', ctoken.CTokenType.OP_GT),
            (r'^=', ctoken.CTokenType.OP_ASN),
            (r'^\+=', ctoken.CTokenType.OP_ADD_ASN),
            (r'^\-=', ctoken.CTokenType.OP_SUB_ASN),
            (r'^\*=', ctoken.CTokenType.OP_MUL_ASN),
            (r'^/=', ctoken.CTokenType.OP_DIV_ASN),
            (r'^->', ctoken.CTokenType.OP_R_ARROW),
            (r'^\*', ctoken.CTokenType.OP_MUL),
            (r'^\/', ctoken.CTokenType.OP_DIV),
            (r'^\+', ctoken.CTokenType.OP_ADD),
            (r'^\+\+', ctoken.CTokenType.OP_ADD_ADD),
            (r'^\-', ctoken.CTokenType.OP_SUB),
            (r'^\-\-', ctoken.CTokenType.OP_SUB_SUB),
            (r'^\&', ctoken.CTokenType.OP_BITS_AND),
            (r'^\!', ctoken.CTokenType.OP_NEG),
            (r'^\~', ctoken.CTokenType.OP_BITS_REVERSE),
            (r'^\(', ctoken.CTokenType.PC_L_ROUND_BRACKET),
            (r'^\)', ctoken.CTokenType.PC_R_ROUND_BRACKET),
            (r'^\[', ctoken.CTokenType.PC_L_SQUARE_BRACKET),
            (r'^\]', ctoken.CTokenType.PC_R_SQUARE_BRACKET),
            (r'^\{', ctoken.CTokenType.PC_L_CURLY_BRACKET),
            (r'^\}', ctoken.CTokenType.PC_R_CURLY_BRACKET),
            (r'^;', ctoken.CTokenType.PC_SEMICOLON),
            (r'^,', ctoken.CTokenType.PC_COMMA),
            (r'^:', ctoken.CTokenType.PC_COLON),
            (r'^\.', ctoken.CTokenType.PC_POINT),
            (r'^//.*', ctoken.CTokenType.COMMENT_SINGLE_LINE),
            (r'^/\*[\s\S]*\*/', ctoken.CTokenType.COMMENT_MULTI_LINE),
]

def ltrim(code: str) -> str:
    while len(code) > 0 and code[0].isspace():
        code = code[1:]
    return code

def tokenize(code: str) -> list[ctoken.CToken]:
    tokens: list[ctoken.CToken] = []
    code = ltrim(code)
    while len(code) > 0:
        # 当前为"时选择手动tokenized # 这是一个非常糟糕的决定，真的很糟糕
        if code[0] == '"':
            tk, code = tokenize_string(code)
            tokens.append(tk)
            continue
        if code[0] == '\'':
            tk, code = tokenize_letter(code)
            tokens.append(tk)
            continue
        # 候选，一次轮训扫描会产生多个候选token
        candidates: list[ctoken.CToken] = []
        for pattern in patterns:
            result = re.search(pattern[0], code)
            if result:
                candidates.append(ctoken.CToken(pattern[1], result.group(0)))
        # 取最长的候选
        candidates.sort(key=lambda x: len(x.value), reverse=True)
        if len(candidates) == 0:
            raise Exception(f'no match, {code}')
        tokens.append(candidates[0])
        code = code[len(candidates[0].value):]
        code = ltrim(code)
    return tokens

def tokenize_string(code: str) -> tuple[ctoken.CToken, str]:
    content = '"'
    code = code[1:]
    # tokenize主逻辑 可以额外处理\"作为内容的情况
    while code[0] != '"':
        if code[0] == '\\':
            content += code[0]
            content += code[1]
            code = code[2:]
            continue
        content += code[0]
        code = code[1:]
    content += '"'
    code = code[1:]
    code = ltrim(code)
    string_tk = ctoken.CToken(ctoken.CTokenType.STRING, content)
    return string_tk, code

def tokenize_letter(code: str) -> tuple[ctoken.CToken, str]:
    content = '\''
    # 跳过左侧的'
    code = code[1:]
    # 读取所有的逻辑
    while code[0] != '\'':
        if code[0] == '\\':
            content += code[0]
            content += code[1]
            code = code[2:]
            continue
        content += code[0]
        code = code[1:]
    content += '\''
    # 跳过右侧的'
    code = code[1:]
    code = ltrim(code)
    letter_tk = ctoken.CToken(ctoken.CTokenType.LETTER, content)
    return letter_tk, code

if __name__ == '__main__':
    code = sys.argv[1]
    print(code)
    tokens = tokenize(code)
    for token in tokens:
        print(token.value, token.token_type)