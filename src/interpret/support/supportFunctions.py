PRINT_ALLOWED = True

def debugMessage(message):
    if (PRINT_ALLOWED):
        print(message)

def printHelp():
    print("Nice help bruh")

def errorExit(errMessage, exitCode):
    print(errMessage)
    exit(exitCode)