from typing import * # type: ignore
import ctoken
import re
import sys

patterns = [(r'^return', ctoken.CTokenType.KEY_RETURN),
            (r'^int*', ctoken.CTokenType.KEY_INT),
            (r'^[a-zA-Z_]+[0-9]*', ctoken.CTokenType.IDENTIFIER),
            (r'^[0-9]+', ctoken.CTokenType.NUMBER),
            (r'^==', ctoken.CTokenType.OP_EQ),
            (r'^!=', ctoken.CTokenType.OP_NE),
            (r'^<=', ctoken.CTokenType.OP_LE),
            (r'^<', ctoken.CTokenType.OP_LT),
            (r'^>=', ctoken.CTokenType.OP_GE),
            (r'^>', ctoken.CTokenType.OP_GT),
            (r'^=', ctoken.CTokenType.OP_ASN),
            (r'^\*', ctoken.CTokenType.OP_MUL),
            (r'^\/', ctoken.CTokenType.OP_DIV),
            (r'^\+', ctoken.CTokenType.OP_ADD),
            (r'^\-', ctoken.CTokenType.OP_SUB),
            (r'^\(', ctoken.CTokenType.PC_L_ROUND_BRACKET),
            (r'^\)', ctoken.CTokenType.PC_R_ROUND_BRACKET),
            (r'^\[', ctoken.CTokenType.PC_L_SQUARE_BRACKET),
            (r'^\]', ctoken.CTokenType.PC_R_SQUARE_BRACKET),
            (r'^\{', ctoken.CTokenType.PC_L_CURLY_BRACKET),
            (r'^\}', ctoken.CTokenType.PC_R_CURLY_BRACKET),
            (r'^;', ctoken.CTokenType.PC_SEMICOLON),
            (r'^,', ctoken.CTokenType.PC_COMMA),
            (r'^:', ctoken.CTokenType.PC_COLON),
]

def ltrim(code: str) -> str:
    while len(code) > 0 and code[0] == ' ':
        code = code[1:]
    return code

# def tokenize(code: str) -> list[ctoken.CToken]:
#     tokens: list[ctoken.CToken] = []
#     code = ltrim(code)
#     while len(code) > 0:
#         for pattern in patterns:
#             result = re.search(pattern[0], code)
#             if result:
#                 tokens.append(ctoken.CToken(pattern[1], result.group(0)))
#                 code = code[len(result.group(0)):]
#                 code = ltrim(code)
#                 break
#     return tokens

def tokenize(code: str) -> list[ctoken.CToken]:
    tokens: list[ctoken.CToken] = []
    code = ltrim(code)
    while len(code) > 0:
        # 候选，一次轮训扫描会产生多个候选token
        candidates: list[ctoken.CToken] = []
        for pattern in patterns:
            result = re.search(pattern[0], code)
            if result:
                candidates.append(ctoken.CToken(pattern[1], result.group(0)))
        # 取最长的候选
        candidates.sort(key=lambda x: len(x.value), reverse=True)
        if len(candidates) == 0:
            raise Exception('')
        tokens.append(candidates[0])
        code = code[len(candidates[0].value):]
        code = ltrim(code)
    return tokens

if __name__ == '__main__':
    code = sys.argv[1]
    print(code)
    tokens = tokenize(code)
    for token in tokens:
        print(token.value, token.token_type)