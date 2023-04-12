import os
import sys
import xml.etree.ElementTree as et

import errors as errors
import supportFunctions as suppFunc

def parseArguments(args):
    if len(args) > 3:
        suppFunc.errorExit("Command-line arguments", errors.INVALID_CMDLINE_ARGS)
    else: 
        suppFunc.debugMessage("Pocty v cajku")

    for arg in args:
        if arg == "--help" or arg == "-h":
            suppFunc.printHelp()
        elif arg == os.path.realpath(__file__):
            continue

        try:
            x = arg.split('=')
        except ValueError:
            errors.errorExit("Command-line arguments", errors.INVALID_CMDLINE_ARGS)
    
        if x[0] == "--input" and x[1] is not None:
            inputFile = x[1]
        elif x[0] == "--source" and x[1] is not None:
            sourceFile = x[1]
        else: 
            errors.errorExit("Command-line arguments", errors.INVALID_CMDLINE_ARGS)

    return inputFile, sourceFile
    
def main():
    input, source = parseArguments(sys.argv)
    print(input)
    print(source)

if __name__ == "__main__":
    main()