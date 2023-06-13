import os
import sys
import xml.etree.ElementTree as et
import re

INVALID_CMDLINE_ARGS = 10

PRINT_ALLOWED = False

class EmptyStackException(Exception):
    pass

class VarNotFoundException(Exception):
    pass

class Frame:
    def __init__(self, dict):
        try:
            self.dict = dict.copy()
        except AttributeError:
            exitProgram(55)
        self.next = None

class FrameStack:
    def __init__(self):
        self.head = None
        self.size = 0

    def isEmpty(self):
        return self.size == 0

    def push(self, dict):
        frame = Frame(dict)
        if self.isEmpty():
            self.head = frame
        else:
            frame.next = self.head
            self.head = frame
        self.size += 1

    def pop(self):
        if self.isEmpty():
            raise EmptyStackException
        self.head = self.head.next
        self.size -= 1

    def top(self):
        if self.isEmpty():
            raise EmptyStackException
        return self.head.dict
    
    def addToLF(self, name, type, value):
        if self.isEmpty():
            raise EmptyStackException
        self.head.dict[name] = {"type": type, "value": value}

    def findVar(self, name):
        if self.isEmpty():
            raise EmptyStackException
        if name in self.head.dict:
            return self.head.dict[name]
        else:
            raise VarNotFoundException


def exitProgram(exitCode):
    debugMessage("=========================== PROGRAM FINISHED ===========================")
    debugMessage(f"GLOBAL FRAME: {globalFrame}")
    try:
        debugMessage(f"LOCAL FRAME: {frameStack.top()}")
    except EmptyStackException:
        pass
    debugMessage(f"TEMPORARY FRAME: {temporaryFrame}")
    exit(exitCode)

def debugMessage(*args):
    if (PRINT_ALLOWED):
        print(*args)

def printHelp():
    print("Nice help bruh")


def isHelpArg(arg):
    return arg == "--help" or arg == "-h"


def isInterpretNameArg(arg, path):
    return arg == path or arg == "interpret.py"


def isInputFileArg(x):
    return x[0] == "--input" and x[1] is not None


def isSourceFileArg(x):
    return x[0] == "--source" and x[1] is not None


def splitArg(arg):
    try:
        x = arg.split('=')
    except ValueError:
        exitProgram(INVALID_CMDLINE_ARGS)
    return x


def parseArguments(args, path):
    if len(args) > 3:
        exitProgram(INVALID_CMDLINE_ARGS)
    else:
        debugMessage("Pocty v cajku")

    inputFile = None
    sourceFile = None

    for arg in args:
        if isHelpArg(arg):
            printHelp()
            exit(0)
        elif isInterpretNameArg(arg, path):
            continue

        x = splitArg(arg)

        if isInputFileArg(x):
            inputFile = x[1]
        elif isSourceFileArg(x):
            sourceFile = x[1]
        else:
            exitProgram(INVALID_CMDLINE_ARGS)

        if inputFile is None:
            inputFile = sys.stdin
        if sourceFile is None:
            sourceFile = sys.stdin

    return inputFile, sourceFile

def safePop(stack):
    try:
        tmp = stack.top()
        stack.pop()
        return tmp
    except EmptyStackException:
        exitProgram(55)

def addVarToFrame(frame, name, type, value):
    if frame == "GF":
        try:
            globalFrame[name] = {"type": type, "value": value}
        except TypeError:
            exitProgram(55)
    elif frame == "LF":
        try:
            frameStack.addToLF(name, type, value)
        except EmptyStackException:
            exitProgram(55)
    else:
        try:
            temporaryFrame[name] = {"type": type, "value": value}
        except TypeError:
            exitProgram(55)
    
def findVarInFrame(frameAndName):
    try:
        frame, name = frameAndName.split('@')
    except ValueError:
        exitProgram(53)
    if frame == "GF":
        try:
            if name in globalFrame:
                return globalFrame[name]
        except:
            debugMessage("var not in gf")
            exitProgram(55)
    if frame == "LF":
        try:
           return frameStack.findVar(name)
        except EmptyStackException:
            exitProgram(55)
        except VarNotFoundException:
            exitProgram(55)
    if frame == "TF":
        try:
            if name in temporaryFrame:
                return temporaryFrame[name]
        except:
            debugMessage("var not in tf")
            exitProgram(55)

