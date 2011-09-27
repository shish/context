<?php
require_once "context.php";

function hello() {
	ctx_log_start("saying hello");
	printf("hello ");
	sleep(1);
	ctx_log_endok("saying hello");
}

function world() {
	ctx_log_start("saying world");
	printf("world\n");
	sleep(2);
	ctx_log_endok("saying world");
}

ctx_set_log("output.php.ctxt");
ctx_log_start("running program");
hello();
world();
ctx_log_endok("running program");
?>
