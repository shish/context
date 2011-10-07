
test: example example.py example.php example.pl Example.class
	./example
	./example.py
	./example.php
	./example.pl
	java Example

example: example.o context.o

Example.class: Example.java
	javac $<

# TODO: compile / run VB from the command line?

clean:
	rm -f *.o *.pyc *.ctxt *.class example
