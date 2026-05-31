<template>
  <v-container class="h-100 d-flex flex-column pa-4 overflow-hidden" fluid>
    <div class="text-center mb-4 flex-shrink-0">
      <v-img src="~/assets/FragHub_icon.png" max-width="100" class="mx-auto"></v-img>
    </div>
    <div class="d-flex flex-column flex-grow-1 overflow-hidden" style="gap: 16px;">
      <v-card class="flex-grow-1 d-flex flex-column border overflow-hidden" elevation="2">
        <v-tabs v-model="tabReport" bg-color="grey-lighten-3" density="compact" class="flex-shrink-0">
          <v-tab value="report">Report</v-tab>
        </v-tabs>
        <v-card-text class="flex-grow-1 overflow-y-auto pa-2 bg-white" ref="reportContainer">
          <div v-for="(log, i) in logs" :key="i" class="mb-1">
            <div v-if="log.type === 'step'" class="text-center font-weight-bold text-subtitle-1 my-3">{{ log.text }}</div>
            <div v-else-if="log.type === 'deletion'" class="text-center text-red font-weight-medium text-subtitle-1 my-1">{{ log.text }}</div>
            <div v-else-if="log.type === 'completion'" class="text-center font-weight-bold text-h6 text-green my-3">{{ log.text }}</div>
            <v-row v-else-if="log.type === 'progress_finished'" class="align-center px-2 py-1 mx-0" style="border-bottom: 1px solid #eee;">
              <v-col cols="4" class="font-weight-bold text-caption pa-0">{{ log.prefix }}</v-col>
              <v-col cols="4" class="pa-0 px-2">
                <v-progress-linear
                    :model-value="100"
                    height="24"
                    color="blue-darken-1"
                    rounded
                    class="mb-2"
                    style="border: 1px solid #ccc;">
                </v-progress-linear>
              </v-col>
              <v-col cols="4" class="text-right text-caption pa-0">{{ log.suffix }}</v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>
      <v-card class="pa-0 flex-shrink-0 border" elevation="2">
        <v-tabs v-model="tabProgress" bg-color="grey-lighten-3" density="compact">
          <v-tab value="progress">Progress</v-tab>
        </v-tabs>
        <v-card-text class="pa-4 bg-white">
          <div v-if="!isFinished">
            <div class="text-subtitle-1 font-weight-medium mb-1">{{ currentPrefix }}</div>
            <v-progress-linear v-model="progressPercent" height="24" color="blue-darken-1" rounded class="mb-2" :class="{ 'instant-reset': progressPercent === 0 }" style="border: 1px solid #ccc;"></v-progress-linear>
            <div class="text-right text-subtitle-2 text-grey-darken-2">{{ suffixText }}</div>
          </div>
          <div v-else class="text-center">
            <div class="text-h5 font-weight-bold my-4">{{ finalMessage }}</div>
          </div>
        </v-card-text>
      </v-card>
    </div>
    <div class="d-flex justify-center mt-6 flex-shrink-0">
      <v-btn v-if="!isFinished" color="error" size="x-large" width="150" class="font-weight-bold" @click="stopProcess" :loading="isStopping">{{ isStopping ? 'STOPPING...' : 'STOP' }}</v-btn>
      <v-btn v-else color="success" size="x-large" width="150" class="font-weight-bold" @click="finishProcess">FINISH</v-btn>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { io } from "socket.io-client"
import { useState } from '#imports'

const socket = io("http://127.0.0.1:8000")
const isExecuting = useState('isExecuting')
const tabReport = ref('report')
const tabProgress = ref('progress')
const reportContainer = ref(null)
const logs = ref([])
const currentPrefix = ref('Starting...')
const itemType = ref('items')
const startTime = ref(Date.now())
const isFinished = ref(false)
const isStopping = ref(false)
const finalMessage = ref('')

// État de progression — directement appliqué, pas de lerp
const progressValue = ref(0)
const totalItems = ref(0)
let taskFinishedLogged = false

// Timer pour rafraîchir le texte elapsed/ETA (pas besoin de RAF)
let timerHandle = null

