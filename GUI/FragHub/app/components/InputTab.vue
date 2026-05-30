<template>
  <v-container fluid class="h-100 position-relative pa-4">

    <div class="d-flex h-100 align-center w-100">

      <div
          class="d-flex flex-column align-center justify-center transition-all flex-shrink-0"
          :class="hasFiles ? 'ml-2 mr-6' : 'mx-auto'"
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
            @click="$refs.fileInput.click()"
        >
          <v-icon size="50" color="primary">mdi-file-document-multiple-outline</v-icon>
        </v-btn>

        <div class="text-subtitle-1 font-weight-bold text-center">
          {{ hasFiles ? 'Add more files' : 'Select input files' }}
        </div>
      </div>

      <v-expand-x-transition>
        <div v-if="hasFiles" class="flex-grow-1 h-100 d-flex flex-column overflow-hidden" style="min-width: 0;">

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
                <v-list-item v-for="(name, index) in fileNames" :key="index" class="border-b">

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
              </v-list>
            </v-card-text>

          </v-card>

        </div>
      </v-expand-x-transition>

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

const hasFiles = computed(() => {
  return parameters.value.input_directory && parameters.value.input_directory.length > 0
})

const fileNames = computed(() => {
  if (!hasFiles.value) return []
  return parameters.value.input_directory.map(path => path.name || path.split(/[/\\]/).pop())
})

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
.transition-all {
  transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.border-b {
  border-bottom: 1px solid #eeeeee;
}
</style>