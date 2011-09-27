#include <stdio.h>

#define CTX_BMARK "BMARK"
#define CTX_START "START"
#define CTX_ENDOK "ENDOK"
#define CTX_ENDER "ENDER"

#define CTX_LOG_BMARK(text) ctx_log_msg(__FUNCTION__, text, CTX_BMARK)
#define CTX_LOG_START(text) ctx_log_msg(__FUNCTION__, text, CTX_START)
#define CTX_LOG_ENDOK(text) ctx_log_msg(__FUNCTION__, text, CTX_ENDOK)
#define CTX_LOG_ENDER(text) ctx_log_msg(__FUNCTION__, text, CTX_ENDER)

extern FILE *context_log;

extern void ctx_set_log(const char *name);
extern void ctx_log_msg(const char *func, const char *text, const char *type);
