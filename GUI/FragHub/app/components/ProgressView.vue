<template>
  <v-container fluid class="pa-4 position-relative d-flex flex-column" style="height: 100vh; max-height: 100vh; overflow: hidden;">

    <div class="background-logo-overlay">
      <v-img src="~/assets/FragHub_icon.png" width="400" opacity="0.08"></v-img>
    </div>

    <v-card class="w-100 d-flex flex-column border bg-transparent-card" elevation="2" style="z-index: 2; flex: 1 1 auto; min-height: 0;">

      <v-tabs v-model="tabReport" bg-color="grey-lighten-4" density="compact" style="flex: 0 0 auto;">
        <v-tab value="report" class="font-weight-bold">EXECUTION REPORT</v-tab>
      </v-tabs>

      <v-card-text class="pa-4 bg-white-transparent" ref="reportContainer" style="flex: 1 1 auto; overflow-y: auto; min-height: 0;">

        <div v-for="(log, i) in logs" :key="i" class="mb-1">

          <div v-if="log.type === 'step'" class="text-center font-weight-bold text-subtitle-1 my-4 text-blue-darken-3">
            {{ log.text }}
          </div>

          <div v-else-if="log.type === 'deletion'" class="text-center text-red-darken-2 font-weight-medium text-subtitle-2 my-1" style="white-space: pre-line;">
            {{ log.text }}
          </div>

          <div v-else-if="log.type === 'progress_finished'" class="mt-2 finished-progress-zone">
            <div class="d-flex align-center justify-start mb-3">
              <v-icon color="success" class="mr-2" size="22">mdi-check-circle-outline</v-icon>
              <div class="text-subtitle-1 font-weight-bold text-green-darken-4 text-truncate">
                {{ log.prefix.replace(/:\s*$/, '') }}
              </div>
            </div>

            <v-progress-linear
                :model-value="100"
                height="26"
                color="success"
                rounded
                class="finished-bar"
            >
              <template v-slot:default>
                <span class="text-white font-weight-black text-caption px-2 drop-shadow">
                  100.00%
                </span>
              </template>
            </v-progress-linear>

            <div class="d-flex justify-space-between mt-2">
              <div class="text-caption text-green-darken-3 font-weight-bold text-left">
                {{ log.current }} of {{ log.total }} {{ log.itemType }} &nbsp;|&nbsp; Elapsed: {{ log.elapsed }} &nbsp;|&nbsp; ETA: 00:00:00
              </div>
              <div class="text-caption text-green-darken-3 font-weight-bold text-right">
                {{ log.speed }} {{ log.itemType }}/s
              </div>
            </div>
          </div>

        </div>

        <ActiveProgress
            v-if="!isFinished"
            :prefix="currentPrefix"
            :progress-percent="progressPercent"
            :current="progressValue"
            :total="totalItems"
            :item-type="itemType"
            :elapsed="formattedElapsed"
            :eta="formattedEta"
            :speed="speedVal"
        />

        <div v-else class="text-center py-8">
          <v-icon color="success" size="64" class="mb-4">mdi-check-circle</v-icon>
          <div class="text-h4 font-weight-black text-green-darken-3">{{ finalMessage }}</div>
        </div>

      </v-card-text>
    </v-card>

    <div class="d-flex justify-center mt-4" style="z-index: 2; flex: 0 0 auto;">
      <v-btn v-if="!isFinished" color="error" size="x-large" width="200" class="font-weight-bold" elevation="4" @click="stopProcess" :loading="isStopping">
        {{ isStopping ? 'STOPPING...' : 'STOP PROCESS' }}
      </v-btn>
      <v-btn v-else color="success" size="x-large" width="200" class="font-weight-bold" elevation="4" @click="finishProcess">
        CLOSE REPORT
      </v-btn>
    </div>

  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { io } from "socket.io-client"
import { useState } from '#imports'
import ActiveProgress from '~/components/ActiveProgress.vue'

