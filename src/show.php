<?php
$dir = "./";
$dh  = opendir($dir);
while (false !== ($filename = readdir($dh))) {
    $files[] = $filename;
}
?>
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Untitled Document</title>
</head>

<body>
<table style="cellspacing:0px; cellpadding:0px;">
<?php

$c=0;
echo '<tr>';
foreach($files as $key => $filename){
	if (strpos($filename,".jpg") !== false)
	{
		echo '<td valign="top"><center>'.$filename.'<br><img width="90%" src="'.$filename.'"></center></td>';
		if( $c == 4){ echo '</tr><tr>'; $c=0; }
		else{ $c=$c+1; }
	}
}
?>
</table>
</body>
</html>
