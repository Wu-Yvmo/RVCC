import codegen
import sys
import ctokenize
import parse

command_orders: dict[str, str] = {}

def init_command_orders():
    argv = sys.argv
    while len(argv) > 0:
        if argv[0] == '-o':
            command_orders['-o'] = argv[1]
            argv = argv[2:]
            continue
        if argv[0] == 'terminal':
            argv = argv[1:]
            command_orders['terminal'] = 'enable'
            continue
        command_orders['input'] = argv[0]
        argv = argv[1:]
    if command_orders.get('-o') is None:
        command_orders['-o'] = 'a.s'

def read_file(filename: str) -> str:
    with open(filename, 'r') as f:
        return f.read()

if __name__ == '__main__':
    # 解析命令行输入参数
    init_command_orders()
    if command_orders.get('terminal') is not None:
        print('terminal mode enabled')
        code = sys.argv[2]
        tokens = ctokenize.tokenize(code)
        cast = parse.parse(tokens)
        code = codegen.codegen(cast)
        print(code)
        exit()
    code = read_file(command_orders['input'])
    tokens = ctokenize.tokenize(code)
    cast = parse.parse(tokens)
    code = codegen.codegen(cast)
    with open(command_orders['-o'], 'w') as f:
        f.write(code)
    # print(code)
    # try:
    #     code = sys.argv[1]
    #     tokens = ctokenize.tokenize(code)
    #     cast = parse.parse(tokens)
    #     code = codegen.codegen(cast)
    #     print(code)
    # except Exception as e:
    #     print(e)
    #     print(sys.argv[1])
    # code = sys.argv[1]
    # tokens = ctokenize.tokenize(code)
    # cast = parse.parse(tokens)
    # code = codegen.codegen(cast)
    # print(code)