// ---------------------------------------------------------------
// Calculs
// ---------------------------------------------------------------
const progressPercent = computed(() => {
  if (totalItems.value <= 0) return 0
  return Math.min((progressValue.value / totalItems.value) * 100, 100)
})

function getSpeed() {
  const elapsed = (Date.now() - startTime.value) / 1000
  return elapsed > 0 ? progressValue.value / elapsed : 0
}

function getETA() {
  const speed = getSpeed()
  return speed > 0 ? (totalItems.value - progressValue.value) / speed : 0
}

const formatTime = (s) => {
  if (!isFinite(s) || s < 0) return '00:00:00'
  const h = Math.floor(s / 3600).toString().padStart(2, '0')
  const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0')
  const sec = Math.floor(s % 60).toString().padStart(2, '0')
  return `${h}:${m}:${sec}`
}

// Tick réactif pour forcer la mise à jour du suffixe chaque seconde
const tick = ref(0)
const suffixText = computed(() => {
  void tick.value // dépendance réactive au tick
  const pct = progressPercent.value.toFixed(2)
  const elapsed = (Date.now() - startTime.value) / 1000
  const speed = getSpeed().toFixed(2)
  const eta = getETA()
  return `${pct}% | ${progressValue.value}/${totalItems.value} ${itemType.value} [${formatTime(elapsed)} < ${formatTime(eta)}, ${speed} ${itemType.value}/s]`
})

// ---------------------------------------------------------------
// Utilitaires
// ---------------------------------------------------------------
const scrollToBottom = async () => {
  await nextTick()
  if (reportContainer.value) {
    const el = reportContainer.value.$el || reportContainer.value
    el.scrollTop = el.scrollHeight
  }
}

function checkTaskFinished() {
  if (
      !taskFinishedLogged &&
      totalItems.value > 0 &&
      progressValue.value >= totalItems.value
  ) {
    taskFinishedLogged = true
    logs.value.push({
      type: 'progress_finished',
      prefix: currentPrefix.value,
      suffix: suffixText.value
    })
    scrollToBottom()
  }
}

// ---------------------------------------------------------------
// Événements Socket.IO
// ---------------------------------------------------------------
onMounted(() => {
  startTime.value = Date.now()

  // Tick chaque seconde pour mettre à jour elapsed/ETA dans le texte
  timerHandle = setInterval(() => { tick.value++ }, 1000)

  socket.on('progress', (val) => {
    progressValue.value = val
    checkTaskFinished()
  })

  socket.on('total_items', (val) => {
    // --- FILET DE SÉCURITÉ ---
    // Si une tâche précédente tournait mais n'a pas été logguée (bloquée à 99%),
    // on force sa complétion avant de réinitialiser la barre.
    if (totalItems.value > 0 && !taskFinishedLogged) {
      progressValue.value = totalItems.value
      checkTaskFinished()
    }
    // -------------------------

    progressValue.value = 0
    totalItems.value = val
    startTime.value = Date.now()
    taskFinishedLogged = false
  })

  socket.on('prefix', (val) => { currentPrefix.value = val })
  socket.on('item_type', (val) => { itemType.value = val })

  socket.on('step', (val) => {
    logs.value.push({ text: val, type: 'step' })
    scrollToBottom()
  })

  socket.on('deletion', (val) => {
    logs.value.push({ text: val, type: 'deletion' })
    scrollToBottom()
  })

  socket.on('completion', (val) => {
    progressValue.value = totalItems.value  // barre à 100% instantané
    finalMessage.value = val
    logs.value.push({ text: val, type: 'completion' })
    isFinished.value = true
    isStopping.value = false
    scrollToBottom()
  })
})

const stopProcess = async () => {
  isStopping.value = true
  await fetch('http://127.0.0.1:8000/stop-analysis')
}

const finishProcess = () => { isExecuting.value = false }

onUnmounted(() => {
  clearInterval(timerHandle)
  socket.disconnect()
})
</script>

<style scoped>
.border { border: 1px solid #e0e0e0; }

/* On désactive la transition native pour un comportement instantané "façon PyQt" */
:deep(.v-progress-linear__determinate) {
  transition: none !important;
}
</style>