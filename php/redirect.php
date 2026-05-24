<?php

include_once __DIR__ . '/bots/python.php';
include_once __DIR__ . '/bots/file_bots.php';

use function BOTS\Python\do_py;
use function BOTS\FILE_BOTS\dump_to_file;

$title      = $_GET['title'] ?? $_POST['title'] ?? '';
$titlelist  = $_GET['titlelist'] ?? $_POST['titlelist'] ?? '';
//---
// the root path is the first part of the split file path
$ROOT_PATH = getenv("HOME") ?: 'I:/MD_TOOLS/MDWIKI_MAIN_REPO';

function printForm($title, $titlelist)
{
    $start_icon = "<input class='btn btn-outline-primary' type='submit' value='send'>";
    // ---
    if (empty($GLOBALS['global_username'])) $start_icon = '<a role="button" class="btn btn-primary" href="/auth/login.php">Log in</a>';
    // ---

    //---
    $rows = <<<HTML
        <div class='col-lg-12'>
            <div class='form-group'>
                <div class='input-group mb-3'>
                    <div class='input-group-prepend'>
                        <span class='input-group-text'>Title:</span>
                    </div>
                    <input class='form-control' type='text' id='title' name='title' value='$title'/>
                </div>
            </div>
        </div>
        <div class='col-lg-12'>
            <h3 class='aligncenter'>or</h3>
        </div>
        <div class='col-lg-12'>
            <div class='form-group'>
                <div class='input-group mb-3'>
                    <div class='input-group-prepend'>
                        <span class='input-group-text'>List of titles:</span>
                    </div>
                    <textarea class='form-control' cols='20' rows='7' id='titlelist' name='titlelist'>$titlelist</textarea>
                </div>
            </div>
        </div>
        <div class='col-lg-12'>
            <h4 class='aligncenter'>
                $start_icon
            </h4>
        </div>
    HTML;

    echo <<<HTML
        <form action='redirect.php' method='POST'>

            <div class='container'>
                <div class='container'>
                    <div class='row'>
                        $rows
                    </div>
                </div>
            </div>
        </form>
    HTML;
}
function get_results($aargs)
{
    //---
    $ccc = " red.py $aargs save";
    //---
    $params = array(
        'dir' => "c9",
        'localdir' => "c9",
        'pyfile' => 'pwb.py',
        'other' => $ccc,
    );
    //---
    $result = do_py($params, "redirect0");
    //---
    return $result;
}
function createRedirects($title, $titlelist)
{
    //---
    global $ROOT_PATH;
    //---

    //echo $_SERVER['SERVER_NAME'];
    echo "<span style='font-size:15pt;color:green'>";
    echo '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;';

    $file = "$ROOT_PATH/public_html/texts/redirectlist.txt";

    if (!empty($title)) {
        $pythonCommand = "-page2:" . rawurlencode($title);
        echo '<span class="">The Bot will create redirects for ' . rawurldecode($title) . ' in seconds.</span>';
    } else {
        $filename = dump_to_file($titlelist, $file);
        // ---
        $pythonCommand = "-file:$filename";
        // ---
        echo '<span class="">The Bot will create redirects for titles in the list in seconds.</span>';
    }

    echo '</span>';
    echo "<br>";

    $result = get_results($pythonCommand);
    // ---
    echo $result;
}

echo <<<HTML
    <div class="card">
        <div class="card-header aligncenter" style="font-weight:bold;">
            <h3>Create redirects.</h3>
        </div>
        <div class="card-body">
HTML;
//---
if ((empty($title) && empty($titlelist)) || empty($GLOBALS['global_username'])) {
    printForm($title, $titlelist);
} else {
    createRedirects($title, $titlelist);
}
echo <<<HTML
    </div>
HTML;
//---
