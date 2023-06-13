<?php

ini_set('display_errors', 'stderr');

/**
 * Funkce processArguments kontroluje správnost zadání přepínačů/CLI parametrů skriptu. 
 * Při nesprávné kombinaci přepínačů vrací exit code 10.
 */
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

/**
 * Funkce myGetType() vrací typ symbolu předaného této funkci.
 * @param symb Vstupní symbol
 */
function myGetType($symb)
{
    if (preg_match("/^(bool|int|string)$/i", $symb))
        return "type";

    /* Rozdělení vstupního symbolu na "typ@něco", kde "typ" může být buď proměnná nebo druh konstanty. */
    $parsed = explode("@", $symb);
    if (preg_match("/(GF|TF|LF)/i", $parsed[0]))
        return "var";
    elseif (preg_match("/(string|int|bool|nil)/i", $parsed[0]))
        return $parsed[0];

    return "label";
}

/**
 * Funkce getValue() vrací hodnotu vstupního symbolu.
 * @param symb Vstupní symbol
 */
function getValue($symb)
{
    $type = myGetType($symb);
    /* Typ konstanty => vrací se část symbolu za "@". */
    if (preg_match("/(int|string|bool|nil)/i", $type))
    {
        $symb = explode("@", $symb);
        return $symb[1];
    }
    /* U proměnné, návěští nebo typu se rovnou vrací jejich název. */
    elseif (preg_match("/(var|label|type)/i", $type))
        return $symb;
    else
        exit(99);
}

/**
 * Funkce checkHeader() kontroluje, zda se na začátku kódu vyskytuje správná hlavička.
 */
function checkHeader($in)
{
    global $emptyLine;
    global $comment;
    $headerLine = "/^\s*\.ippcode23\s*$comment$/i";
    while (!feof($in))
    {
        /* Skipping empty lines and comment lines. Returns 1 when header is matched.
            Anything else is wrong. */
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

/**
 * Funkce initXML udělá základní inicializaci XML souboru, tedy jej vytvoří
 * a zapíše do něj povinný element program s atributem language=IPPcode23.
 */
function initXML()
{
    global $xml;
    $xml->openUri("php://stdout");
    $xml->startDocument("1.0", "UTF-8");
    $xml->setIndent(true);
    $xml->startElement("program");
    $xml->writeAttribute("language", "IPPcode23");
}

/**
 * Funkce addToXML přidá aktuálně zpracovávanou instrukci se všemi jejími 
 * povinnými atributy do výstupního XML souboru.
 */
function addToXML($line)
{
    global $instructionNumber;
    global $xml;
    global $comment;

    /* Odstranění komentáře z aktuálně čteného řádku. */
    $line = preg_replace("/$comment/i", "", $line);

    /* Rozdělení řádku na instrukci a její případné operandy. 
        Každá položka pole $output je buď opcode instrukce nebo její operand. */
    $output = preg_split("/\s+/", $line);

    /* Přidání elementu instruction s příšlušnými atributy,
        kde opcode je první položka pole $output. */
    $xml->startElement("instruction");
    $xml->writeAttribute("order", "$instructionNumber");
    $xml->writeAttribute("opcode", strtoupper($output[0]));

    for ($i = 1; isset($output[$i]); $i++)
    {
        /* Po nahrazení komentáře prázdným řetězcem se tam občas objevuje. */
        if ($output[$i] === "")
            continue;

        /* Zapsání operandů instrukce jako elementy do výstupního XML. */    
        $xml->startElement("arg$i");
        $xml->writeAttribute("type", myGetType($output[$i]));
        $xml->text(getValue($output[$i]));
        $xml->endElement();
    }
    $xml->endElement();
}

/**
 * Funkce printHelp() vypíše na standardní výstup nápovědu ke skriptu,
 * byl-li při spouštění přítomen přepínač --help.
 */
function printHelp()
{
    echo "Skript parse.php načítá ze standardního vstupu zdrojový kód v jazyce IPPCode23.
Na standardni výstup poté vypíše XML reprezentaci zdrojového kódu. 
Použití: php[8.1] parse.php ([< nazev souboru] | [--help])\n";
}

/**
 * Funkce parse() provádí syntaktickou analýzu zdrojového kódu pomocí regulárních výrazů.
 * @param in Vstupní soubor
 */
function parse($in)
{
    global $emptyLine;
    global $instructionNumber;
    global $varLabelName;
    global $comment;
    $instructions = "(move|createframe|pushframe|popframe|defvar|call|return|pushs|pops|add|sub|mul|idiv|lt|gt|eq|and|or|not|int2char|stri2int|read|write|concat|strlen|getchar|setchar|type|label|jumpifeq|jumpifneq|\bjump\b|exit|dprint|break)";
    $variable = "(GF|TF|LF)@$varLabelName";
    $stringLiteral = "string@([^\s#\\\\]|\\\\\d{3})*";
    $intConstant = "(?-i)int(?i)@([-+]?\d+|0[xX][0-9a-fA-F]+|0[oO]?[0-7]+)";
    $boolConstant = "(?-i)bool@(true|false)(?i)";
    $nil = "(?-i)nil@nil(?i)";
    $symbol = "($variable|$intConstant|$boolConstant|$stringLiteral|$nil)";
    $varType = "(?-i)(int|bool|string)";
    $commentLine = "/^\s*#.*$/";

    /* Pro lepší případnou úpravu kódu jsou v poli $templates "šablony" instrukcí a každá šablona obsahuje
        RV pro symboly, konstanty, komentáře, apod. Pokud by se někde vyskytla chyba v 
        RV, pak stačí změnit RV v proměnných definovaných nad tímto komentářem. */
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
        /* Prázdné řádky a řádky obsahující pouze komentáře jsou přeskakovány. */
        if (preg_match($emptyLine, $line))
            continue;
        elseif (preg_match($commentLine, $line))
            continue;

        /* Každý řádek prochází "šablonami" a pokud se nějaká trefí, pak se zapíše instrukce do výstupního XML. */
        foreach ($templates as $template)
        {
            if (preg_match($template, $line))
            {
                addToXML($line);
                $instructionNumber++;
                continue 2;
            }
        }

        /* Pokud se na řádku opcode žádné instrukce nevyskytuje, případně se za ním
            nachází další znaky (kromě bílých znaků), pak je chyba brána jako špatný opcode. */
        if (!preg_match("/^$instructions.*$/i", $line))
            exit(22);
        elseif (preg_match("/^$instructions\S+$/i", $line))
            exit(22);
        exit(23);
    }
}

$emptyLine = "/\A\s*\z/";
$comment = "(#.*)?";
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