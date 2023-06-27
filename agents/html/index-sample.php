<?php
print '<!DOCTYPE html>';
print '<html>';
print '<head><link rel="shortcut icon" type="image/x-icon" href="../../kraken.png" />';

$name = shell_exec('pwd');
$f = explode("/",$name);
$name = array_pop($f);

print '<title>'.$name.'</title>';
print '</head>';
print '<style>';
print 'a:link{color:#202020; background-color:transparent; text-decoration:none}';
print 'a:visited{color:#0074AA; background-color:transparent; text-decoration:none}';
print 'a:hover{color:#000090;background-color:transparent; text-decoration:underline}';
print 'a:active{color:#000040;background-color:transparent; text-decoration:underline}';
print 'body.ex{margin-top: 0px; margin-bottom:25px; margin-right: 25px; margin-left: 25px;}';
print '</style>';
print '<body class="ex" bgcolor="#ffefef">';
print '<body style="font-family: arial;font-size: 20px;font-weight: bold;color:#405050;">';

print '<!DOCTYPE html>';
print '<html>';
print '<head>';
print '<title>'. $name .'</title>';
print '</head>';
print '<h1 style="font-family:arial;font-size:20px;font-weight:medium;color:#222222;">Sample: <a href=README>' . $name . '</a></h1>';
print '<style>';
print 'a:link{color:#202020; background-color:transparent; text-decoration:none}';
print 'a:visited{color:#0074AA; background-color:transparent; text-decoration:none}';
print 'a:hover{color:#000090;background-color:transparent; text-decoration:underline}';
print 'a:active{color:#000040;background-color:transparent; text-decoration:underline}';
print 'body.ex{margin-top:25px; margin-bottom:25px; margin-right: 25px; margin-left: 25px;}';
print '</style>';
print '<body class="ex" bgcolor="#ffefef">';
print '<body style="font-family: arial;font-size: 16px;font-weight: medium;color:#405050;">';
print '<hr>';

// list the png files and provide link access
$output = shell_exec('ls -1 *.png');
$f = explode("\n",$output);
if (sizeof($f) > 1) {
  print '<code>';
  foreach ($f as &$file) {
    print '   <a href="' . $file . '"><img width=30% src=' . $file . '></a>';
  }
  print '</code><br>';
}

// list the error counting per file
$output = shell_exec('ls -1 README ncounts.err');
$f = explode("\n",$output);
if (sizeof($f) > 1) {
  print '<code>';
  foreach ($f as &$file) {
    print '<a href="'.$file.'">'.$file.'</a><br>';
  }
  print '</code>';
}

// list the log files and provide link access
$output = shell_exec('ls -lt ????????-????-????-????-????????????.??? | tr -s " "');
$f = explode("\n",$output);
if (sizeof($f) > 1) {
  print 'Most recent up top<pre>';
  $i=0;
  foreach ($f as &$file) {
    $search = array(".err");
    $replace1 = array(".out");
    $replace2 = array("");
    if ($file != "") {
      $g = explode(" ",$file);
      $filename = array_pop($g);
      array_shift($g);
      array_shift($g);
      array_shift($g);
      array_shift($g);
      $size = (int) array_shift($g);
      $date = implode(" ", $g); 
      //$rest = implode(" ", $g); 
      $stub = str_replace($search,$replace2,$filename);
      // print '<li> ['.$i.'] '. $rest . ' --> ' . ' <a href="' . $filename . '">'.$filename.'</a>';
      printf("[%06d] <a href=\"%s\">%s</a> -- %s (Size: %d kB)\n",$i,$filename,$filename,$date,$size/1000);
      $i=$i+1;
    }
  }
  print '</pre>';
}
?>

<hr>
<p style="font-family: arial;font-size: 10px;font-weight: bold;color:#405050;">
<!-- hhmts start -->
<?php
$output = shell_exec('cat ../../../../heartbeat');
$f = explode("\n",$output);
foreach ($f as &$line) {
  print $line;
}
?>
-- <a href="http://web.mit.edu/physics/people/faculty/paus_christoph.html">Christoph Paus</a>
<!-- hhmts end -->
</p>
</body></html>
