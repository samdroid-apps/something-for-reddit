/*
 * Copyright (C) 2016, Sam Parkinson
 * The following license matches markdown.h from github.com/reddit/snudown
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

[CCode (cheader_filename = "snudown.h", cprefix = "")]
namespace Snudown {
    [CCode (cprefix = "MDKA_")]
    enum AutolinkType {
        NOT_AUTOLINK,
        NORMAL,
        EMAIL
    }

    [Flags]
    [CCode (cprefix = "MKD_TABLE_")]
    enum TableFlags {
        ALIGN_L,
        ALIGN_R,
        ALIGN_CENTER,
        ALIGNMASK,
        HEADER
    }

    [Flags]
    [CCode (cprefix = "MKDEXT_")]
    enum mkd_extensions {
        NO_INTRA_EMPHASIS,
        TABLES,
        FENCED_CODE,
        AUTOLINK,
        STRIKETHROUGH,
        SPACE_HEADERS,
        SUPERSCRIPT,
        LAX_SPACING,
        NO_EMAIL_AUTOLINK
    }

    [CCode (cname = "buf", has_type_id = false, destroy_function = "bufreset")]
    public struct Buffer {
        [CCode (array_length_name = "size")]
	char[] data;
    }

    namespace CallbackTypes {
        /* blockcode, blockquote, blockhtml, paragraph, normal_text */
        [CCode]
        public delegate void block (Buffer ob, Buffer text);

        [CCode]
        public delegate void header (Buffer ob, Buffer text, int level);
        [CCode]
        public delegate void hrule (Buffer ob);

        /* list, listitem */
        [CCode]
        public delegate void list (Buffer ob, Buffer text, int flags);
    }

    [CCode (cname = "SDCallbacks")]
    struct Callbacks {
        [CCode]
        public CallbackTypes.block? blockcode;
        [CCode]
        public CallbackTypes.block? blockquote;
        [CCode]
        public CallbackTypes.block? blockhtml;
        [CCode]
        public CallbackTypes.header? header;
        [CCode]
        public CallbackTypes.hrule? hrule;
        [CCode]
        public CallbackTypes.list? list;
        [CCode]
        public CallbackTypes.list? listitem;
        [CCode]
        public CallbackTypes.block? paragraph;
        /*
            void (*table)(struct buf *ob, const struct buf *header, const struct buf *body, void *opaque);
            void (*table_row)(struct buf *ob, const struct buf *text, void *opaque);
            void (*table_cell)(struct buf *ob, const struct buf *text, int flags, void *opaque, int col_span);
        */

        /* span level callbacks - NULL or return 0 prints the span verbatim */
        /*int (*autolink)(struct buf *ob, const struct buf *link, enum mkd_autolink type, void *opaque);
        int (*codespan)(struct buf *ob, const struct buf *text, void *opaque);
        int (*double_emphasis)(struct buf *ob, const struct buf *text, void *opaque);
        int (*emphasis)(struct buf *ob, const struct buf *text, void *opaque);
        int (*image)(struct buf *ob, const struct buf *link, const struct buf *title, const struct buf *alt, void *opaque);
        int (*linebreak)(struct buf *ob, void *opaque);
        int (*link)(struct buf *ob, const struct buf *link, const struct buf *title, const struct buf *content, void *opaque);
        int (*raw_html_tag)(struct buf *ob, const struct buf *tag, void *opaque);
        int (*triple_emphasis)(struct buf *ob, const struct buf *text, void *opaque);
        int (*strikethrough)(struct buf *ob, const struct buf *text, void *opaque);
        int (*superscript)(struct buf *ob, const struct buf *text, void *opaque);*/

        /* low level callbacks - NULL copies input directly into the output */
        /*void (*entity)(struct buf *ob, const struct buf *entity, void *opaque);
        void (*normal_text)(struct buf *ob, const struct buf *text, void *opaque);*/

        /* header and footer */
        /*void (*doc_header)(struct buf *ob, void *opaque);
        void (*doc_footer)(struct buf *ob, void *opaque);*/
    }

    [Compact]
    [CCode (cname = "SDMarkdown",
            free_function = "sd_markdown_free",
            has_type_id = false)]
    class Markdown {
        [CCode (cname = "sd_markdown_new")]
        public Markdown (
            uint extentions, 
            size_t max_nesting,
            size_t max_table_cols,
            Callbacks callbacks,
            void *opaque
        );

        [CCode (cname = "sd_markdown_render")]
        public void render (
            Buffer ob,
            char[] document,
            Markdown md
        );
    }
}
