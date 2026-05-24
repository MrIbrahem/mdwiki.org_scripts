<?php

include_once __DIR__ . '/bots/python.php';

use function BOTS\Python\do_py;

echo <<<HTML
    <div class="card">
		<div class="card-header aligncenter" style="font-weight:bold;">
			<h3>Fix redirects</h3>
		</div>
		<div class="card-body">
HTML;
//---
$title = $_GET['title'] ?? '';
//---
echo <<<HTML
	<div class='container'>
HTML;
//---

//---
$start_icon = "<input class='btn btn-outline-primary' type='submit' value='send'>";
// ---
if (empty($GLOBALS['global_username'])) $start_icon = '<a role="button" class="btn btn-primary" href="/auth/login.php">Log in</a>';
// ---
echo <<<HTML
	<form action='fixred.php' method='GET'>

		<div class='container'>
			<div class='row'>
				<div class='col-lg-12'>
					<h6>To run the bot on all pages type: all.</h6>
				</div>
				<div class='col-lg-12'>
					<div class='input-group mb-3'>
						<div class='input-group-prepend'>
							<span class='input-group-text'>Title</span>
						</div>
						<input class='form-control' type='text' id='title' name='title' value='$title' required/>
					</div>
				</div>
				<div class='col-lg-12'>
					<h4 class='aligncenter'>
						$start_icon
					</h4>
				</div>
			</div>
		</div>
	</form>
HTML;

function get_results($title)
{
	//---
	//---
	$title2 = str_replace('+', '_', $title);
	$title2 = str_replace(' ', '_', $title2);
	$title2 = str_replace('"', '\\"', $title2);
	$title2 = str_replace("'", "\\'", $title2);
	$title2 = rawurlencode($title2);
	//---
	$ccc = " fixred.py -page2:$title2 save";
	//---
	$params = array(
		'dir' => "c9",
		'localdir' => "c9",
		'pyfile' => 'pwb.py',
		'other' => $ccc,
	);
	//---
	$result = do_py($params, 'fixred0');
	//---
	return $result;
}
//---
if (!empty($title) && !empty($GLOBALS['global_username'])) {
	echo "starting:<br>";
	//---
	$resultb = get_results($title);
	//---
	echo "finished. result:($resultb)<br>";
	//---
	echo $resultb;
};
//---
echo <<<HTML
	</div>
HTML;
//---
