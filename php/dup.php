<?php

// Output HTML structure
echo <<<HTML
    <div class="card">
        <div class="card-header aligncenter" style="font-weight:bold;">
            <h3>Fix duplicate redirects.</h3>
        </div>
        <div class="card-body">
HTML;

// Process request parameters
$start = $_POST['start'] ?? '';


//---
$start_icon = "<input class='btn btn-outline-primary' type='submit' name='start' value='start'>";
// ---
if (empty($GLOBALS['global_username'])) $start_icon = '<a role="button" class="btn btn-primary" href="/auth/login.php">Log in</a>';
// ---
// Handle form submission or execute command
if (empty($start) || empty($GLOBALS['global_username'])) {
    echo <<<HTML
    <form action='dup.php' method='POST'>

        <div class='col-lg-12'>
            <h4 class='aligncenter'>
                $start_icon
            </h4>
        </div>
    </form>
    HTML;
} else {
    // Define command
    echo "starting....";

    $faf = 'toolforge jobs run fixduplict --image python3.9 --command "python3 fix_duplicate.py save"';

    // Execute command and output result
    $result = shell_exec($faf);

    echo $result;
}
echo <<<HTML
    </div>
HTML;
