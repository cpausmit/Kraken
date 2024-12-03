<?php
// Directory to scan
$directory = "./";

// Check if the directory exists
$i = 0;
if (is_dir($directory)) {
    // Scan the directory for files
    $files = scandir($directory);
    
    // Filter out . and .. and non-file entries
    $files = array_filter($files, function($file) use ($directory) {
        return is_file("$directory/$file");
    });

    // Initialize arrays for .out and .err files
    $outFiles = [];
    $errFiles = [];

    // Separate files based on extensions
    foreach ($files as $file) {
        $extension = pathinfo($file, PATHINFO_EXTENSION);
        if ($extension === 'out') {
            $outFiles[] = $file;
        } elseif ($extension === 'err') {
            $errFiles[] = $file;
        }
    }

    // Create pairs of .out and .err files
    $pairs = [];
    foreach ($outFiles as $outFile) {
        $baseName = pathinfo($outFile, PATHINFO_FILENAME);
        $errFile = $baseName . '.err';

        if (in_array($errFile, $errFiles)) {
            $pairs[] = [
	    	'base' => $baseName,
                'out' => $outFile,
                'err' => $errFile,
                'out_info' => stat("$directory/$outFile"),
                'err_info' => stat("$directory/$errFile"),
            ];
        }
    }
} else {
    die("Directory does not exist.");
}

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

?>


Most recent up top
<pre>
<table>
  <tr>
    <th>Index</th>
    <th>Base</th>
    <th>out [kB] LMod</th>
    <th>err [kB] LMod</th>
  </tr>
  <?php if (!empty($pairs)): ?>
  <?php foreach ($pairs as $pair): ?>
  <tr>
    <td><?php $i=$i+1; printf('[%06d]',$i); ?></td>
    <td><?php echo $pair['base']." :"; ?></td>
    <td><?php echo "<a href="; echo $pair['out']; echo ">"; printf('%6d',$pair['out_info']['size']/1000); echo " "; echo date("y/m/d H:i", $pair['out_info']['mtime']); echo "</a>"; echo "    "; ?></td>
    <td><?php echo "<a href="; echo $pair['err']; echo ">"; printf('%6d',$pair['out_info']['size']/1000); echo " "; echo date("y/m/d H:i", $pair['err_info']['mtime']); echo "</a>"; echo "    "; ?></td>

  </tr>
  <?php endforeach; ?>
  <?php else: ?>
  <tr>
    <td colspan="4" style="text-align:center;">No matching file pairs found</td>
  </tr>
  <?php endif; ?>
</table>
</pre>
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
