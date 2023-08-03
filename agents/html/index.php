<!DOCTYPE html>
<html>
<head>
<title>Agents</title>
<link rel="shortcut icon" type="image/x-icon" href="kraken.png" />
</head>
<style>
a:link{color:#202020; background-color:transparent; text-decoration:none}
a:visited{color:#0074AA; background-color:transparent; text-decoration:none}
a:hover{color:#000090;background-color:transparent; text-decoration:underline}
a:active{color:#000040;background-color:transparent; text-decoration:underline}
body.ex{margin-top: 0px; margin-bottom:25px; margin-right: 25px; margin-left: 25px;}
</style>

<body class="ex" bgcolor="#ffefef">
<body style="font-family: arial;font-size: 20px;font-weight: bold;color:#405050;">
<hr>
<img src="Kraken.jpg" width="850px" alt="The Agents">
<table><tr><td VALIGN=top>
<?php
$cycle = './cycle.cfg';
$output = shell_exec('ls -1r reviewd/*/*/status*.html');
$f = explode("\n",$output);
if (sizeof($f) > 1) {

  $active = shell_exec('source ' . $cycle . '; echo $KRAKEN_REVIEW_CYCLE');
  $active = substr($active, 0, -1);
  $a = explode(" ",$active);
  print '<h2>Status</h2>'."\n";
  print '<pre>'."\n";
  $f = explode("\n",$output);
  $g = [];
  $book = "";
  $cbook = "";
  $pys = array();
  $search = array("status-",".html");
  $replace = array("","");
  foreach ($f as &$file) {
    if ($file != "") {
      $text = str_replace($search,$replace,$file);
      $g = explode("/",$text);
      $agent = $g[0];
      if ($g[1].'/'.$g[2] == $book) {
	$pys[] = $g[3];
      }
      else {
	if ($book != '') {
	  print '  '.$book.' : ';
          foreach ($pys as &$py) {
            if (in_array("$cbook:$py",$a)) {
              print '<a href="'.$agent.'/'.$book.'/status-'.$py.'.html">'.$py.'</a> (<a href="'.$agent.'/'.$book.'/queue'.'">active</a>)'."\n";
            }
            else {
              print '<a href="'.$agent.'/'.$book.'/status-'.$py.'.html">'.$py.'</a>'."\n";
            }
	  }
	}
	$cbook = $g[1].':'.$g[2];
	$book = $g[1].'/'.$g[2];
	$pys = array();
	$pys[] = $g[3];
      }
    }
  }
  // do not forget last elemet
  print '  '.$book.' : ';
  foreach ($pys as &$py) {
    if (in_array("$cbook:$py",$a)) {
      print '<a href="'.$agent.'/'.$book.'/status-'.$py.'.html">'.$py.'</a> (<a href="'.$agent.'/'.$book.'/queue'.'">active</a>)'."\n";
    }
    else {
      print '<a href="'.$agent.'/'.$book.'/status-'.$py.'.html">'.$py.'</a>'."\n";
    }
  }
  print '</pre>'."\n";
  print "</td>";
}
?>
<td><pre>   </pre></td><td VALIGN=top>
<h2>The Agents</h2>
<pre>
    <a href="catalogd">catalogd</a> -- catalog creation log
    <a href="cleanupd">cleanupd</a> -- cleanup logs
    <a href="monitord">monitord</a> -- monitor for cataloging
    <a href="reviewd">reviewd</a> -- request review logs
</pre>
</td></tr></table>

<!-- <img src="agents.jpg" alt="The Agents"> -->
<hr>
<p style="font-family: arial;font-size: 10px;font-weight: bold;color:#405050;">
<!-- hhmts start -->
<?php
$output = shell_exec('cat heartbeat');
$f = explode("\n",$output);
foreach ($f as &$line) {
  print $line;
}
?>
-- <a href="http://web.mit.edu/physics/people/faculty/paus_christoph.html">Christoph Paus</a>
<!-- hhmts end -->
</p>
</body>
</html>
