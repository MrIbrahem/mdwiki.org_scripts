<?php

namespace BOTS\Python;

$root_path = getenv("HOME") ?: 'I:/mdwiki';


function do_py($params, $do_test = true, $return_commaand = false)
{
    //---
    global $root_path;
    //---
    $dir        = $params['dir'] ?? '';
    $localdir   = $params['localdir'] ?? '';
    $pyfile     = $params['pyfile'] ?? '';
    $other      = $params['other'] ?? '';
    //---
    $py3 = $root_path . "/local/bin/python3";
    //---
    $my_dir = $dir;
    //---
    if ($_SERVER['SERVER_NAME'] == 'localhost') {
        $my_dir = $localdir;
        $py3 = "python3";
    };
    //---
    if ($pyfile != '' && $my_dir != '') {
        $command = $py3 . " $my_dir/$pyfile $other";
        //---
        // replace // with /
        $command = str_replace('//', '/', $command);
        //---
        if ($do_test == true) {
            if ($_SERVER['SERVER_NAME'] == 'localhost' || ($_GET['test'] ?? "") != '') {
                echo "<h6>$command</h6>";
            };
        };
        //---
        // Passing the command to the function
        $cmd_output = @shell_exec($command);
        //---
        if ($return_commaand == true) {
            return ["command" => $command, "output" => $cmd_output];
        }
        //---
        return $cmd_output;
    };
    return '';
}
