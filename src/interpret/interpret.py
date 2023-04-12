import sys
import xml.etree.ElementTree as et

from support import errors
from support import supportFunctions

def parseArguments(args):
    if len(args) > 3:
        supportFunctions.errorExit("Command-line arguments", errors.INVALID_CMDLINE_ARGS)
    else: 
        supportFunctions.debugMessage("Pocty v cajku")

    for arg in args:
        if arg == "--help" or arg == "-h":
            supportFunctions.printHelp()

        try:
            x = arg.split('=')
        except ValueError:
            errors.errorExit("Command-line arguments", errors.INVALID_CMDLINE_ARGS)
    
        if x[0] == "input" and x[1] is not None:
            inputFile = x[1]
        elif x[0] == "source" and x[1] is not None:
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