<template>
  <v-container class="h-100 d-flex flex-column pa-4" fluid>
    <div class="text-center mb-4">
      <v-img src="~/assets/FragHub_icon.png" max-width="80" class="mx-auto"></v-img>
      <h2 class="text-h5 font-weight-bold mt-2">Processing Analysis</h2>
    </div>

    <v-tabs v-model="activeView" color="primary" grow class="mb-4">
      <v-tab value="progress">
        <v-icon start>mdi-progress-clock</v-icon> Progress
      </v-tab>
      <v-tab value="report">
        <v-icon start>mdi-text-box-outline</v-icon> Report
      </v-tab>
    </v-tabs>

    <v-window v-model="activeView" class="flex-grow-1">

      <v-window-item value="progress" class="fill-height">
        <v-card class="pa-4 h-100 d-flex flex-column justify-center" elevation="2">
          <div class="text-h6 mb-2">{{ currentPrefix }}</div>

          <v-progress-linear
              v-model="progressPercent"
              height="30"
              color="primary"
              striped
              rounded
              class="mb-4"
          >
            <strong>{{ progressPercent.toFixed(1) }}%</strong>
          </v-progress-linear>

          <div class="d-flex justify-space-between text-body-2 text-grey-darken-1">
            <span>{{ processedItems }} / {{ totalItems }} {{ itemType }}</span>
            <span>Speed: {{ itemsPerSecond.toFixed(2) }} {{ itemType }}/s</span>
            <span>ETA: {{ formatTime(estimatedTimeLeft) }}</span>
          </div>
        </v-card>
      </v-window-item>

      <v-window-item value="report" class="fill-height">
        <v-card class="h-100 overflow-y-auto" elevation="2" id="report-container">
          <v-list density="compact">
            <v-list-item v-for="(log, i) in logs" :key="i" class="border-b">
              <template v-slot:prepend>
                <v-icon :color="log.type === 'error' ? 'error' : 'primary'" size="small">
                  {{ log.type === 'error' ? 'mdi-alert-circle' : 'mdi-chevron-right' }}
                </v-icon>
              </template>
              <v-list-item-title :class="log.type === 'error' ? 'text-red font-weight-bold' : ''">
                {{ log.text }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-window-item>
    </v-window>

    <div class="d-flex justify-center mt-6">
      <v-btn
          v-if="!isFinished"
          color="error"
          size="x-large"
          prepend-icon="mdi-stop-circle"
          @click="stopProcess"
          :loading="isStopping"
      >
        {{ isStopping ? 'STOPPING...' : 'STOP' }}
      </v-btn>
      <v-btn v-else color="success" size="x-large" prepend-icon="mdi-check" @click="finishProcess">
        FINISH
      </v-btn>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io } from "socket.io-client"
import { useState } from '#imports'

const socket = io("http://127.0.0.1:8000")
const activeView = ref('progress')
const isExecuting = useState('isExecuting')

// États de progression (Logique identique au ProgressBarWidget de PyQt)
const logs = ref([])
const progressValue = ref(0)
const totalItems = ref(100)
const currentPrefix = ref('Starting...')
const itemType = ref('items')
const startTime = ref(Date.now())
const isFinished = ref(false)
const isStopping = ref(false)

const progressPercent = computed(() => (totalItems.value > 0 ? (progressValue.value / totalItems.value) * 100 : 0))

// Calculs de performance (ETA, Vitesse)
const processedItems = computed(() => progressValue.value)
const itemsPerSecond = computed(() => {
  const elapsed = (Date.now() - startTime.value) / 1000
  return elapsed > 0 ? progressValue.value / elapsed : 0
})
const estimatedTimeLeft = computed(() => {
  const remaining = totalItems.value - progressValue.value
  return itemsPerSecond.value > 0 ? remaining / itemsPerSecond.value : 0
})

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0')
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0')
  const s = Math.floor(seconds % 60).toString().padStart(2, '0')
  return `${h}:${m}:${s}`
}

onMounted(() => {
  startTime.value = Date.now()

  socket.on('progress', (val) => { progressValue.value = val })
  socket.on('total_items', (val) => { totalItems.value = val })
  socket.on('prefix', (val) => { currentPrefix.value = val })
  socket.on('item_type', (val) => { itemType.value = val })

  socket.on('step', (val) => {
    logs.value.push({ text: val, type: 'info' })
  })

  socket.on('deletion', (val) => {
    logs.value.push({ text: val, type: 'error' })
  })

  socket.on('completion', (val) => {
    logs.value.push({ text: val, type: 'info' })
    isFinished.value = true
  })
})

const stopProcess = () => {
  isStopping.value = true
  socket.emit('stop_request') // Backend devra gérer cet arrêt
}

const finishProcess = () => {
  isExecuting.value = false
}

onUnmounted(() => { socket.disconnect() })
</script>

<style scoped>
.border-b { border-bottom: 1px solid #e0e0e0; }
#report-container { background: #f9f9f9; }
</style>