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
    NUMBER = auto()
    STRING = auto()
    LETTER = auto()
    # 赋值
    OP_ASN = auto()
    OP_ADD_ASN = auto()
    OP_SUB_ASN = auto()
    OP_MUL_ASN = auto()
    OP_DIV_ASN = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_ADD = auto()
    OP_ADD_ADD = auto()
    OP_SUB = auto()
    OP_SUB_SUB = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_BITS_AND = auto()
    OP_R_ARROW = auto()
    # 括号
    PC_L_ROUND_BRACKET = auto()
    PC_R_ROUND_BRACKET = auto()
    PC_L_SQUARE_BRACKET = auto()
    PC_R_SQUARE_BRACKET = auto()
    PC_L_CURLY_BRACKET = auto()
    PC_R_CURLY_BRACKET = auto()
    # 分号
    PC_SEMICOLON = auto()
    # 逗号
    PC_COMMA = auto()
    # 冒号
    PC_COLON = auto()
    # 点号
    PC_POINT = auto()
    # 单行注释
    COMMENT_SINGLE_LINE = auto()
    # 多行注释
    COMMENT_MULTI_LINE = auto()

class CToken:
    def __init__(self, token_type: CTokenType, value: str):
        super().__init__()
        self.token_type = token_type
        self.value = value