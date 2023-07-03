from sys import exit

DEBUG = False
EDEBUG = False

# format: (name, value)
variables = []
variables.append(["PATH", ""])

# format: (name, args, code, python code?)
functions = []


using_flow_l = False


def debug(*m):
    if DEBUG or EDEBUG:
        f = ""
        for t in m:
            f += str(t).strip() + " "
        print(f)

def edebug(*m):
    if EDEBUG:
        f = ""
        for t in m:
            f += str(t).strip() + " "
        print(f)

def rs(a):
    if type(a) == StringLiteral:
        return a.val
    return a

def sr(a):
    if type(a) == str:
        return StringLiteral(a)
    return a

def stripo(a):
    if type(a) == str:
        return a.strip()
    return a

    
def prepare(data):
    global variables
    global functions

    lines = []
    isadd = False
    for line in data.split("\n"):
        line = line.strip()
        if line == "" or line[0] == "-":
            continue
        
        if line[-1] == "+":
            if isadd:
                lines[-1] += line[:-1].strip()
            else:
                isadd = True
                lines.append(line[:-1].strip())
        elif line[0] == "+":
            lines[-1] += line[1:].strip()
        elif isadd:
            lines[-1] += line
            isadd = False
        else:
            lines.append(line)


    if isadd:
        print("line join operator found but not used")
        exit(-1)

    for line in lines:
        a = line.split("=")
        b = line.split("+=")
    
        if len(a) > 0:
            if len(b) > 0:
                if len(a[0]) > len(b[0]):
                    op = "+="
                else:
                    op = "="
            else:
                op = "="
        elif len(b) > 0:
            op = "+="
        else:
            print("no (valid) operator found in line with code ",line,"!")
            exit()
    
        left = line.split(op)[0].strip()
        right = op.join(line.split(op)[1:]).strip()
    
        if "(" in left:
            if op == "+=":
                print("operator '+=' can NOT be used on functions")
                exit()
            # function assignment
            if not ")" in left:
                print("unclosed '('!")
                exit()
    
            fname = left.split("(")[0]
            fargl = left.split("(")[1].split(")")[0].split(",")
            for farg in fargl:
                farg = farg.strip()

            found = False
            for func in functions:
                if func[0] == fname and len(func[1]) == len(fargl):
                    found = True
                    func[2] = right

            if not found:
                functions.append([fname, fargl, right])
            
        else:
            # variable assignment / concatination
            found = False
            for var in variables:
                if var[0] == left:
                    if op == "=":
                        var[1] = rs(parse(right))
                    elif op == "+=":
                        var[1] = var[1] + rs(parse(right))
                    found = True
                    break

            if not found:
                variables.append([left, parse(right)])


def is_literal(s):
    global variables
    global functions

    if type(s) != str:
        return True
    
    s = s.strip()


    # === LITERALS ===
    if len(s) == 0:
        return True

    if s[0] == "\"":
        if not s[-1] == "\"":
            print("unclosed string!")
            exit()
        return True
    if s[0] == "'":
        if not s[-1] == "\'":
                print("unclosed string!")
                exit()
        return True

    isnum = True
    isnum_amountPre = 0
    isnum_amountCom = 0
    for c in s:
        c = ord(c)
        if c > 47 and c < 58:
            continue
        if c == 46:
            isnum_amountCom += 1
            if isnum_amountCom > 1:
                print("too many . in number!")
                exit()
            else:
                continue
        if c == 43 or c == 45:
            isnum_amountPre += 1
            if isnum_amountPre > 1:
                isnum = False
            else:
                continue
        isnum = False

    if isnum:
        return True

    return False


class StringLiteral:
    val = ""
    def __init__(self, val):
        self.val = val


