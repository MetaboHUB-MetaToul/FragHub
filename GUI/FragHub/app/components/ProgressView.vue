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

            <div v-if="log.type === 'step'" class="text-center font-weight-bold text-subtitle-1 my-3">
              {{ log.text }}
            </div>

            <div v-else-if="log.type === 'deletion'" class="text-center text-red font-weight-medium text-subtitle-1 my-1">
              {{ log.text }}
            </div>

            <div v-else-if="log.type === 'completion'" class="text-center font-weight-bold text-h6 text-green my-3">
              {{ log.text }}
            </div>

            <v-row v-else-if="log.type === 'progress_finished'" class="align-center px-2 py-1 mx-0" style="border-bottom: 1px solid #eee;">
              <v-col cols="4" class="font-weight-bold text-caption pa-0">{{ log.prefix }}</v-col>
              <v-col cols="4" class="pa-0 px-2">
                <v-progress-linear model-value="100" height="18" color="blue-darken-1" rounded class="border"></v-progress-linear>
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

            <v-progress-linear
                v-model="progressPercent"
                height="24"
                color="blue-darken-1"
                rounded
                class="mb-2"
                :class="{ 'instant-reset': progressPercent === 0 }"
                style="border: 1px solid #ccc;"
            ></v-progress-linear>

            <div class="text-right text-subtitle-2 text-grey-darken-2">
              {{ suffixText }}
            </div>
          </div>
          <div v-else class="text-center">
            <div class="text-h5 font-weight-bold my-4">{{ finalMessage }}</div>
          </div>
        </v-card-text>
      </v-card>

    </div>

    <div class="d-flex justify-center mt-6 flex-shrink-0">
      <v-btn
          v-if="!isFinished"
          color="error"
          size="x-large"
          width="150"
          class="font-weight-bold"
          @click="stopProcess"
          :loading="isStopping"
      >
        {{ isStopping ? 'STOPPING...' : 'STOP' }}
      </v-btn>
      <v-btn
          v-else
          color="success"
          size="x-large"
          width="150"
          class="font-weight-bold"
          @click="finishProcess"
      >
        FINISH
      </v-btn>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { io } from "socket.io-client"
import { useState } from '#imports'

const socket = io("http://127.0.0.1:8000")
const isExecuting = useState('isExecuting')

const tabReport = ref('report')
const tabProgress = ref('progress')
const reportContainer = ref(null)

const logs = ref([])
const progressValue = ref(0)
const totalItems = ref(100)
const currentPrefix = ref('Starting...')
const itemType = ref('items')
const startTime = ref(Date.now())
const isFinished = ref(false)
const isStopping = ref(false)
const finalMessage = ref('')
let hasReportedCurrentTask = false
let timerInterval = null;

const progressPercent = computed(() => {
  if (totalItems.value <= 0) return 0;
  return (progressValue.value / totalItems.value) * 100;
})

const itemsPerSecond = computed(() => {
  const elapsed = (Date.now() - startTime.value) / 1000
  return elapsed > 0 ? progressValue.value / elapsed : 0
})

const estimatedTimeLeft = computed(() => {
  const remaining = totalItems.value - progressValue.value
  return itemsPerSecond.value > 0 ? remaining / itemsPerSecond.value : 0
})

const formatTime = (seconds) => {
  if (!isFinite(seconds) || seconds < 0) return "00:00:00"
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0')
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0')
  const s = Math.floor(seconds % 60).toString().padStart(2, '0')
  return `${h}:${m}:${s}`
}

const suffixText = computed(() => {
  const pct = progressPercent.value.toFixed(2)
  const prog = progressValue.value
  const tot = totalItems.value
  const it = itemType.value
  const elapsed = (Date.now() - startTime.value) / 1000
  const speed = itemsPerSecond.value.toFixed(2)
  const eta = estimatedTimeLeft.value
  return `${pct}% | ${prog}/${tot} ${it} [${formatTime(elapsed)} < ${formatTime(eta)}, ${speed} ${it}/s]`
})

const scrollToBottom = async () => {
  await nextTick()
  if (reportContainer.value) {
    const el = reportContainer.value.$el || reportContainer.value;
    el.scrollTop = el.scrollHeight
  }
}

watch(progressValue, (newVal) => {
  if (newVal >= totalItems.value && totalItems.value > 0 && !hasReportedCurrentTask) {
    logs.value.push({
      type: 'progress_finished',
      prefix: currentPrefix.value,
      suffix: suffixText.value
    })
    hasReportedCurrentTask = true
    scrollToBottom()
  }
})

onMounted(() => {
  startTime.value = Date.now()

  timerInterval = setInterval(() => {
    if (!isFinished.value && progressValue.value < totalItems.value) {
      progressValue.value = progressValue.value
    }
  }, 1000);

  socket.on('progress', (val) => { progressValue.value = val })

  socket.on('total_items', (val) => {
    totalItems.value = val
    startTime.value = Date.now()
    progressValue.value = 0
    hasReportedCurrentTask = false
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
    finalMessage.value = val;
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

const finishProcess = () => {
  isExecuting.value = false
}

onUnmounted(() => {
  clearInterval(timerInterval)
  socket.disconnect()
})
</script>

<style scoped>
.border { border: 1px solid #e0e0e0; }

/* Magie Noire CSS (Deep Selector) :
  On rentre dans le composant interne de Vuetify pour désactiver
  l'animation de la barre UNIQUEMENT quand la classe instant-reset est active.
*/
.instant-reset :deep(.v-progress-linear__determinate) {
  transition: none !important;
}
</style>