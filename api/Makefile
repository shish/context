
test: output.py-decorator.ctxt output.py-profile.ctxt \
	output.c.ctxt \
	output.php.ctxt \
	output.pl.ctxt \
	output.java.ctxt output.java-profile.ctxt

output.py-decorator.ctxt: example-decorator.py context.py
	./example-decorator.py

output.py-profile.ctxt: example-decorator.py context.py
	./example-profile.py

output.c.ctxt:      example.c     context.c
	gcc example.c context.c -o example
	./example

output.php.ctxt:    example.php   context.php
	./example.php

output.pl.ctxt:     example.pl    context.pm
	./example.pl

output.java.ctxt:   Example.class Context.class
	java Example

output.java-profile.ctxt: ExampleProfile.class libcontext.so
	java -agentpath:./libcontext.so=output.java-profile.ctxt,ExampleProfile ExampleProfile




%.class: %.java
	javac $<

# TODO: compile / run VB from the command line?

clean:
	rm -f *.o *.so *.pyc *.ctxt *.class example

libcontext.so: java-profiler.c
	gcc -fPIC -I /usr/lib/jvm/java-6-openjdk/include/ -shared -Wl,-soname,libcontext.so.1 -o libcontext.so java-profiler.c
