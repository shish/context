#include <stdio.h>
#include <time.h>
#include <sys/timeb.h>
#include <unistd.h>

#include "context.h"

FILE *context_log;

void ctx_set_log(const char *name) {
	context_log = fopen(name, "a");
}

void ctx_log_msg(const char *func, const char *text, const char *type) {
	if(context_log) {
		struct timeb tmb;
		char hostname[256];

		ftime(&tmb);
		gethostname(hostname, 256);

        fprintf(
			context_log,
			"%ld.%d %s %d %d %s %s %s\n",
            tmb.time, tmb.millitm,
            hostname,
			getpid(),
			0, //gettid(),
            type, func, text
        );
	}
}
