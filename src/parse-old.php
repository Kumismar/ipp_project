<?php

ini_set('display_errors', 'stderr');
define("debugPrint", 0);

$xml = new XMLWriter();
$emptyLine = "/\A\s*\z/";
$comment = "(?i)(#.*)?";
$varLabelName = "[_\-\$&%\*!\?a-zA-Z][_\-\$&%\*!\?a-zA-Z0-9]*";
$instructionNumber = 1;

function dbgMsg($text)
{
    if (debugPrint)
        echo $text;
}

function processArguments()
{
    global $argc, $argv;
    if ($argc > 2)
    {
        dbgMsg("Na picu argummenty kundo\n");
        exit(10);
    }
    elseif ($argc == 2)
    {
        if ($argv[1] === "--help")
        {
            printHelp();
            exit(0);
        }
        else
        {
            dbgMsg("Na picu argumenty kundo\n");
            exit(10);
        }
    }
}

function myGetType($string) : string
{
    global $varLabelName;

    $parsed = preg_split("/@/", $string);
    if (preg_match("/(GF|TF|LF)/i", $parsed[0]))
        return "var";

    if (preg_match("/^(bool|int|string)$/i", $string))
        return "type";
    elseif (preg_match("/(string|int|bool|nil)@.*/i", $string))
        return $parsed[0];
    
    return "label";
}

function getValue($arg) : string
{
    $type = myGetType($arg);
    if (preg_match("/(int|string|bool|nil)/i", $type))
    {
        $arg = preg_split("/@/", $arg);
        return $arg[1];
    }
    elseif (preg_match("/(var|label|type)/i", $type))
        return $arg;
}

function checkHeader($in) : int
{
    global $emptyLine;
    global $comment;
    $headerLine = "/^\s*\.ippcode23\s*$comment$/i";
    while (!feof($in))
    {
        $line = fgets($in);        
        if (preg_match($emptyLine, $line))
        {
            dbgMsg("Empty line pred hlavickou\n");
            continue;
        }
        elseif (preg_match("/^\s*#.*$/", $line))
        {
            dbgMsg("Commentline pred hlavickou");
            continue;
        }
        elseif (preg_match($headerLine, $line))
            return 1;
        else
        {
            dbgMsg("Hlavicka tam jakasi je, ale uplne na kokot\n");
            exit(21);
        }
    }
    dbgMsg("EOF dopici\n");
    exit(21);
}

function createXML()
{
    global $xml;
    $xml->openUri("php://stdout");
    $xml->startDocument("1.0", "UTF-8");
    $xml->setIndent(true);
    $xml->startElement("program");
    $xml->writeAttribute("language", "IPPcode23");
}

function addToXML($line)
{
    global $instructionNumber;
    global $xml;
    global $comment;
    $line = preg_replace("/$comment/i", "", $line);
    $output = preg_split("/\s+/", $line);
    
    $xml->startElement("instruction");
    $xml->writeAttribute("order", "$instructionNumber");
    $xml->writeAttribute("opcode", strtoupper($output[0]));
    
    for ($i = 1; isset($output[$i]); $i++)
    {
        if ($output[$i] === "")
            continue;
        $xml->startElement("arg$i");
        $xml->writeAttribute("type", myGetType($output[$i]));
        $xml->text(getValue($output[$i]));
        $xml->endElement();
    }
    $xml->endElement();
}

function printHelp()
{
    echo "Prepinac --help => za chvilku tady snad neco bude\n";
}

