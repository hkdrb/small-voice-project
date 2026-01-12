'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { Markdown } from 'tiptap-markdown';
import {
  Bold,
  Italic,
  Strikethrough,
  List,
  ListOrdered,
  Quote,
  Code,
  Link as LinkIcon,
  Unlink,
  Highlighter
} from 'lucide-react';
import { useEffect } from 'react';

interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  className?: string;
  minHeight?: string;
  editable?: boolean;
}

const MenuBar = ({ editor }: { editor: any }) => {
  if (!editor) {
    return null;
  }

  const setLink = () => {
    const previousUrl = editor.getAttributes('link').href;
    const url = window.prompt('URL', previousUrl);

    // cancelled
    if (url === null) {
      return;
    }

    // empty
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }

    // update link
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  };

  return (
    <div className="flex flex-wrap gap-1 p-2 border-t border-slate-200 bg-slate-50/50 rounded-b-xl">
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        disabled={!editor.can().chain().focus().toggleBold().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('bold') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Bold"
      >
        <Bold className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        disabled={!editor.can().chain().focus().toggleItalic().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('italic') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Italic"
      >
        <Italic className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleStrike().run()}
        disabled={!editor.can().chain().focus().toggleStrike().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('strike') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Strikethrough"
      >
        <Strikethrough className="w-4 h-4" />
      </button>

      <div className="w-[1px] h-6 bg-slate-300 mx-1 self-center"></div>

      <button
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('bulletList') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Bullet List"
      >
        <List className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('orderedList') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Ordered List"
      >
        <ListOrdered className="w-4 h-4" />
      </button>

      <div className="w-[1px] h-6 bg-slate-300 mx-1 self-center"></div>

      <button
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('blockquote') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Blockquote"
      >
        <Quote className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('codeBlock') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Code Block"
      >
        <Code className="w-4 h-4" />
      </button>

      <div className="w-[1px] h-6 bg-slate-300 mx-1 self-center"></div>

      <button
        onClick={setLink}
        className={`p-1.5 rounded hover:bg-slate-200 transition-colors ${editor.isActive('link') ? 'bg-slate-200 text-slate-800' : 'text-slate-500'}`}
        title="Link"
      >
        <LinkIcon className="w-4 h-4" />
      </button>
      {editor.isActive('link') && (
        <button
          onClick={() => editor.chain().focus().unsetLink().run()}
          className="p-1.5 rounded hover:bg-slate-200 transition-colors text-slate-500"
          title="Unlink"
        >
          <Unlink className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default function RichTextEditor({
  content,
  onChange,
  placeholder = 'MarkDown形式で入力できます...',
  className = '',
  minHeight = '150px',
  editable = true
}: RichTextEditorProps) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Link.configure({
        openOnClick: false,
      }),
      Placeholder.configure({
        placeholder: placeholder,
      }),
      Markdown.configure({
        html: false,
        transformPastedText: true,
        transformCopiedText: true,
      }),
    ],
    content: content,
    editable: editable,
    onUpdate: ({ editor }) => {
      // Get markdown content
      // @ts-ignore
      const markdownMap = editor.storage.markdown.getMarkdown();
      onChange(markdownMap);
    },
    editorProps: {
      attributes: {
        class: `prose prose-sm max-w-none focus:outline-none p-4 min-h-[${minHeight}]`,
      },
    },
  });

  // Update content if changed from outside
  useEffect(() => {
    // @ts-ignore
    if (editor && content !== editor.storage.markdown.getMarkdown()) {
      // Only update if content is drastically different to avoid cursor jumps
      // This is a simple check, ideally we'd compare more robustly
      if (content === '') {
        editor.commands.setContent(content);
      }
    }
  }, [content, editor]);

  return (
    <div className={`border border-slate-200 rounded-xl overflow-hidden bg-white ${className} focus-within:ring-2 focus-within:ring-sage-primary/20 focus-within:border-sage-primary transition-all`}>
      <EditorContent editor={editor} style={{ minHeight }} />
      <MenuBar editor={editor} />

      <style jsx global>{`
         .ProseMirror p.is-editor-empty:first-child::before {
           color: #adb5bd;
           content: attr(data-placeholder);
           float: left;
           height: 0;
           pointer-events: none;
         }
         
         .ProseMirror blockquote {
           border-left: 3px solid #cbd5e1;
           padding-left: 1rem;
           margin-left: 0;
           color: #64748b;
         }
 
         .ProseMirror code {
             background-color: #f1f5f9;
             padding: 0.125rem 0.25rem;
             border-radius: 0.25rem;
             color: #ef4444;
             font-size: 0.875em;
         }
 
         .ProseMirror pre {
             background: #0d0d0d;
             color: #fff;
             font-family: 'JetBrainsMono', monospace;
             padding: 0.75rem 1rem;
             border-radius: 0.5rem;
         }
         
         .ProseMirror pre code {
             color: inherit;
             padding: 0;
             background: none;
             font-size: 0.8rem;
         }
         
         .ProseMirror ul {
             list-style-type: disc;
             padding-left: 1.5em;
         }
 
         .ProseMirror ol {
             list-style-type: decimal;
             padding-left: 1.5em;
         }
 
         .ProseMirror a {
             color: #0369a1;
             text-decoration: underline;
         }
       `}</style>
    </div>
  );
}
