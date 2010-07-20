/*
 * Copyright (C) 2010 Neil Stockbridge
 * LICENSE: GPL
 */

#include <fcntl.h>
#include <errno.h>
#include <linux/kd.h>
#include <malloc.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>


typedef  char  bool;
#define  false  0
#define  true   1


// This console magic is gratefully pinched from consolechars
int is_a_console(int fd)
{
  char arg;

  arg = 0;
  return (ioctl(fd, KDGKBTYPE, &arg) == 0
    && ((arg == KB_101) || (arg == KB_84)));
}

static int open_a_console(char *fnam)
{
  int fd;

  /* try read-only */
  fd = open(fnam, O_RDWR);

  /* if failed, try read-only */
  if (fd < 0 && errno == EACCES)
      fd = open(fnam, O_RDONLY);

  /* if failed, try write-only */
  if (fd < 0 && errno == EACCES)
      fd = open(fnam, O_WRONLY);

  /* if failed, fail */
  if (fd < 0)
      return -1;

  /* if not a console, fail */
  if (! is_a_console(fd))
    {
      close(fd);
      return -1;
    }

  /* success */
  return fd;
}

int get_console_fd()
{
  int fd;

  fd = open_a_console("/dev/tty");
  if (fd >= 0)
    return fd;

  fd = open_a_console("/dev/tty0");
  if (fd >= 0)
    return fd;

  fd = open_a_console("/dev/console");
  if (fd >= 0)
    return fd;

  for (fd = 0; fd < 3; fd++)
    if (is_a_console(fd))
      return fd;

  fprintf(stderr,
    "Couldnt get a file descriptor referring to the console\n");
  return -1;
}


typedef enum
{
  EXPECTING_FINGERPRINT,
  EXPECTING_DIMENSIONS,
  EXPECTING_MAXVAL,
}
ParserState;


typedef struct
{
  uint16_t  width;
  uint16_t  height;
  uint16_t  maximum_value;
  uint8_t   *data;
}
Image;


// Loads a PNM P6 image ( 24-bit colour with binary pixel data).
// Returns 0 if the image was successfully loaded, non-zero on error.  On
// error, the "error" pointer will refer to a human-readable description of
// what was wrong.
// The fields in the "image" struct may be in an undefined state on error.
// The "data" field of the image must be passed to free() when no longer
// required.
//
int load_pnm_p6( char *path_to_file, Image *image, char **error)
{
  /* EXAMPLE PNM P6 HEADER:
P6
# CREATOR: GIMP PNM Filter Version 1.1
128 24
255
<binary data>
  */
  FILE  *f = fopen( path_to_file, "r");
  if ( NULL == f) {
    *error = "Could not open file";
    return 1;  // TODO - proper error code
  }

  char         line_store[ 80];
  ParserState  state          = EXPECTING_FINGERPRINT;
  bool         reading_header = true;
  int          outcome        = 1;  // indicating an error

  while ( reading_header)
  {
    char *line = fgets( line_store, sizeof(line_store), f);

    if ( NULL == line)
    {
      *error = "Premature end of file";
      goto tidy_up;
    }

    switch ( state)
    {
      case EXPECTING_FINGERPRINT:
        // Check that the file is in fact a P6 PNM file
        if ( 0 == strcmp("P6\n", line)) {
          state = EXPECTING_DIMENSIONS;
        }
        else {
          *error = "Not a PNM P6 file";
          goto tidy_up;
        }
        break;
      case EXPECTING_DIMENSIONS:
        // If this line does NOT contain a comment..
        if ( line[ 0] != '#')
        {
          // Try to get the dimensions of the image from the line
          int  count = sscanf( line, "%hu %hu\n", &image->width, &image->height);
          if ( count != 2) {
            *error = "Bad dimensions line";
            goto tidy_up;
          }
          state = EXPECTING_MAXVAL;
        }
        break;
      case EXPECTING_MAXVAL:
      {
        // Try to get the maximum pixel value in the image from the line
        int  count = sscanf( line, "%hu\n", &image->maximum_value);
        if ( count != 1) {
          *error = "Bad maxval line";
          goto tidy_up;
        }
        // The binary data follows the Depth line
        reading_header = false;
      }
    }
  }

  image->data = malloc( 3 * image->width * image->height);
  size_t  rows_read = fread( image->data, 3 * image->width, image->height, f);
  if ( rows_read != image->height)
  {
    *error = "Some data is missing";
    goto tidy_up;
  }

  // Indicate that no error occurred
  outcome = 0;

 tidy_up:
  fclose( f);

  return outcome;
}


