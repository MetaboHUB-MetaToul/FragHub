<template>
  <v-app>
    <v-main>
      <v-container class="fill-height d-flex flex-column" fluid>

        <div class="text-center mb-6">
          <v-img
              src="/assets/FragHub_icon.png"
              height="200"
              width="200"
              class="mx-auto"
              alt="FragHub Logo"
          ></v-img>
        </div>

        <v-card class="flex-grow-1 w-100 mb-6 d-flex flex-column" elevation="3">
          <v-tabs
              v-model="activeTab"
              bg-color="grey-darken-3"
              color="primary"
              align-tabs="center"
          >
            <v-tab value="input">INPUT</v-tab>
            <v-tab value="output">OUTPUT</v-tab>
            <v-tab value="filters">Filters settings</v-tab>
            <v-tab value="denovo">De Novo settings</v-tab>
            <v-tab value="output_settings">Output settings</v-tab>
            <v-tab value="projects">Projects settings</v-tab>
          </v-tabs>

          <v-card-text class="flex-grow-1 overflow-y-auto">
            <v-tabs-window v-model="activeTab">

              <v-tabs-window-item value="input">
                <div class="text-center py-10 text-grey">Composant InputTab viendra ici...</div>
              </v-tabs-window-item>

              <v-tabs-window-item value="output">
                <div class="text-center py-10 text-grey">Composant OutputTab viendra ici...</div>
              </v-tabs-window-item>

              <v-tabs-window-item value="filters">
                <div class="text-center py-10 text-grey">Composant FiltersTab viendra ici...</div>
              </v-tabs-window-item>

              <v-tabs-window-item value="denovo">
                <div class="text-center py-10 text-grey">Composant DeNovoTab viendra ici...</div>
              </v-tabs-window-item>

              <v-tabs-window-item value="output_settings">
                <div class="text-center py-10 text-grey">Composant OutputSettingTab viendra ici...</div>
              </v-tabs-window-item>

              <v-tabs-window-item value="projects">
                <div class="text-center py-10 text-grey">Composant ProjectsTab viendra ici...</div>
              </v-tabs-window-item>

            </v-tabs-window>
          </v-card-text>
        </v-card>

        <div class="text-center mb-4">
          <v-btn
              color="success"
              size="x-large"
              elevation="4"
              width="140"
              height="60"
              class="text-h6 font-weight-bold"
              @click="startExecution"
          >
            START
          </v-btn>
        </div>

      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, useState } from '#imports'

// Gestion de l'onglet actif
const activeTab = ref('input')

// Équivalent direct de ton `parameters_dict` de global_vars.py
// useState permet à cet objet d'être réactif et accessible partout dans l'app Nuxt
const parameters = useState('parameters', () => ({
  input_directory: null,
  output_directory: null,
  // Les autres valeurs par défaut seront initialisées dans leurs composants respectifs
}))

// Équivalent de open_progress_window() dans main_GUI.py
const startExecution = () => {
  const missingSelections = []

  if (!parameters.value.input_directory || parameters.value.input_directory.length === 0) {
    missingSelections.push("at least one input file")
  }
  if (!parameters.value.output_directory) {
    missingSelections.push("an output directory")
  }

  if (missingSelections.length > 0) {
    // Plus tard, nous remplacerons ce simple alert par un v-dialog ou un v-snackbar Vuetify
    alert("Please select " + missingSelections.join(" and ") + " before starting.")
    return
  }

  console.log("Démarrage du processus avec les paramètres :", parameters.value)
  // La logique de communication IPC avec Electron/Python se fera ici.
}
</script>