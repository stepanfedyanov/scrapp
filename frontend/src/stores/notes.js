import { defineStore } from 'pinia'
import api from '../api/client'

export const useNotesStore = defineStore('notes', {
  state: () => ({
    notes: [],
    loading: false
  }),
  actions: {
    async fetchNotes() {
      this.loading = true
      try {
        const { data } = await api.get('/notes/')
        this.notes = data
      } finally {
        this.loading = false
      }
    },
    async createNote(payload) {
      const { data } = await api.post('/notes/', payload)
      this.notes.unshift(data)
      return data
    },
    async updateNote(id, payload) {
      const { data } = await api.patch(`/notes/${id}/`, payload)
      const index = this.notes.findIndex((note) => note.id === id)
      if (index !== -1) this.notes[index] = data
      return data
    },
    async deleteNote(id) {
      await api.delete(`/notes/${id}/`)
      this.notes = this.notes.filter((note) => note.id !== id)
    },
    getById(id) {
      return this.notes.find((note) => note.id === Number(id))
    }
  }
})
