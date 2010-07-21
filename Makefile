
PROJECT = setfont2
STRIP = strip
CFLAGS = -Wall -Os
INCLUDES = -I. -I/usr/include
LIBS = -L/usr/lib
PARTS = setfont2.o

.c.o:
	$(RM) $@
	$(CC) -c $(CFLAGS) $(DEFINES) $(INCLUDES) $*.c

.SILENT:

all: $(PROJECT)

$(PROJECT): $(PARTS)
	$(CC) -Wl,-rpath-link=/usr/lib $(DEFINES) $(LIBS) -o $(PROJECT) $(PARTS)
	$(STRIP) $(PROJECT)

clean:
	rm -f *.o $(PROJECT)

