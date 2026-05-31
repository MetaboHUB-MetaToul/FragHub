<template>
  <v-container fluid class="h-100 position-relative pa-4">

    <div class="d-flex h-100 align-center w-100">

      <div class="transition-flex" :style="{ flex: hasFiles ? '0 0 8px' : '1 1 0%' }"></div>

      <div
          class="d-flex flex-column align-center justify-center flex-shrink-0 button-zone"
          style="width: 160px;"
      >
        <input
            type="file"
            ref="fileInput"
            multiple
            accept=".json,.csv,.msp,.mgf"
            class="d-none"
            @change="handleFileChange"
        />

        <v-btn
            icon
            width="100"
            height="100"
            elevation="3"
            color="grey-lighten-4"
            class="mb-4"
            @click="browseFiles"
        >
          <v-icon size="50" color="primary">mdi-file-document-multiple-outline</v-icon>
        </v-btn>

        <div class="text-subtitle-1 font-weight-bold text-center">
          {{ hasFiles ? 'Add more files' : 'Select input files' }}
        </div>
      </div>

      <transition name="slide-panel">
        <div v-if="hasFiles" class="panel-container d-flex flex-column overflow-hidden" style="min-width: 0; height: 100%;">

          <v-card class="w-100 h-100 d-flex flex-column border-0" elevation="2">

            <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-3 d-flex align-center justify-space-between flex-shrink-0">
              <span><v-icon class="mr-2">mdi-format-list-bulleted</v-icon>Selected Files ({{ parameters.input_directory.length }})</span>

              <v-btn size="small" color="error" variant="text" prepend-icon="mdi-delete-sweep" @click="clearAll">
                Clear all
              </v-btn>
            </v-card-title>

            <v-divider class="flex-shrink-0"></v-divider>

            <v-card-text class="pa-0 flex-grow-1 overflow-y-auto">
              <v-list density="compact">
                <transition-group name="list-anim">
                  <v-list-item v-for="(name, index) in fileNames" :key="name + index" class="border-b">

                    <template v-slot:prepend>
                      <v-icon size="small" color="primary" class="mr-3">mdi-file-outline</v-icon>
                    </template>

                    <v-list-item-title class="text-body-2">{{ name }}</v-list-item-title>

                    <template v-slot:append>
                      <v-btn
                          icon="mdi-delete"
                          variant="text"
                          color="error"
                          size="small"
                          @click="removeFile(index)"
                      ></v-btn>
                    </template>

                  </v-list-item>
                </transition-group>
              </v-list>
            </v-card-text>

          </v-card>

        </div>
      </transition>

      <div class="transition-flex" :style="{ flex: hasFiles ? '0 0 0%' : '1 1 0%' }"></div>

    </div>

    <div class="position-absolute" style="bottom: 10px; right: 10px;">
      <v-tooltip location="top" max-width="400">
        <template v-slot:activator="{ props }">
          <v-btn icon="mdi-information" variant="text" size="small" color="grey" v-bind="props"></v-btn>
        </template>
        <span class="text-body-2">Select single or multiple .json, .csv, .msp, or .mgf files</span>
      </v-tooltip>
    </div>

  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useState } from '#imports'

const parameters = useState('parameters')

// ON REMET LA RÉFÉRENCE POUR LE WEB
const fileInput = ref(null)

const hasFiles = computed(() => {
  return parameters.value.input_directory && parameters.value.input_directory.length > 0
})

const fileNames = computed(() => {
  if (!hasFiles.value) return []
  return parameters.value.input_directory.map(path => path.split(/[/\\]/).pop())
})

// === LOGIQUE HYBRIDE (ELECTRON + WEB) ===
const browseFiles = async () => {
  if (window.electronAPI) {
    // Si on est dans l'application Electron
    const selectedFiles = await window.electronAPI.selectFiles()

    if (selectedFiles && selectedFiles.length > 0) {
      if (!parameters.value.input_directory) parameters.value.input_directory = []
      parameters.value.input_directory = [...parameters.value.input_directory, ...selectedFiles]
    }
  } else {
    // Si on est sur le navigateur Web (Fallback), on clique sur l'input caché
    if (fileInput.value) {
      fileInput.value.click()
    }
  }
}

// ON REMET LA FONCTION POUR GÉRER LA SÉLECTION WEB
const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    const newNames = files.map(f => f.name)
    if (!parameters.value.input_directory) parameters.value.input_directory = []
    parameters.value.input_directory = [...parameters.value.input_directory, ...newNames]
  }
  event.target.value = ''
}

const removeFile = (index) => {
  parameters.value.input_directory.splice(index, 1)
}

const clearAll = () => {
  parameters.value.input_directory = []
}
</script>

<style scoped>
/* 1. L'animation de glissement du bouton (grâce aux espaceurs flex) */
.transition-flex {
  transition: flex 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.button-zone {
  z-index: 2; /* Garde le bouton au-dessus de l'animation d'ouverture */
}

/* 2. L'animation du volet qui s'ouvre (Tiroir) */
.panel-container {
  flex-grow: 1;
  will-change: max-width, opacity, transform;
}

.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: max-width 0.7s cubic-bezier(0.16, 1, 0.3, 1),
  opacity 0.5s ease 0.1s,
  transform 0.7s cubic-bezier(0.16, 1, 0.3, 1),
  margin 0.7s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  max-width: 0;
  opacity: 0;
  transform: translateX(-40px); /* Le volet sort de sous le bouton */
  margin-left: 0 !important;
}

.slide-panel-enter-to,
.slide-panel-leave-from {
  max-width: 100%;
  opacity: 1;
  transform: translateX(0);
  margin-left: 24px !important; /* L'équivalent de ml-6 */
}

/* 3. Animation de la liste des fichiers (ajout/suppression) */
.list-anim-enter-active,
.list-anim-leave-active {
  transition: all 0.4s ease;
}
.list-anim-enter-from,
.list-anim-leave-to {
  opacity: 0;
  transform: translateX(20px); /* Les nouveaux fichiers arrivent par la droite */
}
.list-anim-leave-active {
  position: absolute; /* Empêche la liste de sauter pendant qu'un élément est supprimé */
  width: 100%;
}

.border-b {
  border-bottom: 1px solid #eeeeee;
}
</style>