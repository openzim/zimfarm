<template>
  <v-dialog v-model="dialog" max-width="800px" persistent>
    <v-card>
      <v-card-title>
        <span class="text-h5">Create Worker</span>
      </v-card-title>
      <v-card-text>
        <v-form ref="form" v-model="valid" @submit.prevent="createWorker">
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="workerData.name"
                label="Worker Name"
                :rules="nameRules"
                required
                variant="outlined"
                density="compact"
                hint="Only lowercase alphanumeric and dashes."
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />
          <h3 class="text-h6 mb-2">SSH Key</h3>
          <SshKeyInput v-model="sshKeyData" />
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="error" variant="text" @click="close">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          :disabled="!isValid"
          :loading="saving"
          @click="createWorker"
        >
          Create
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import SshKeyInput from '@/components/SshKeyInput.vue'
import { useNotificationStore } from '@/stores/notification'
import { useWorkersStore } from '@/stores/workers'
import type { WorkerCreateSchema } from '@/types/workers'
import { computed, ref, watch } from 'vue'
import type { VForm } from 'vuetify/components'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'created'): void
}>()

const notificationStore = useNotificationStore()
const workersStore = useWorkersStore()

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const valid = ref(false)
const saving = ref(false)
const form = ref<VForm | null>(null)

const initialWorkerData = {
  name: '',
}

const workerData = ref({ ...initialWorkerData })
const sshKeyData = ref({ name: '', key: '' })

const nameRules = [
  (v: string) => !!v || 'Name is required',
  (v: string) => v.length > 2 || 'Name must be greater than 2 characters',
  (v: string) => /^[a-z0-9-]+$/.test(v) || 'Only lowercase alphanumeric and dashes allowed',
]

const isValid = computed(() => {
  return valid.value && sshKeyData.value.name.length > 0 && sshKeyData.value.key.length > 0
})

watch(dialog, async (newVal) => {
  if (newVal) {
    workerData.value = { ...initialWorkerData }
    sshKeyData.value = { name: '', key: '' }
    if (form.value) form.value.resetValidation()
  }
})

const close = () => {
  dialog.value = false
}

const createWorker = async () => {
  if (!isValid.value) return

  saving.value = true
  const payload: WorkerCreateSchema = {
    name: workerData.value.name,
    ssh_key: { key: sshKeyData.value.key },
  }

  const result = await workersStore.createWorker(payload)
  saving.value = false

  if (result) {
    notificationStore.showSuccess(`Worker ${workerData.value.name} created successfully!`)
    emit('created')
    close()
  } else {
    for (const error of workersStore.errors) {
      notificationStore.showError(error)
    }
  }
}
</script>
