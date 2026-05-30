<template>
  <v-container class="h-100 position-relative pa-0">

    <div class="grid-layout h-100">

      <div></div>

      <div class="d-flex flex-column align-center justify-center">
        <v-btn
            icon
            width="100"
            height="100"
            elevation="3"
            color="grey-lighten-4"
            class="mb-4"
            @click="browseDirectory"
        >
          <v-icon size="50" color="primary">mdi-folder-open-outline</v-icon>
        </v-btn>
        <div class="text-subtitle-1 font-weight-bold">Select output directory</div>
      </div>

      <div class="h-100 py-4 pr-4 pl-8 d-flex align-stretch">
        <v-expand-x-transition>

          <v-card v-if="parameters.output_directory" class="w-100 h-100 d-flex flex-column" elevation="2">

            <v-card-title class="text-subtitle-1 pa-2 bg-grey-lighten-3 flex-shrink-0">
              Selected Directory
            </v-card-title>
            <v-divider class="flex-shrink-0"></v-divider>

            <v-card-text class="pa-4 flex-grow-1 d-flex align-center justify-center overflow-y-auto">
              <div class="text-body-1 text-center text-break font-weight-medium text-grey-darken-2">
                {{ parameters.output_directory }}
              </div>
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
        <span>
          Create a new empty directory or Select an existing directory <br>
          where FragHub has already written files
        </span>
      </v-tooltip>
    </div>

  </v-container>
</template>

<script setup>
import { useState } from '#imports'

const parameters = useState('parameters')

const browseDirectory = async () => {
  // Pour tester, on simule un dossier
  parameters.value.output_directory = "C:\\Users\\Axel\\Data\\FragHub_Output"
}
</script>

<style scoped>
.grid-layout {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  width: 100%;
  height: 100%;
}
</style>