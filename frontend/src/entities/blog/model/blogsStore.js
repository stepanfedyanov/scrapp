import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '~/src/shared/api'

export const useBlogsStore = defineStore('blogs', () => {
  const blogs = ref([])
  const loading = ref(false)
  const blogDefaults = ref({}) // Map: blog_uuid -> array of defaults

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

  // Blog Default Integrations
  const fetchBlogDefaults = async (blogUuid) => {
    loading.value = true
    try {
      const { data } = await api.get('/blog-default-integrations/', {
        params: { blog_uuid: blogUuid }
      })
      blogDefaults.value[blogUuid] = data
      return data
    } finally {
      loading.value = false
    }
  }

  const createBlogDefault = async (blogUuid, payload) => {
    const { data } = await api.post('/blog-default-integrations/', {
      ...payload,
      blog_uuid: blogUuid
    })
    if (!blogDefaults.value[blogUuid]) {
      blogDefaults.value[blogUuid] = []
    }
    blogDefaults.value[blogUuid].push(data)
    return data
  }

  const updateBlogDefault = async (defaultId, payload) => {
    const { data } = await api.patch(`/blog-default-integrations/${defaultId}/`, payload)
    // Update in cache
    Object.keys(blogDefaults.value).forEach(blogUuid => {
      const idx = blogDefaults.value[blogUuid].findIndex(d => d.id === defaultId)
      if (idx >= 0) {
        blogDefaults.value[blogUuid][idx] = data
      }
    })
    return data
  }

  const deleteBlogDefault = async (defaultId) => {
    await api.delete(`/blog-default-integrations/${defaultId}/`)
    // Remove from cache
    Object.keys(blogDefaults.value).forEach(blogUuid => {
      blogDefaults.value[blogUuid] = blogDefaults.value[blogUuid].filter(d => d.id !== defaultId)
    })
  }

  const getBlogDefaults = (blogUuid) => {
    return blogDefaults.value[blogUuid] || []
  }

  return {
    blogs,
    loading,
    total,
    fetchBlogs,
    createBlog,
    deleteBlog,
    getById,
    // Blog defaults
    blogDefaults,
    fetchBlogDefaults,
    createBlogDefault,
    updateBlogDefault,
    deleteBlogDefault,
    getBlogDefaults,
  }
})
