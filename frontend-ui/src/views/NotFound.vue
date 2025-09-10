<!-- Friendly fallback for unmatched routes -->

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="text-center pa-6" elevation="2">
          <v-card-title class="text-h4 mb-4 d-flex align-center justify-center">
            Not Found
            <v-icon icon="mdi-carrot" class="ml-2" color="orange"></v-icon>
          </v-card-title>

          <v-card-text class="text-body-1 mb-6">
            Sorry, this content was not found. Maybe you'd like to go back?
          </v-card-text>

          <v-card-actions class="justify-center">
            <BackButton />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import BackButton from '@/components/BackButton.vue'
</script>

<style scoped>
.v-card {
  border-radius: 16px;
}
</style>