function parse($in)
{
    global $emptyLine;
    global $instructionNumber;
    global $varLabelName;
    global $comment;
    $instructions = "(move|createframe|pushframe|popframe|defvar|call|return|pushs|pops|add|sub|mul|idiv|lt|gt|eq|and|or|not|int2char|stri2int|read|write|concat|strlen|getchar|setchar|type|label|jumpifeq|jumpifneq|^jump$|exit|dprint|break)";
    $variable = "(GF|TF|LF)@$varLabelName";
    $stringLiteral = "string@([^\s#\\\\]|\\\\\d{3})*";
    $intConstant = "(?-i)int@[-+]?\d+(?i)";
    $boolConstant = "(?-i)bool@(true|false)(?i)";
    $nil = "(?-i)nil@nil(?i)";
    $symbol = "($variable|$intConstant|$boolConstant|$stringLiteral|$nil)";
    $varType = "(?-i)(int|bool|string)";

    $commentLine = "/^\s*#.*$/"; 
    $noOperandInstructions = "/^\s*(createframe|pushframe|popframe|return|break)\s*$comment\s*$/i";
    $arithmeticInstructions = "/^\s*(?i)(add|sub|mul|idiv|gt|lt|eq)(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/"; 
    $flowControlInstructions = "/^\s*(?i)(label|jump|call)(?-i)\s+$varLabelName\s*$comment\s*$/"; 
    $conditionJumps = "/^\s*(?i)(jumpifeq|jumpifneq)(?-i)\s+$varLabelName\s+$symbol\s+$symbol\s*$comment\s*$/"; 
    $logicalInstructions = "/^\s*(?i)(and|or)(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/"; 
    $exit = "/^\s*(?i)exit(?-i)\s+$symbol\s*$comment$/"; 
    $dprint = "/^\s*(?i)dprint(?-i)\s+$symbol\s*$comment\s*$/";
    $not = "/^\s*(?i)not(?-i)\s+$variable\s+$symbol\s*$comment\s*$/";
    $move = "/^\s*(?i)move(?-i)\s+$variable\s+$symbol\s*$comment\s*$/";~
    $concat = "/^\s*(?i)concat(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/";
    $getchar = "/^\s*(?i)getchar(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/";
    $setchar = "/^\s*(?i)setchar(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/"; 
    $strlen = "/^\s*(?i)strlen(?-i)\s+$variable\s+$symbol\s*$comment\s*$/";
    $type = "/^\s*(?i)type(?-i)\s+$variable\s+$symbol\s*$comment\s*$/";
    $read = "/^\s*(?i)read(?-i)\s+$variable\s+$varType\s*$comment$/";
    $write = "/^\s*(?i)write(?-i)\s+$symbol\s*$comment$/"; 
    $int2char = "/^\s*(?i)int2char(?-i)\s+$variable\s+$symbol\s*$comment\s*$/";
    $stri2int = "/^\s*(?i)stri2int(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/";
    $pushs = "/^\s*(?i)pushs(?-i)\s+$symbol\s*$comment\s*$/";
    $pops = "/^\s*(?i)pops(?-i)\s+$variable\s*$comment\s*$/";
    $defvar = "/^\s*(?i)defvar(?-i)\s+$variable\s*$comment$/";

    while ($line = fgets($in))
    {
        dbgMsg($line);

        if (preg_match($emptyLine, $line))
        {
            dbgMsg("EmptyLine ok\n");
            continue;
        }
        elseif (preg_match($commentLine, $line))
        {
            dbgMsg("Comment ok\n");
            continue;
        }
        elseif (preg_match($move, $line))
        {
            dbgMsg("move ok\n");
        }
        elseif (preg_match($noOperandInstructions, $line))
        {
            dbgMsg("createframe/pushframe/popframe/return/break ok\n");
        }
        elseif (preg_match($conditionJumps, $line))
        {
            dbgMsg("jumpif(n)eq ok\n");
        }
        elseif (preg_match($arithmeticInstructions, $line))
        {
            dbgMsg("add/sub/mul/idiv/gt/lt/eq ok\n");
        }
        elseif (preg_match($logicalInstructions, $line))
        {
            dbgMsg("and/or ok\n");
        }
        elseif (preg_match($flowControlInstructions, $line))
        {
            dbgMsg("label/jump/call ok\n");
        }
        elseif (preg_match($dprint, $line))
        {
            dbgMsg("dprint ok\n");
        }
        elseif (preg_match($exit, $line))
        {
            dbgMsg("exit ok\n");
        }
        elseif (preg_match($not, $line))
        {
            dbgMsg("not ok\n");
        }
        elseif (preg_match($concat, $line))
        {
            dbgMsg("concat ok\n");
        }
        elseif (preg_match($getchar, $line))
        {
            dbgMsg("getchar ok\n");
        }
        elseif (preg_match($setchar, $line))
        {
            dbgMsg("setchar ok\n");
        }
        elseif (preg_match($strlen, $line))
        {
            dbgMsg("strlen ok\n");
        }
        elseif (preg_match($type, $line))
        {
            dbgMsg("type ok\n");
        }
        elseif (preg_match($read, $line))
        {
            dbgMsg("read ok\n");
        }
        elseif (preg_match($write, $line))
        {
            dbgMsg("write ok\n");
        }
        elseif (preg_match($int2char, $line))
        {
            dbgMsg("int2char ok\n");
        }
        elseif (preg_match($stri2int, $line))
        {
            dbgMsg("stri2int ok\n");
        }
        elseif (preg_match($pushs, $line))
        {
            dbgMsg("pushs ok\n");
        }
        elseif (preg_match($pops, $line))
        {
            dbgMsg("pops ok\n");
        }
        elseif (preg_match($defvar, $line))
        {
            dbgMsg("defvar ok\n");
        }
        else
        {
            if (preg_match("/^((?i).ippcode23(?-i)|[a-zA-Z][a-zA-Z0-9\s]*)$/", $line) &&
                preg_match("/^$instructions.*$/i", $line) == false)
                exit(22);
            elseif (preg_match("/^$instructions\S+$/i", $line))
                exit(22);
            dbgMsg("Je to v kunde\n");
            exit(23);
        }
        addToXML($line);
        $instructionNumber++;
    }
}

$file = fopen("php://stdin", 'r');
processArguments();

if (!checkHeader($file))
    dbgMsg("Missing header\n");
else
    dbgMsg("Header ok\n");

createXML();
parse($file);
$xml->endDocument();
file_put_contents("out.xml", $xml->outputMemory());
exit(0);