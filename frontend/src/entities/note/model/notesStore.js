import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '~/src/shared/api'

export const useNotesStore = defineStore('notes', () => {
  const notes = ref([])
  const loading = ref(false)

  const fetchNotes = async (blogUuid) => {
    loading.value = true
    try {
      const params = blogUuid ? { blog_uuid: blogUuid } : undefined
      const { data } = await api.get('/notes/', { params })
      notes.value = data
    } finally {
      loading.value = false
    }
  }

  const createNote = async (payload) => {
    const { data } = await api.post('/notes/', payload)
    notes.value.unshift(data)
    return data
  }

  const updateNote = async (uuid, payload) => {
    const { data } = await api.patch(`/notes/${uuid}/`, payload)
    const index = notes.value.findIndex((note) => note.uuid === uuid)
    if (index !== -1) notes.value[index] = data
    return data
  }

  const deleteNote = async (uuid) => {
    await api.delete(`/notes/${uuid}/`)
    notes.value = notes.value.filter((note) => note.uuid !== uuid)
  }

  const getById = (id) => notes.value.find((note) => note.id === Number(id))

  const total = computed(() => notes.value.length)

  return {
    notes,
    loading,
    total,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    getById
  }
})