def parse(s):
    global variables
    global functions
    global using_flow_l

    if type(s) != str:
        return s
    
    if s == "":
        return ""

    if len(s) == 0:
            return ""

    debug("parsing",s)

    # === weird shit ===
    if s[0] == "(":
        if not s[-1] == ")":
            print("unclosed '('!")
            exit()
        return parse(s[1:-1])

    # === LITERALS ===
    if s.strip() == "true":
        return True

    if s.strip() == "false":
        return False
    
    if s[0] == "\"":
        if not s[-1] == "\"":
            print("unclosed string!")
            exit()
        return sr(s[1:-1])
    if s[0] == "'":
        if not s[-1] == "\'":
                print("unclosed string!")
                exit()
        return sr(s[1:-1])

    s = s.strip()

    # === boolean shit ===
    if s[0] == "!":
        return not parse(s[1:])

    isnum = True
    isnum_amountPre = 0
    isnum_amountCom = 0
    amountNum = 0
    for c in s:
        c = ord(c)
        if c > 47 and c < 58:
            amountNum += 1
            continue
        if c == 46:
            isnum_amountCom += 1
            if isnum_amountCom > 1:
                print("too many . in number!")
                exit()
            else:
                continue
        if c == 43 or c == 45:
            isnum_amountPre += 1
            if isnum_amountPre > 1:
                isnum = False
            else:
                continue
        isnum = False

    if amountNum == 0:
        isnum = False

    if isnum:
        return float(s)


    # === VARIABLES  ===
    for var in variables:
        if var[0] == s:
            return var[1]


    # === FUNCTIONS ===
    if s[-1] == ")":
        fin = 0
        parsing_fn = True
        fname = ""
        fargs = []
        parsing_str = False
        parsing_farg = False
        wasstring = False

        parsingv = ""
        for c in s:
            if c == '(':
                fin += 1
            if c == ')':
                fin -= 1

            edebug("character:",c,"fin:",fin)

            if c == "\"" and fin == 1:
                parsing_str = not parsing_str
                if not parsing_str:
                    wasstring = True
            elif c == '(' and fin == 1:
                parsing_fn = False
                parsing_farg = True
                fname = parsingv
                parsingv = ""
            elif c == ')' and fin == 0:
                fargs.append(parsingv.strip())
                parsing_farg = False
                parsingv = ""
                # done parsing

                if using_flow_l:
                    if fname == "do":
                        for arg in fargs:
                            parse(arg)
                        return 0

                    if fname == "after": # execute a after b (and returns b)
                        if len(fargs) != 2:
                            print("invalid arguments")
                            exit()
                        val = parse(fargs[1])
                        parse(fargs[0])
                        return val

                    if fname == "before": # execute a before b (and returns b)
                        if len(fargs) != 2:
                            print("invalid arguments")
                            exit()
                        parse(fargs[0])
                        return parse(fargs[1])

                    if fname == "if": # [boolean] [if true] [if false (optional)]
                        if len(fargs) < 2 or len(fargs) > 3:
                            print("invalid arguments")
                            exit()
                        c = rs(parse(fargs[0]))
                        debug("condition result:",c)
                        if c:
                            return parse(fargs[1])
                        elif len(fargs) == 3:
                            return parse(fargs[2])
                        else:
                            return False

                    if fname == "with": # [var name (string)]=[value], ops...   and returns result of last expression
                        if len(fargs) < 2:
                            print("invalid arguments")
                            exit()
                        a = fargs[0].split("=")
                        oldvars = variables
                        variables.append((a[0], parse(a[1].strip())))

                        for exp in fargs[1:]:
                            val = parse(exp.strip())
                        
                        variables = oldvars
                        return val
                    
                oldvars = variables

                ispycode = False
                found = False
                argn = []
                for func in functions:
                    if func[0] == fname:
                        found = True
                        if len(func) > 3:
                            ispycode = True
                            py_func_code = func[3]
                        else:
                            func_code = func[2]
                        
                        if len(func[1]) != len(fargs):
                            continue

                        argn = func[1]
                        for argi, arg in enumerate(func[1]):
                            variables.append([arg, fargs[argi]])

                if not found:
                    print("no function named ", fname, "!")
                    exit()

                if ispycode:
                    variables = oldvars
                    
                    debug("standart library function call: ", fname, " args (parsed): ")
                    evars = {}
                    if len(argn) > 0:
                        for argi, arg in enumerate(fargs):
                            evars[argn[argi]] = rs(parse(arg))
                            #if is_literal(arg):
                            #    evars[argn[argi]] = rs(arg)
                            #else:
                            #    evars[argn[argi]] = rs(parse(sr(arg)))
                    debug("- ", evars)
                    if py_func_code != "":
                        val = sr(eval(py_func_code, evars))
                        return val
                    else:
                        return 0
                else:
                    debug("function call: ", fname, " args: ", fargs)
                    val = parse(func_code)
                variables = oldvars

                return val
            elif c == ',' and parsing_farg and fin == 1 and not parsing_str:
                fargs.append(parsingv.strip())
                parsingv = ""
                wasstring = False
                parsing_farg = True
            else:
                parsingv += c

    # === MORE BOOLEAN SHIT ===
    
    if "==" in s:
        sp = s.split("==")
        return rs(parse(sp[0].strip())) == rs(parse(sp[1].strip()))
    if "!=" in s:
        sp = s.split("!=")
        return rs(parse(sp[0].strip())) != rs(parse(sp[1].strip()))
    if ">=" in s:
        sp = s.split(">=")
        return rs(parse(sp[0].strip())) >= rs(parse(sp[1].strip()))
    if "<=" in s:
        sp = s.split("<=")
        return rs(parse(sp[0].strip())) <= rs(parse(sp[1].strip()))
    if ">" in s:
        sp = s.split(">")
        return rs(parse(sp[0].strip())) > rs(parse(sp[1].strip()))
    if "<" in s:
        sp = s.split("<")
        return rs(parse(sp[0].strip())) < rs(parse(sp[1].strip()))
    if "||" in s:
        sp = s.split("||")
        return rs(parse(sp[0].strip())) or rs(parse(sp[1].strip()))
    if "&&" in s:
        sp = s.split("&&")
        return rs(parse(sp[0].strip())) and rs(parse(sp[1].strip()))

    return s
    

