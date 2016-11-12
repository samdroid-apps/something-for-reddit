#include "./snudown/src/markdown.h"

typedef struct sd_markdown SDMarkdown;
typedef struct sd_callbacks SDCallbacks;
typedef struct buf SDBuf;

void snudown_callbacks_destroy (SDCallbacks * self) {
    // Maybe I need to do something for this?  I don't think I do, but
    // Vala wants this function to exist
}

void snudown_markdown_free (SDMarkdown * self) {
    sd_markdown_free (self);
}


void sd_markdown_render_sane (SDMarkdown *md,
                              struct buf *ob,
                              const uint8_t *document, size_t doc_size) {
    setvbuf (stderr, NULL, _IONBF, 0); //turn off buffering
    // Who came up with the idea of passing the object instance at the end?
    sd_markdown_render (ob, document, doc_size, md);
}

void snudown_buffer_free (SDBuf * self) {
    bufrelease (self);
}
