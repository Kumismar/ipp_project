<?php

ini_set('display_errors', 'stderr');

function processArguments()
{
    global $argc, $argv;
    if ($argc > 2)
        exit(10);
    elseif ($argc == 2)
    {
        if ($argv[1] === "--help")
        {
            printHelp();
            exit(0);
        }
        else
            exit(10);
    }
}

function myGetType($string)
{
    $parsed = explode("@", $string);
    if (preg_match("/(GF|TF|LF)/i", $parsed[0]))
        return "var";

    if (preg_match("/^(bool|int|string)$/i", $string))
        return "type";
    elseif (preg_match("/(string|int|bool|nil)@.*/i", $string))
        return $parsed[0];

    return "label";
}

function getValue($arg)
{
    $type = myGetType($arg);
    if (preg_match("/(int|string|bool|nil)/i", $type))
    {
        $arg = explode("@", $arg);
        return $arg[1];
    }
    elseif (preg_match("/(var|label|type)/i", $type))
        return $arg;
    else
        exit(99);
}

function checkHeader($in)
{
    global $emptyLine;
    global $comment;
    $headerLine = "/^\s*\.ippcode23\s*$comment$/i";
    while (!feof($in))
    {
        $line = fgets($in);
        if (preg_match($emptyLine, $line))
            continue;
        elseif (preg_match("/^\s*#.*$/", $line))
            continue;
        elseif (preg_match($headerLine, $line))
            return 1;
        else
            exit(21);
    }
    exit(21);
}

function initXML()
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

    $templates = array(
        "/^\s*(createframe|pushframe|popframe|return|break)\s*$comment\s*$/i",
        "/^\s*(?i)(add|sub|mul|idiv|gt|lt|eq)(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)(label|jump|call)(?-i)\s+$varLabelName\s*$comment\s*$/",
        "/^\s*(?i)(jumpifeq|jumpifneq)(?-i)\s+$varLabelName\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)(and|or)(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)exit(?-i)\s+$symbol\s*$comment$/",
        "/^\s*(?i)dprint(?-i)\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)not(?-i)\s+$variable\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)move(?-i)\s+$variable\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)concat(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)getchar(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)setchar(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)strlen(?-i)\s+$variable\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)type(?-i)\s+$variable\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)read(?-i)\s+$variable\s+$varType\s*$comment$/",
        "/^\s*(?i)write(?-i)\s+$symbol\s*$comment$/",
        "/^\s*(?i)int2char(?-i)\s+$variable\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)stri2int(?-i)\s+$variable\s+$symbol\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)pushs(?-i)\s+$symbol\s*$comment\s*$/",
        "/^\s*(?i)pops(?-i)\s+$variable\s*$comment\s*$/",
        "/^\s*(?i)defvar(?-i)\s+$variable\s*$comment$/"
    );

    while ($line = fgets($in))
    {
        if (preg_match($emptyLine, $line))
            continue;
        elseif (preg_match($commentLine, $line))
            continue;

        foreach ($templates as $template)
        {
            if (preg_match($template, $line))
            {
                addToXML($line);
                $instructionNumber++;
                continue 2;
            }
        }

        if (preg_match("/^((?i).ippcode23(?-i)|[a-zA-Z][a-zA-Z0-9\s]*)$/", $line) && !preg_match("/^$instructions.*$/i", $line))
            exit(22);
        elseif (preg_match("/^$instructions\S+$/i", $line))
            exit(22);
        exit(23);
    }
}

$emptyLine = "/\A\s*\z/";
$comment = "(?i)(#.*)?";
$varLabelName = "[_\-\$&%\*!\?a-zA-Z][_\-\$&%\*!\?a-zA-Z0-9]*";
$instructionNumber = 1;

$file = fopen("php://stdin", 'r');
if (!$file) exit(11);

processArguments();
checkHeader($file);

$xml = new XMLWriter();
initXML();
parse($file);

$xml->endDocument();
exit(0);