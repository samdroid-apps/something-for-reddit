#include "./snudown/src/markdown.h"

typedef struct sd_markdown SDMarkdown;
typedef struct sd_callbacks SDCallbacks;

void snudown_callbacks_destroy (SDCallbacks * self) {
    // Maybe I need to do something for this?  I don't think I do, but
    // Vala wants this function to exist
}

void snudown_markdown_free (SDMarkdown * self) {
    sd_markdown_free (self);
}
