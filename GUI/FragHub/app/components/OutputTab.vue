<template>
  <v-container class="fill-height d-flex flex-column position-relative">

    <div class="d-flex flex-column align-center justify-center flex-grow-1">

      <v-btn
          icon
          width="140"
          height="140"
          elevation="3"
          color="grey-lighten-4"
          class="mb-6"
          @click="browseDirectory"
      >
        <v-icon size="80" color="primary">mdi-folder-open-outline</v-icon>
      </v-btn>

      <div class="text-h5 font-weight-bold mb-6">Select output directory</div>

      <div
          v-if="parameters.output_directory"
          class="text-body-1 text-center text-break px-4"
          style="max-width: 600px;"
      >
        {{ parameters.output_directory }}
      </div>

      <div v-else class="text-grey font-italic text-body-1">
        No directory selected
      </div>

    </div>

    <div class="d-flex justify-end w-100 mt-auto">
      <v-tooltip location="top">
        <template v-slot:activator="{ props }">
          <v-btn
              icon="mdi-information-outline"
              variant="text"
              v-bind="props"
              color="grey-darken-1"
          ></v-btn>
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

// Récupération de l'état global partagé
const parameters = useState('parameters')

// Équivalent de ta méthode browse_output_files()
const browseDirectory = async () => {
  /* Plus tard avec Electron :
    const selectedDir = await window.electronAPI.selectDirectoryDialog()
    if (selectedDir) {
      parameters.value.output_directory = selectedDir
    }
  */

  // Pour tester l'UI dans le navigateur, on injecte un chemin factice :
  parameters.value.output_directory = "C:\\Users\\Axel\\Data\\FragHub_Output"
}
</script>