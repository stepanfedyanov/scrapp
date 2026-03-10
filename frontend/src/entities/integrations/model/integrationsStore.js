import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '~/src/shared/api/client'

export const useIntegrationsStore = defineStore('integrations', () => {
  // State
  const definitions = ref([])
  const integrations = ref([])
  const publishTargets = ref([])
  const publishLogs = ref([])
  const loading = ref(false)
  const currentIntegrationId = ref(null)
  const currentPublishTargetId = ref(null)
  const error = ref(null)

  // Computed
  const getDefinitionByCode = computed(() => (code) => {
    return definitions.value.find(def => def.code === code)
  })

  const getIntegrationById = computed(() => (id) => {
    return integrations.value.find(int => int.id === id)
  })

  const getPublishTargetsByContent = computed(() => (contentTypeId, objectId) => {
    return publishTargets.value.filter(
      pt => pt.content_type_id === contentTypeId && pt.object_id === objectId
    )
  })

  // Actions - Integration Definitions
  const fetchDefinitions = async () => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/integration-definitions/')
      definitions.value = Array.isArray(data) ? data : data.results || []
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchDefinitionById = async (id) => {
    try {
      const { data } = await api.get(`/integration-definitions/${id}/`)
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // Actions - Integrations (User's instances)
  const fetchIntegrations = async (filters = {}) => {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          params.append(key, value)
        }
      })
      const url = `/integrations/${params.toString() ? '?' + params.toString() : ''}`
      const { data } = await api.get(url)
      integrations.value = Array.isArray(data) ? data : data.results || []
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createIntegration = async (payload) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/integrations/', payload)
      integrations.value.unshift(data)
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateIntegration = async (id, payload) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.patch(`/integrations/${id}/`, payload)
      const index = integrations.value.findIndex(int => int.id === id)
      if (index !== -1) {
        integrations.value[index] = data
      }
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteIntegration = async (id) => {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/integrations/${id}/`)
      integrations.value = integrations.value.filter(int => int.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Actions - Publish Targets
  const fetchPublishTargets = async (filters = {}) => {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          params.append(key, value)
        }
      })
      const url = `/publish-targets/${params.toString() ? '?' + params.toString() : ''}`
      const { data } = await api.get(url)
      publishTargets.value = Array.isArray(data) ? data : data.results || []
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createPublishTarget = async (payload) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/publish-targets/', payload)
      publishTargets.value.unshift(data)
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updatePublishTarget = async (id, payload) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.patch(`/publish-targets/${id}/`, payload)
      const index = publishTargets.value.findIndex(pt => pt.id === id)
      if (index !== -1) {
        publishTargets.value[index] = data
      }
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deletePublishTarget = async (id) => {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/publish-targets/${id}/`)
      publishTargets.value = publishTargets.value.filter(pt => pt.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const publishTarget = async (publishTargetId) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post(`/publish-targets/${publishTargetId}/publish/`)
      const index = publishTargets.value.findIndex(pt => pt.id === publishTargetId)
      if (index !== -1) {
        publishTargets.value[index] = data
      }
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Actions - Publish Logs
  const fetchPublishLogs = async (publishTargetId, params = {}) => {
    loading.value = true
    error.value = null
    try {
      const url = new URL(`/publish-targets/${publishTargetId}/logs/`, 'http://dummy')
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, value)
        }
      })
      const { data } = await api.get(url.pathname + url.search)
      publishLogs.value = Array.isArray(data) ? data : data.results || []
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    definitions,
    integrations,
    publishTargets,
    publishLogs,
    loading,
    error,
    currentIntegrationId,
    currentPublishTargetId,

    // Computed
    getDefinitionByCode,
    getIntegrationById,
    getPublishTargetsByContent,

    // Methods
    fetchDefinitions,
    fetchDefinitionById,
    fetchIntegrations,
    createIntegration,
    updateIntegration,
    deleteIntegration,
    fetchPublishTargets,
    createPublishTarget,
    updatePublishTarget,
    deletePublishTarget,
    publishTarget,
    fetchPublishLogs
  }
})