def checkVar(arg):
    if arg != "var":
        debugMessage(f"type is {arg}")
        exitProgram(53)

def updateVar(var, type, value):
    try:
        var["type"] = type
        var["value"] = value
    except TypeError:
        exitProgram(53)

def isVar(type):
    return type == "var"

def isConstant(type):
    return (type in ["int", "bool", "string", "nil"]) 

def isSymbol(type):
    return isConstant(type) or isVar(type)

def isIntConstant(argType, value):
    if argType["type"] == "int":
        return True
    try:
        int(value)
    except ValueError:
        exitProgram(53)

def main():
    inputFile, source = parseArguments(sys.argv, os.path.realpath(__file__))

    try: 
        if source == sys.stdin:
            sourceXML = ""
            for line in sys.stdin:
                sourceXML = sourceXML + line
            XMLtree = et.parse(et.fromstring(sourceXML))
        else:
            XMLtree = et.parse(f"{source}")
    except Exception:
        exit(31)

    program = XMLtree.getroot()

    global globalFrame
    global localFrame
    global temporaryFrame
    global frameStack

    globalFrame = {}
    localFrame = None
    temporaryFrame = None
    frameStack = FrameStack()   
    instOrders = [0]
    instList = []
    dataStack = []
    if inputFile != sys.stdin:
        file = open(inputFile, 'r')
    # TODO: poradi instrukci
    for instruction in program:
        if instruction.tag != "instruction":
            exitProgram(32)
        instList.append(instruction)

    for i in range(len(instList)):
        instruction = instList[0]
        for inst in instList:
            try:
                if int(inst.attrib["order"]) < int(instruction.attrib["order"]):
                    instruction = inst
            except KeyError:
                exitProgram(32)
            except ValueError:
                exitProgram(32)
        instList.remove(instruction)
        if instruction.attrib["order"] in instOrders:
            exitProgram(32)

        try:
            if int(instruction.attrib["order"]) < 1:
                exitProgram(32)
        except Exception:
            exitProgram(32)
        instOrders.append(instruction.attrib["order"])
        argumentsNumber = [] # Poradi argumentu (jakozto nazev xml elementu, e.g. arg1 apod.)
        argumentsType = [] # Typ argumentu
        argumentsValues = [] # Hodnota argumentu

        for arg in instruction:
            if not re.match("^arg\d+$", arg.tag):
                exitProgram(32)
            argumentsNumber.append(arg.tag)
            argumentsType.append(arg.attrib)
            argumentsValues.append(arg.text)

        if len(argumentsNumber) > 1 and argumentsNumber[0] > argumentsNumber[1]:
            tmp = argumentsNumber[0]
            argumentsNumber[0] = argumentsNumber[1]
            argumentsNumber[1] = tmp
            tmp = argumentsType[0]
            argumentsType[0] = argumentsType[1]
            argumentsType[1] = tmp
            tmp = argumentsValues[0]
            argumentsValues[0] = argumentsValues[1]
            argumentsValues[1] = tmp
        elif len(argumentsNumber) > 2 and argumentsNumber[1] > argumentsNumber[2]:
            tmp = argumentsNumber[1]
            argumentsNumber[1] = argumentsNumber[2]
            argumentsNumber[2] = tmp
            tmp = argumentsType[0]
            argumentsType[1] = argumentsType[2]
            argumentsType[2] = tmp
            tmp = argumentsValues[0]
            argumentsValues[1] = argumentsValues[2]
            argumentsValues[2] = tmp

        try:
            debugMessage("INSTRUCTION:", instruction.attrib["opcode"])
            debugMessage("ARGUMENTS:", argumentsNumber, argumentsType, argumentsValues)
        except KeyError:
            exit(32)

        opcode = instruction.attrib["opcode"]
        match opcode.upper():
            case "MOVE":
                if len(argumentsType) != 2:
                    exitProgram(32)
                    
                checkVar(argumentsType[0]["type"])
                variable = findVarInFrame(argumentsValues[0])

                if not isSymbol(argumentsType[1]["type"]):
                    exitProgram(53)
                elif isConstant(argumentsType[1]["type"]): # konstanta do promenne
                    updateVar(variable, argumentsType[1]["type"], argumentsValues[1])
                else: # promenna do promenne
                    var2 = findVarInFrame(argumentsValues[1])
                    updateVar(variable, var2["type"], var2["value"])

            case "CREATEFRAME":
                if len(argumentsType) != 0:
                    exitProgram(32)
                temporaryFrame = {}

            case "PUSHFRAME":
                if len(argumentsType) != 0:
                    exitProgram(32)
                frameStack.push(temporaryFrame)
                localFrame = frameStack.top()
                temporaryFrame = None

            case "POPFRAME":
                if len(argumentsType) != 0:
                    exitProgram(32)
                temporaryFrame = safePop(frameStack)

            case "DEFVAR":
                if len(argumentsType) != 1:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                frame, name = argumentsValues[0].split('@')
                addVarToFrame(frame, name, None, None)

            case "CALL":
                if len(argumentsType) != 1:
                    exitProgram(32)

            case "RETURN":
                if len(argumentsType) != 0:
                    exitProgram(32)

            case "PUSHS":
                if len(argumentsType) != 1:
                    exitProgram(32)
                stackNode = {}
                if isConstant(argumentsType[0]["type"]):
                    stackNode["value"] = argumentsValues[0]
                    stackNode["type"] = argumentsType[0]["type"]
                elif isVar(argumentsType[0]["type"]):
                    var = findVarInFrame(argumentsValues[0])
                    stackNode["value"] = var["value"]
                    stackNode["type"] = var["type"]
                else: 
                    exitProgram(53)
                
                dataStack.append(stackNode)

            case "POPS":
                if len(argumentsType) != 1:
                    exitProgram(32)
                if len(dataStack) == 0:
                    exitProgram(56)

                var = findVarInFrame(argumentsValues[0])
                poppedNode = dataStack.pop()
                var["value"] = poppedNode["value"]
                var["type"] = poppedNode["type"]

            case "ADD" | "SUB" | "MUL" | "IDIV":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                result = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                if isConstant(argumentsType[2]["type"]):
                    op2 = argumentsValues[2]
                elif isVar(argumentsType[2]["type"]):
                    var = findVarInFrame(argumentsValues[2])
                    op2 = var["value"]
                else: 
                    exitProgram(53)                      

                try:
                    op1 = int(op1)
                    op2 = int(op2)
                except ValueError:
                    exitProgram(53)

                if opcode == "ADD":
                    tmpResult = op1 + op2
                elif opcode == "SUB":
                    tmpResult = op1 - op2
                elif opcode == "MUL": 
                    tmpResult = op1 * op2
                else:
                    try:
                        tmpResult = op1 // op2
                    except ZeroDivisionError:
                        exitProgram(57) 
                result["value"] = str(tmpResult)

            case "LT" | "GT" | "EQ" :
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    type1 = argumentsType[1]["type"]
                    value1 = argumentsValues[1]
                else:
                    var1 = findVarInFrame(argumentsValues[1])
                    type1 = var1["type"]
                    value1 = var1["value"]
                if isConstant(argumentsType[2]["type"]):
                    type2 = argumentsType[2]["type"]
                    value2 = argumentsValues[2]
                else:
                    var2 = findVarInFrame(argumentsValues[2])
                    type2 = var2["type"]
                    value2 = var2["value"]
                if type1 != type2:
                    exitProgram(53)   

                if opcode == "EQ":
                    result = str(value1 == value2).lower()
                elif opcode == "GT":
                    if type1 == "string":
                        result = value1 >= value2
                    elif type1 == "bool":
                        if value1 == "true" and value2 == "false":
                            result = "true"
                        else:
                            result = "false"
                    else:
                        result = str(value1 > value2).lower()
                else:
                    if type1 == "string":
                        result = str(value1 <= value2).lower()
                    elif type1 == "bool":
                        if value1 == "true" and value2 == "false":
                            result = "true"
                        else:
                            result = "false"
                    else:
                        result = str(value1 < value2).lower()

                var["type"] = "bool"
                var["value"] = result

            case "AND" | "OR":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "bool":
                        exitProgram(53)
                    type1 = argumentsType[1]["type"]
                    value1 = argumentsValues[1]
                else:
                    var1 = findVarInFrame(argumentsValues[1])
                    if var1["type"] != "bool":
                        exitProgram(53)
                    type1 = var1["type"]
                    value1 = var1["value"]
                if isConstant(argumentsType[2]["type"]):
                    if argumentsType[2]["type"] != "bool":
                        exitProgram(53)
                    type2 = argumentsType[2]["type"]
                    value2 = argumentsValues[2]
                else:
                    var2 = findVarInFrame(argumentsValues[2])
                    if var1["type"] != "bool":
                        exitProgram(53)
                    type2 = var2["type"] 
                    value2 = var2["value"]

                if value1 == "true":
                    value1 = 1
                else:
                    value1 = 0
                if value2 == "true":
                    value2 = 1
                else:
                    value2 = 0
                
                if opcode == "AND":
                    result = value1 & value2
                else:
                    result = value1 | value2

                if result == 1:
                    result = "true"
                else:
                    result = "false"

                var["type"] = "bool"
                var["value"] = result

            case "NOT":
                if len(argumentsType) != 2:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "bool":
                        exitProgram(53)
                    type1 = argumentsType[1]["type"]
                    value1 = argumentsValues[1]
                else:
                    var1 = findVarInFrame(argumentsValues[1])
                    if var1["type"] != "bool":
                        exitProgram(53)
                    type1 = var1["type"]
                    value1 = var1["value"]      

                if value1 == "true":
                    result = "false"
                else:
                    result = "true" 

                var["type"] = "bool"
                var["value"] = result 

            case "INT2CHAR":
                if len(argumentsType) != 2:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                res = findVarInFrame(argumentsValues[0])

                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "int":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "int":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                result = str(chr(int(op1)))
                res["type"] = "string"
                res["value"] = result

            case "STRI2INT":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "string":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                if isConstant(argumentsType[2]["type"]):
                    if argumentsType[2]["type"] != "int":
                        exitProgram(53)
                    op2 = argumentsValues[2]
                elif isVar(argumentsType[2]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "int":
                        exitProgram(53)
                    op2 = var["value"]
                else: 
                    exitProgram(53)   

                text = list(op1)
                result = str(ord(text[int(op2)]))

                var["type"] = "int"
                var["value"] = result

            case "READ":
                if len(argumentsType) != 2:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if argumentsValues[1] not in ["int", "bool", "string"]:
                    exitProgram(53) 

                if inputFile == sys.stdin:
                    msg = input()
                else:
                    msg = file.readline()
                    msg = msg.rstrip('\n')
                
                if not msg:
                    dataType = "nil"
                    value = "nil"
                elif argumentsValues[1] == "bool":
                    dataType = "bool"
                    if msg.lower() == "true":
                        value = "true"
                    else:
                        value = "false"
                elif argumentsValues[1] == "string":
                    dataType = "string"
                    value = msg
                else:
                    dataType = "int"
                    try:
                        value = str(int(msg))
                    except ValueError:
                        dataType = "nil"
                        value = "nil"
                updateVar(var, dataType, value)

            case "WRITE":
                if len(argumentsType) != 1:
                    exitProgram(32)
                if isConstant(argumentsType[0]["type"]):
                    message = argumentsValues[0]
                elif isVar(argumentsType[0]["type"]):
                    var = findVarInFrame(argumentsValues[0])
                    try:
                        if var["type"] == "nil":
                            message = ""
                    except TypeError:
                        exitProgram(53)    
                    message = var["value"]
                    if message == None:
                        message = ""
                try:    
                    print(message, end="")
                except UnboundLocalError:
                    print("", end="")
                debugMessage()

            case "CONCAT":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "string":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                if isConstant(argumentsType[2]["type"]):
                    if argumentsType[1]["type"] != "string":
                        exitProgram(53)
                    op2 = argumentsValues[2]
                elif isVar(argumentsType[2]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op2 = var["value"]
                else: 
                    exitProgram(53) 

                var["value"] = op1 + op2
                var["type"] = "string"

            case "STRLEN":
                if len(argumentsType) != 2:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "string":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                var["type"] = "int"
                var["value"] = len(op1)

            case "GETCHAR":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "string":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                if isConstant(argumentsType[2]["type"]):
                    if argumentsType[2]["type"] != "int":
                        exitProgram(53)
                    op2 = argumentsValues[2]
                elif isVar(argumentsType[2]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "int":
                        exitProgram(53)
                    op2 = var["value"]
                else: 
                    exitProgram(53) 

                op2 = int(op2)
                if op2 > len(op1) - 1:
                    exitProgram(58)
                
                text = list(op1)
                var["type"] = "string"
                var["value"] = str(text[op2])

            case "SETCHAR":
                if len(argumentsType) != 3:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if var["type"] != "string":
                    exitProgram(53)
                
                if isConstant(argumentsType[1]["type"]):
                    if argumentsType[1]["type"] != "int":
                        exitProgram(53)
                    op1 = argumentsValues[1]
                elif isVar(argumentsType[1]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "int":
                        exitProgram(53)
                    op1 = var["value"]
                else: 
                    exitProgram(53)

                if isConstant(argumentsType[2]["type"]):
                    if argumentsType[2]["type"] != "string":
                        exitProgram(53)
                    op2 = argumentsValues[2]
                elif isVar(argumentsType[2]["type"]):
                    var = findVarInFrame(argumentsValues[1])
                    if var["type"] != "string":
                        exitProgram(53)
                    op2 = var["value"]
                else: 
                    exitProgram(53)
                
                if op2 == "":
                    exitProgram(58)
                text = list(op2)
                char = text[0]

                op1 = int(op1)
                modified = var["value"]
                if op1 > len(modified) - 1:
                    exitProgram(58)
                modified = list(modified)
                modified[op1] = char
                var["value"] = "".join(modified)

            case "TYPE":
                if len(argumentsType) != 2:
                    exitProgram(32)
                checkVar(argumentsType[0]["type"])
                var = findVarInFrame(argumentsValues[0])
                if isConstant(argumentsType[1]["type"]):
                    op = argumentsType[1]["type"]
                elif isVar(argumentsType[1]["type"]):
                    op = findVarInFrame(argumentsValues[1])["type"]
                    if op == None:
                        op = ""
                else:
                    exitProgram(53)

                if op in ["", "int", "bool", "string", "nil"]:
                    var["value"] = op
                    var["type"] = "string"
                else:   
                    exitProgram(99)          

            case "LABEL":
                pass 

            case "JUMP":
                pass 

            case "JUMPIFEQ":
                pass

            case "JUMPIFNEQ":
                pass

            case "EXIT":
                if len(argumentsType) != 1:
                    exitProgram(32)
                if isConstant(argumentsType[0]["type"]):
                    if argumentsType[0]["type"] != "int":
                        exitProgram(53)
                    op1 = argumentsValues[0]
                elif isVar(argumentsType[0]["type"]):
                    var = findVarInFrame(argumentsValues[0])
                    if var["type"] != "int":
                        exitProgram(53)
                    op1 = var["value"]
                else:
                    exitProgram(53)
                op1 = int(op1)
                if not 0 <= op1 <= 49:
                    exitProgram(57)
                exitProgram(op1)

            case "DPRINT":
                if len(argumentsType) != 1:
                    exitProgram(32)
                if isConstant(argumentsType[0]["type"]):
                    op1 = argumentsValues[0]
                elif isVar(argumentsType[0]["type"]):
                    var = findVarInFrame(argumentsValues[0])
                    op1 = var["value"]
                else:
                    exitProgram(53)

                sys.stderr.write(op1)

            case "BREAK":
                pass

            case _:
                exitProgram(32)

    exitProgram(0)

                
if __name__ == "__main__":
    main()