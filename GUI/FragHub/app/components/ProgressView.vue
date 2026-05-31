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

          <div v-else-if="log.type === 'progress_finished'" class="mt-2 pa-3 finished-progress-zone">
            <div class="text-subtitle-2 font-weight-bold mb-1 text-green-darken-4">{{ log.prefix }}</div>
            <v-row class="align-center mx-0">
              <v-col cols="8" class="pa-0">
                <v-progress-linear
                    :model-value="100"
                    height="20"
                    color="success"
                    rounded
                    class="finished-bar"
                ></v-progress-linear>
              </v-col>
              <v-col cols="4" class="text-right pa-0 text-caption font-weight-bold text-green-darken-4">
                100.00%
              </v-col>
            </v-row>
            <div class="text-right text-caption text-grey-darken-3 mt-1">{{ log.suffix }}</div>
          </div>

        </div>

        <ActiveProgress
            v-if="!isFinished"
            :prefix="currentPrefix"
            :progress-percent="progressPercent"
            :suffix="suffixText"
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
const isFinished = ref(false)
const isStopping = ref(false)
const finalMessage = ref('')

const progressValue = ref(0)
const totalItems = ref(0)
let taskFinishedLogged = false
let timerHandle = null

const progressPercent = computed(() => {
  if (totalItems.value <= 0) return 0
  return Math.min((progressValue.value / totalItems.value) * 100, 100)
})

const suffixText = computed(() => {
  const elapsed = (Date.now() - startTime.value) / 1000
  const speed = elapsed > 0 ? (progressValue.value / elapsed).toFixed(2) : 0
  const eta = speed > 0 ? (totalItems.value - progressValue.value) / speed : 0
  return `${progressValue.value}/${totalItems.value} ${itemType.value} [${formatTime(elapsed)} < ${formatTime(eta)}, ${speed} ${itemType.value}/s]`
})

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
    logs.value.push({
      type: 'progress_finished',
      prefix: currentPrefix.value,
      suffix: suffixText.value
    })
  }
}

onMounted(() => {
  startTime.value = Date.now()
  timerHandle = setInterval(() => { /* force computed update */ }, 1000)

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

/* Le nouveau style pour l'étape terminée */
.finished-progress-zone {
  border: 2px solid #4CAF50; /* Le "tour" en vert success */
  background-color: rgba(76, 175, 80, 0.05); /* Fond très légèrement vert */
  border-radius: 8px;
}

.finished-bar {
  border: 1px solid #388E3C;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>