const socket = io("http://127.0.0.1:8000")
const isExecuting = useState('isExecuting')
const tabReport = ref('report')
const reportContainer = ref(null)
const logs = ref([])
const currentPrefix = ref('Initializing...')
const itemType = ref('items')
const startTime = ref(Date.now())
const now = ref(Date.now()) // NOUVEAU: Variable réactive pour forcer la mise à jour du chronomètre
const isFinished = ref(false)
const isStopping = ref(false)
const finalMessage = ref('')

const progressValue = ref(0)
const totalItems = ref(0)
let taskFinishedLogged = false
let timerHandle = null

// --- Calculs Mathématiques ---
const progressPercent = computed(() => {
  if (totalItems.value <= 0) return 0
  return Math.min((progressValue.value / totalItems.value) * 100, 100)
})

const elapsedSec = computed(() => {
  const e = (now.value - startTime.value) / 1000
  return e > 0 ? e : 0
})

const speedVal = computed(() => {
  // On bloque le calcul de vitesse si moins d'1 seconde s'est écoulée
  // pour éviter les valeurs aberrantes dues aux divisions proches de 0.
  if (progressValue.value === 0 || elapsedSec.value < 1) return "0.00"
  return (progressValue.value / elapsedSec.value).toFixed(2)
})

const etaSec = computed(() => {
  const speed = parseFloat(speedVal.value)
  return speed > 0 ? (totalItems.value - progressValue.value) / speed : 0
})

const formattedElapsed = computed(() => formatTime(elapsedSec.value))
const formattedEta = computed(() => formatTime(etaSec.value))

const formatTime = (s) => {
  if (!isFinite(s) || s < 0) return '00:00:00'
  const h = Math.floor(s / 3600).toString().padStart(2, '0')
  const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0')
  const sec = Math.floor(s % 60).toString().padStart(2, '0')
  return `${h}:${m}:${sec}`
}

const scrollToBottom = async () => {
  await nextTick()
  if (reportContainer.value) {
    const el = reportContainer.value.$el || reportContainer.value
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }
}

watch([logs, progressValue], () => {
  scrollToBottom()
}, { deep: true })

function checkTaskFinished() {
  if (!taskFinishedLogged && totalItems.value > 0 && progressValue.value >= totalItems.value) {
    taskFinishedLogged = true

    // On passe toutes les données séparément pour maintenir le design
    logs.value.push({
      type: 'progress_finished',
      prefix: currentPrefix.value,
      current: progressValue.value,
      total: totalItems.value,
      itemType: itemType.value,
      elapsed: formattedElapsed.value,
      speed: speedVal.value
    })
  }
}

onMounted(() => {
  startTime.value = Date.now()
  now.value = Date.now()
  // Met à jour la variable réactive 'now' toutes les secondes pour actualiser le temps
  timerHandle = setInterval(() => { now.value = Date.now() }, 1000)

  socket.on('progress', (val) => {
    progressValue.value = val
    checkTaskFinished()
  })

  socket.on('total_items', (val) => {
    if (totalItems.value > 0 && !taskFinishedLogged) {
      progressValue.value = totalItems.value
      checkTaskFinished()
    }
    progressValue.value = 0
    totalItems.value = val
    startTime.value = Date.now()
    now.value = Date.now()
    taskFinishedLogged = false
  })

  socket.on('prefix', (val) => { currentPrefix.value = val })
  socket.on('item_type', (val) => { itemType.value = val })
  socket.on('step', (val) => { logs.value.push({ text: val, type: 'step' }) })
  socket.on('deletion', (val) => { logs.value.push({ text: val, type: 'deletion' }) })

  socket.on('completion', (val) => {
    progressValue.value = totalItems.value
    finalMessage.value = val
    isFinished.value = true
    isStopping.value = false
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
.background-logo-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  pointer-events: none;
}

.bg-transparent-card {
  background-color: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(4px);
}

.bg-white-transparent {
  background-color: rgba(255, 255, 255, 0.7) !important;
}

.finished-progress-zone {
  border: 2px solid #4CAF50;
  background-color: rgba(76, 175, 80, 0.05);
  padding: 16px;
  border-radius: 12px;
}

.finished-bar {
  border: 1px solid #388E3C;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.15);
}

.drop-shadow {
  text-shadow: 1px 1px 2px rgba(0,0,0,0.6);
  letter-spacing: 1px;
}
</style>