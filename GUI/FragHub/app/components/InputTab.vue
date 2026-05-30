<template>
  <v-container class="h-100 position-relative pa-4">

    <div class="grid-layout h-100">

      <div></div>

      <div class="d-flex flex-column align-center justify-center">
        <input type="file" ref="fileInput" multiple accept=".json,.csv,.msp,.mgf" class="d-none" @change="handleFileChange" />

        <v-btn
            icon
            width="100"
            height="100"
            elevation="3"
            color="grey-lighten-4"
            class="mb-4"
            @click="$refs.fileInput.click()"
        >
          <v-icon size="50" color="primary">mdi-file-document-multiple-outline</v-icon>
        </v-btn>
        <div class="text-subtitle-1 font-weight-bold">Select input files</div>
      </div>

      <div class="d-flex align-center justify-start pl-8">
        <v-expand-x-transition>
          <v-card v-if="fileNames.length > 0" width="300" height="250" elevation="2">
            <v-card-title class="text-subtitle-1 pa-2 bg-grey-lighten-3">Selected Files</v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-0 overflow-y-auto" style="height: 200px;">
              <v-list density="compact">
                <v-list-item v-for="(name, index) in fileNames" :key="index" :title="name">
                  <template v-slot:prepend>
                    <v-icon size="x-small" color="primary">mdi-file</v-icon>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-expand-x-transition>
      </div>

    </div>

    <div class="position-absolute" style="bottom: 10px; right: 10px;">
      <v-tooltip location="top">
        <template v-slot:activator="{ props }">
          <v-btn icon="mdi-information-outline" variant="text" v-bind="props" color="grey" size="small"></v-btn>
        </template>
        <span>Select single or multiple .json, .csv, .msp, or .mgf files</span>
      </v-tooltip>
    </div>

  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useState } from '#imports'

const parameters = useState('parameters')
const fileInput = ref(null)

const fileNames = computed(() => {
  if (!parameters.value.input_directory || parameters.value.input_directory.length === 0) return []
  return parameters.value.input_directory.map(path => path.name || path.split(/[/\\]/).pop())
})

const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    parameters.value.input_directory = files.map(f => f.name)
  }
}
</script>

<style scoped>
/* C'est ce bloc qui empêche tout décentrage horizontal */
.grid-layout {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  width: 100%;
}
</style>