import os.path
from sys import argv

if len(argv) < 2 or len(argv) > 3:
    print("invalid arguments!")
    print("usage: [file] [init code = main(0)]")
    exit()

with open(argv[1]) as f:
    data = f.read()
    prepare(data)


# path stuff
pathv = variables[0][1]

stdlibs = [
    "types.l",      # convert types
    "math.l",       # math
    "str.l",        # strings
    "io.l",         # input and output shit
    "arr.l",        # arrays
    "flow.l",        # change the flow of the programm
]

for lib in pathv.split(";"):
    lib = lib.strip()
    if lib == "":
        continue

    debug("importing library ",lib)

    if lib == "flow.l":
        using_flow_l = True
    elif lib == "types.l":
        functions.append(["str", ["a"], "", "str(a)"])
        functions.append(["int", ["a"], "", "int(a)"])
        functions.append(["float", ["a"], "", "float(a)"])
        functions.append(["list", ["a"], "", "list(a)"])
    elif lib == "math.l":
        functions.append(["mul", ["a", "b"], "", "a * b"])
        functions.append(["add", ["a", "b"], "", "a + b"])
        functions.append(["sub", ["a", "b"], "", "a - b"])
        functions.append(["div", ["a", "b"], "", "a / b"])
        functions.append(["mod", ["a", "b"], "", "a % b"])
    elif lib == "str.l":
        functions.append(["concat", ["a", "b"], "", "a + b"])
        functions.append(["concat", ["a", "b", "c"], "", "a + b + c"])
        functions.append(["split", ["a", "b"], "", "a.split(b)"])
    elif lib == "io.l":
        functions.append(["input", [], "", "input()"])
        functions.append(["print", ["a"], "", "print(a)"])
    elif lib == "arr.l":
        functions.append(["join", ["arr", "c"], "", "c.join(arr)"])
        functions.append(["sort", ["arr"], "", "arr.sort()"])
        functions.append(["get", ["index", "arr"], "", "arr[index]"])
        functions.append(["sublist", ["from", "to", "arr"], "", "arr[from:to]"])
    else:
        if not os.path.exists(lib):
            print("Library",lib,"not found!")
            exit()
        with open(lib) as f:
            s = f.read()
            prepare(s)


if len(argv) == 3:
    print(rs(parse(argv[2])))
else:
    found = False
    for func in functions:
        if func[0] == "main":
            found = True

    if not found:
        print("no function called main!")
    else:
        print(rs(parse("main(0)")))
