<?php
define("CTX_BMARK", "BMARK");
define("CTX_START", "START");
define("CTX_ENDOK", "ENDOK");
define("CTX_ENDER", "ENDER");

$_context_log = null;

function ctx_set_log($name) {
	global $_context_log;
	if($name) {
		$_context_log = fopen($name, "a");
	}
	else {
		$_context_log = null;
	}
}

function ctx_log_msg($func, $text, $type) {
	global $_context_log;
	if($_context_log) {
        fprintf(
			$_context_log,
			"%f %s %d %d %s %s %s\n",
            microtime(true), # returning a float is 5.0+
            php_uname('n'),  # gethostname() is 5.3+
			posix_getpid(),
			posix_getpid(), //gettid(),
            $type, $func, $text
        );
	}
}

function __get_func() {
	$stack = debug_backtrace();
	if(count($stack) < 3) {
		return "top-level";
	}
	$p = $stack[2];
	return $p['function'];
}

function ctx_log_bmark($text) {ctx_log_msg(__get_func(), $text, "BMARK");}
function ctx_log_start($text) {ctx_log_msg(__get_func(), $text, "START");}
function ctx_log_endok($text) {ctx_log_msg(__get_func(), $text, "ENDOK");}
function ctx_log_ender($text) {ctx_log_msg(__get_func(), $text, "ENDER");}
?>
