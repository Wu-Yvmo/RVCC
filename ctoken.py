from enum import Enum, auto

class CTokenType(Enum):
    KEY_STATIC = auto()
    KEY_STRUCT = auto()
    KEY_UNION = auto()
    KEY_ENUM = auto()
    KEY_TYPEDEF = auto()
    KEY_SIZEOF = auto()
    KEY_IF = auto()
    KEY_ELSE = auto()
    KEY_FOR = auto()
    KEY_WHILE = auto()
    KEY_RETURN = auto()
    KEY__BOOL = auto()
    KEY_LONG = auto()
    KEY_INT = auto()
    KEY_SHORT = auto()
    KEY_CHAR = auto()
    KEY_VOID = auto()
    IDENTIFIER = auto()
    # 数字（目前暂时只是整型）
    NUMBER = auto()
    # 字符串
    STRING = auto()
    # 单个字母
    LETTER = auto()
    # '=' 赋值
    OP_ASN = auto()
    # '+=' 加赋值
    OP_ADD_ASN = auto()
    # '-=' 减赋值
    OP_SUB_ASN = auto()
    # '*=' 乘赋值
    OP_MUL_ASN = auto()
    # '/=' 除赋值
    OP_DIV_ASN = auto()
    # '==' 等于运算符
    OP_EQ = auto()
    # '!=' 不等于运算符
    OP_NE = auto()
    # '<' 小于运算符
    OP_LT = auto()
    # '<=' 小于等于运算符
    OP_LE = auto()
    # '>' 大于运算符
    OP_GT = auto()
    # '>=' 大于等于运算符
    OP_GE = auto()
    # '+' 加 运算符
    OP_ADD = auto()
    # '++' 自增运算符
    OP_ADD_ADD = auto()
    # '-' 减 运算符
    OP_SUB = auto()
    # '--' 自减运算符
    OP_SUB_SUB = auto()
    # '*' 乘 运算符
    OP_MUL = auto()
    # '/' 除 运算符
    OP_DIV = auto()
    # '&' 位与 运算符
    OP_BITS_AND = auto()
    # '->'
    OP_R_ARROW = auto()
    # '!' 逻辑非
    OP_NEG = auto()
    # '~' 按位求反
    OP_BITS_REVERSE = auto()
    # '(' 左圆括号
    PC_L_ROUND_BRACKET = auto()
    # ')' 右圆括号
    PC_R_ROUND_BRACKET = auto()
    # '[' 左方括号
    PC_L_SQUARE_BRACKET = auto()
    # ']' 右方括号
    PC_R_SQUARE_BRACKET = auto()
    # '{' 左花括号
    PC_L_CURLY_BRACKET = auto()
    # '}' 右花括号
    PC_R_CURLY_BRACKET = auto()
    # ';' 分号
    PC_SEMICOLON = auto()
    # ',' 逗号
    PC_COMMA = auto()
    # ':' 冒号
    PC_COLON = auto()
    # '.' 点号
    PC_POINT = auto()
    # '//...' 单行注释
    COMMENT_SINGLE_LINE = auto()
    # '/*...*/' 多行注释
    COMMENT_MULTI_LINE = auto()

class CToken:
    def __init__(self, token_type: CTokenType, value: str):
        super().__init__()
        self.token_type = token_type
        self.value = value