int main( int argc, char **argv)
{
  if ( argc != 2)
  {
    fprintf( stderr, "Use: %s path-to-glyph-sheet.pnm\n", argv[0]);
    exit( 1);
  }

  // Load the glyph sheet from the PNM file
  Image  image;
  char   *error;
  int    outcome = load_pnm_p6( argv[1], &image, &error);
  if ( outcome != 0)
  {
    fprintf( stderr, "Could not load glyph sheet: %s\n", error);
    exit( 1);
  }

  bool  should_emit_data = false;

  // The glyph sheet is expected to have 8 rows of 32 glyphs.  The image
  // dimensions will be used to determine the glyph cell dimensions.
  uint8_t  pixels_across_glyph  = image.width / 32;
  uint8_t  pixels_down_glyph = image.height / 8;
  uint8_t  bytes_across_glyph = 4 * pixels_across_glyph;
  uint8_t  bytes_per_glyph = bytes_across_glyph * pixels_down_glyph;

  uint16_t  charcount = 256;
  unsigned char  data[ bytes_per_glyph * charcount];

  // Initialize the kernel glyph sheet so that unused pixels are empty
  memset( data, 0x00, sizeof(data));

  int  ch, y, x;
  for ( ch = 0; ch < 256; ++ch)
  {
    // Work out the row number on the glyph sheet of the glyph for "ch"
    // There are 8 rows of 32 glyphs on the image
    uint8_t  glyph_sheet_row    = ch / 32;
    uint8_t  glyph_sheet_column = ch % 32;
    uint8_t  top_edge_of_glyph  = pixels_down_glyph * glyph_sheet_row;
    uint8_t  left_edge_of_glyph = pixels_across_glyph * glyph_sheet_column;

    if ( should_emit_data) {
      printf("%c\n", ch);
    }

    for ( y = 0;  y < pixels_down_glyph;  ++ y)
    {
      uint8_t  *file_glyph_row = &image.data[ 3 * ( image.width * ( top_edge_of_glyph + y) + left_edge_of_glyph)];
      uint8_t  *kernel_glyph_row = &data[ bytes_per_glyph * ch + bytes_across_glyph * y];
      if ( bytes_per_glyph * ch + bytes_across_glyph * y + bytes_across_glyph <= sizeof(data))
      {
        // Copy the row of pixels from the file sheet to the kernel sheet
        for ( x = 0;  x < pixels_across_glyph;  ++ x)
        {
          kernel_glyph_row[ 4*x + 0] = file_glyph_row[ 3*x + 2];
          kernel_glyph_row[ 4*x + 1] = file_glyph_row[ 3*x + 1];
          kernel_glyph_row[ 4*x + 2] = file_glyph_row[ 3*x + 0];
          if ( should_emit_data) {
            uint8_t  *row = kernel_glyph_row + 4*x;
            printf("%02hx,%02hx,%02hx,%02hx ", row[0], row[1], row[2], row[3]);
          }
        }
        if ( should_emit_data) {
          printf("\n");
        }
      }
      else {
        fprintf( stderr, "Shit\n");
        goto tidy_up;
      }
    }
  }

  // Leave a fingerprint of this non-standard font so the kernel can recognise
  // it as such
  *(uint32_t*)data = 0x6a127efd;

  struct console_font_op  request = { op:        KD_FONT_OP_SET,
                                      width:     pixels_across_glyph,
                                      height:    pixels_down_glyph,
                                      charcount: 256,
                                      data:      data,
                                    };

  if ( ioctl( get_console_fd(), KDFONTOP, &request)) {
    perror("Bugger");
  }

  tidy_up:
  free( image.data);

  return 0;
}

