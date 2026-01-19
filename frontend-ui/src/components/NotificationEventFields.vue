<template>
  <v-row v-if="modelValue" dense>
    <v-col cols="12">
      <h3 class="text-subtitle-1">{{ eventTitle }}</h3>
    </v-col>
    <v-col cols="12" sm="4">
      <v-combobox
        :model-value="modelValue.mailgun"
        :rules="mailgunRules"
        :delimiters="[',', ' ']"
        @update:model-value="updateMailgun"
        label="Mailgun Recipients"
        hint="Email addresses to notify via Mailgun"
        multiple
        chips
        closable-chips
        density="compact"
        variant="outlined"
        persistent-hint
        clearable
      />
    </v-col>
    <v-col cols="12" sm="4">
      <v-combobox
        :model-value="modelValue.webhook"
        :rules="webhookRules"
        :delimiters="[',', ' ']"
        @update:model-value="updateWebhook"
        label="Webhook URLs"
        hint="Webhook URLs to notify"
        multiple
        chips
        closable-chips
        density="compact"
        variant="outlined"
        persistent-hint
        clearable
      />
    </v-col>
    <v-col cols="12" sm="4">
      <v-combobox
        :model-value="modelValue.slack"
        :rules="slackRules"
        :delimiters="[',', ' ']"
        @update:model-value="updateSlack"
        label="Slack Channels"
        hint="Slack channels to notify"
        multiple
        chips
        closable-chips
        density="compact"
        variant="outlined"
        persistent-hint
        clearable
      />
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import type { EventNotification } from '@/types/schedule'

interface Props {
  modelValue: EventNotification | null
  eventTitle: string
}

interface Emits {
  (e: 'update:modelValue', value: EventNotification): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Validation rules
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const urlRegex = /^https?:\/\/.+/
const slackRegex = /^[#|@].+$/

const mailgunRules = [
  (value: string[] | null) => {
    if (!value || value.length === 0) return true
    const invalidEmails = value.filter((email) => !emailRegex.test(email))
    if (invalidEmails.length > 0) {
      return `Invalid email address(es): ${invalidEmails.join(', ')}`
    }
    return true
  },
]

const webhookRules = [
  (value: string[] | null) => {
    if (!value || value.length === 0) return true
    const invalidUrls = value.filter((url) => !urlRegex.test(url))
    if (invalidUrls.length > 0) {
      return `Invalid URL(s): ${invalidUrls.join(', ')}`
    }
    return true
  },
]

const slackRules = [
  (value: string[] | null) => {
    if (!value || value.length === 0) return true
    const invalidChannels = value.filter((channel) => !slackRegex.test(channel))
    if (invalidChannels.length > 0) {
      return `Invalid Slack channel(s) - must start with # or @: ${invalidChannels.join(', ')}`
    }
    return true
  },
]

const updateMailgun = (mailgun: string[] | null) => {
  if (props.modelValue) {
    emit('update:modelValue', {
      ...props.modelValue,
      mailgun,
    })
  }
}

const updateWebhook = (webhook: string[] | null) => {
  if (props.modelValue) {
    emit('update:modelValue', {
      ...props.modelValue,
      webhook,
    })
  }
}

const updateSlack = (slack: string[] | null) => {
  if (props.modelValue) {
    emit('update:modelValue', {
      ...props.modelValue,
      slack,
    })
  }
}
</script>
