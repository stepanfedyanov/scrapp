import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '~/src/shared/api'

export const useBlogsStore = defineStore('blogs', () => {
  const blogs = ref([])
  const loading = ref(false)

  const fetchBlogs = async () => {
    loading.value = true
    try {
      const { data } = await api.get('/blogs/')
      blogs.value = data
    } finally {
      loading.value = false
    }
  }

  const createBlog = async (payload) => {
    const { data } = await api.post('/blogs/', payload)
    blogs.value.unshift(data)
    return data
  }

  const deleteBlog = async (uuid) => {
    await api.delete(`/blogs/${uuid}/`)
    blogs.value = blogs.value.filter((blog) => blog.uuid !== uuid)
  }

  const getById = (id) => blogs.value.find((blog) => blog.id === Number(id))

  const total = computed(() => blogs.value.length)

  return {
    blogs,
    loading,
    total,
    fetchBlogs,
    createBlog,
    deleteBlog,
    getById
  }
})
