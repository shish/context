#include <stdio.h>
#include <unistd.h>

#include "context.h"

void hello() {
	CTX_LOG_START("starting to say hello");
	printf("hello ");
	sleep(1);
	CTX_LOG_ENDOK("starting to say hello");
}

void world() {
	CTX_LOG_START("starting to say world");
	printf("world\n");
	sleep(2);
	CTX_LOG_ENDOK("starting to say world");
}

int main(int argc, char *argv[]) {
	ctx_set_log("example.c.ctxt");
	CTX_LOG_START("running program");
	hello();
	world();
	CTX_LOG_ENDOK("running program");
	return 0;
}
