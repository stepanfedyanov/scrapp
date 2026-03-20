import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { api } from '~/src/shared/api'


const operationToPath = {
  'write-structure': 'write-structure',
  'write-note': 'write-note',
  'write-new-chapter': 'write-new-chapter',
  'write-more-text': 'write-more-text',
}


export const useAiJobsStore = defineStore('ai-jobs', () => {
  const activeJob = ref(null)
  const isPolling = ref(false)
  let pollTimer = null

  const triggerJob = async (noteUuid, operation, sourceBlockUuid = null) => {
    const path = operationToPath[operation]
    if (!path) {
      throw new Error(`Unsupported AI operation: ${operation}`)
    }

    const payload = sourceBlockUuid ? { source_block_uuid: sourceBlockUuid } : {}
    const { data } = await api.post(`/notes/${noteUuid}/ai/${path}/`, payload)

    activeJob.value = {
      jobUuid: data.job_uuid,
      status: data.status,
      operationType: data.operation_type,
      noteUuid,
      sourceBlockUuid,
    }

    return activeJob.value
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    isPolling.value = false
  }

  const startPolling = (onSuccess, onError) => {
    if (!activeJob.value?.jobUuid) {
      throw new Error('No active AI job to poll.')
    }

    stopPolling()
    isPolling.value = true

    pollTimer = setInterval(async () => {
      try {
        const { data } = await api.get(
          `/ai-generation-jobs/${activeJob.value.jobUuid}/`
        )
        activeJob.value = {
          ...activeJob.value,
          status: data.status,
          details: data,
        }

        if (data.status === 'succeeded') {
          stopPolling()
          await onSuccess(data)
        }

        if (data.status === 'failed') {
          stopPolling()
          await onError(data)
        }
      } catch (error) {
        stopPolling()
        await onError({
          error_message: error.message,
          status: 'failed',
        })
      }
    }, 2000)
  }

  const clearActiveJob = () => {
    stopPolling()
    activeJob.value = null
  }

  const isProcessing = computed(() => {
    return ['queued', 'running'].includes(activeJob.value?.status)
  })

  return {
    activeJob,
    isPolling,
    isProcessing,
    triggerJob,
    startPolling,
    stopPolling,
    clearActiveJob,
  }
})