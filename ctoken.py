from enum import Enum, auto

class CTokenType(Enum):
    KEY_IF = auto()
    KEY_ELSE = auto()
    KEY_FOR = auto()
    KEY_WHILE = auto()
    KEY_RETURN = auto()
    KEY_INT = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    # 赋值
    OP_ASN = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_ADD = auto()
    OP_SUB = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_BITS_AND = auto()
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

class CToken:
    def __init__(self, token_type: CTokenType, value: str):
        super().__init__()
        self.token_type = token_type
        self.value = value