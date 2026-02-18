<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { watch, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'delete'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({ heading: false }),
    Link.configure({ openOnClick: false }),
    Placeholder.configure({ placeholder: props.placeholder || t('blocks.writeSomething') }),
  ],
  editorProps: {
    attributes: { class: 'tiptap-editor' },
  },
  onUpdate({ editor }) {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(
  () => props.modelValue,
  (val) => {
    if (editor.value && editor.value.getHTML() !== val) {
      editor.value.commands.setContent(val || '', false)
    }
  },
)

onBeforeUnmount(() => {
  editor.value?.destroy()
})

function setLink() {
  const url = window.prompt('URL', editor.value?.getAttributes('link').href ?? '')
  if (url === null) return
  if (url === '') {
    editor.value?.chain().focus().extendMarkRange('link').unsetLink().run()
  } else {
    editor.value?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }
}
</script>

<template>
  <div class="block-text">
    <div v-if="editor" class="toolbar">
      <button
        v-for="item in [
          { action: 'toggleBold', label: 'B', name: 'bold', title: $t('blocks.toolbar.bold') },
          { action: 'toggleItalic', label: 'I', name: 'italic', title: $t('blocks.toolbar.italic'), italic: true },
          { action: 'toggleCode', label: '</>', name: 'code', title: $t('blocks.toolbar.code') },
          { action: 'toggleBlockquote', label: '❝', name: 'blockquote', title: $t('blocks.toolbar.quote') },
          { action: 'toggleBulletList', label: '•—', name: 'bulletList', title: $t('blocks.toolbar.bulletList') },
          { action: 'toggleOrderedList', label: '1.', name: 'orderedList', title: $t('blocks.toolbar.orderedList') },
        ]"
        :key="item.name"
        type="button"
        :title="item.title"
        :class="['toolbar-btn', { active: editor.isActive(item.name) }]"
        @click="editor.chain().focus()[item.action]().run()"
      >{{ item.label }}</button>

      <button
        type="button"
        :title="$t('blocks.toolbar.link')"
        :class="['toolbar-btn', { active: editor.isActive('link') }]"
        @click="setLink"
      >🔗</button>
    </div>

    <EditorContent :editor="editor" />

    <button class="delete-btn" type="button" :title="$t('blocks.deleteBlock')" @click="emit('delete')">
      <i class="pi pi-trash" />
    </button>
  </div>
</template>

<style scoped lang="scss">
.block-text {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: visible;

  &:hover .delete-btn {
    opacity: 1;
  }
}

.toolbar {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
  padding: 6px 8px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 8px 8px 0 0;
}

.toolbar-btn {
  padding: 2px 7px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  line-height: 1.6;
  color: #374151;
  transition: background 0.15s, border-color 0.15s;

  &:hover {
    background: #e5e7eb;
    border-color: #d1d5db;
  }

  &.active {
    background: #dbeafe;
    border-color: #93c5fd;
    color: #1d4ed8;
  }
}

.delete-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s, border-color 0.15s;
  padding: 3px 6px;

  &:hover {
    color: #ef4444;
    border-color: #fca5a5;
  }
}

:deep(.tiptap-editor) {
  padding: 10px 12px;
  min-height: 80px;
  outline: none;
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;

  p { margin: 0 0 8px 0; }
  p:last-child { margin-bottom: 0; }

  strong { font-weight: 600; }

  em { font-style: italic; }

  code {
    background: #f3f4f6;
    border-radius: 3px;
    padding: 1px 4px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }

  pre {
    background: #1e293b;
    color: #e2e8f0;
    border-radius: 6px;
    padding: 12px 16px;
    overflow-x: auto;
    code { background: none; color: inherit; padding: 0; }
  }

  blockquote {
    border-left: 3px solid #6366f1;
    margin: 8px 0;
    padding-left: 14px;
    color: #6b7280;
    font-style: italic;
  }

  ul { list-style: disc; padding-left: 22px; margin: 0 0 8px; }
  ol { list-style: decimal; padding-left: 22px; margin: 0 0 8px; }
  li { margin-bottom: 2px; }

  a {
    color: #6366f1;
    text-decoration: underline;
    cursor: pointer;
  }

  p.is-editor-empty:first-child::before {
    content: attr(data-placeholder);
    color: #9ca3af;
    pointer-events: none;
    float: left;
    height: 0;
  }
}
</style>
