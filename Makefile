
PROJECT = setfont2
STAGING_DIR = $(HOME)/nanonote/openwrt-xburst/staging_dir
ROOT_DIR = $(STAGING_DIR)/target-mipsel_uClibc-0.9.30.1
#ROOT_DIR = ""
CC = $(STAGING_DIR)/toolchain-mipsel_gcc-4.3.3+cs_uClibc-0.9.30.1/usr/bin/mipsel-openwrt-linux-uclibc-gcc
STRIP = $(STAGING_DIR)/toolchain-mipsel_gcc-4.3.3+cs_uClibc-0.9.30.1/usr/mipsel-openwrt-linux-uclibc/bin/strip
#STRIP = strip
CFLAGS = -Wall -Os
INCLUDES = -I. -I$(ROOT_DIR)/usr/include
LIBS = -L$(ROOT_DIR)/usr/lib
PARTS = setfont2.o

.c.o:
	$(RM) $@
	$(CC) -c $(CFLAGS) $(DEFINES) $(INCLUDES) $*.c

.SILENT:

all: $(PROJECT)

$(PROJECT): $(PARTS)
	$(CC) -Wl,-rpath-link=$(ROOT_DIR)/usr/lib $(DEFINES) $(LIBS) -o $(PROJECT) $(PARTS)
	$(STRIP) $(PROJECT)

clean:
	rm -f *.o $(PROJECT)

