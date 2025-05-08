import codegen
import sys
import ctokenize
import parse

if __name__ == '__main__':
    code = sys.argv[1]
    tokens = ctokenize.tokenize(code)
    cast = parse.parse(tokens)
    code = codegen.codegen(cast)
    print(code)
    # try:
    #     code = sys.argv[1]
    #     tokens = ctokenize.tokenize(code)
    #     cast = parse.parse(tokens)
    #     code = codegen.codegen(cast)
    #     print(code)
    # except Exception as e:
    #     print(e)
    #     print(sys.argv[1])