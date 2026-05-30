<template>
  <v-app>
    <v-main>
      <v-container class="fill-height d-flex flex-column overflow-hidden" fluid>

        <div class="text-center mb-2 flex-shrink-0">
          <v-img
              src="~/assets/FragHub_icon.png"
              height="100"
              width="100"
              class="mx-auto"
              alt="FragHub Logo"
          ></v-img>
        </div>

        <v-card
            class="w-100 flex-grow-1 d-flex flex-column mb-4"
            elevation="3"
            style="min-height: 400px; max-height: 550px;"
        >
          <v-tabs
              v-model="activeTab"
              bg-color="grey-darken-3"
              color="primary"
              align-tabs="center"
          >
            <v-tab value="input">INPUT</v-tab>
            <v-tab value="output">OUTPUT</v-tab>
            <v-tab value="filters">Filters</v-tab>
            <v-tab value="denovo">De Novo</v-tab>
            <v-tab value="output_settings">Output settings</v-tab>
            <v-tab value="projects">Projects settings</v-tab>
          </v-tabs>

          <v-card-text class="flex-grow-1 overflow-y-auto pa-0"> <v-tabs-window v-model="activeTab" class="h-100">

            <v-tabs-window-item value="input" class="h-100">
              <InputTab />
            </v-tabs-window-item>

            <v-tabs-window-item value="output" class="h-100"><OutputTab /></v-tabs-window-item>
            <v-tabs-window-item value="filters" class="h-100"><FiltersTab /></v-tabs-window-item>
            <v-tabs-window-item value="denovo" class="h-100"><DeNovoTab /></v-tabs-window-item>
            <v-tabs-window-item value="output_settings" class="h-100"><OutputSettingTab /></v-tabs-window-item>
            <v-tabs-window-item value="projects" class="h-100"><ProjectsTab /></v-tabs-window-item>

          </v-tabs-window>
          </v-card-text>
        </v-card>

        <div class="text-center mb-2 flex-shrink-0">
          <v-btn
              color="success"
              size="large"
              elevation="4"
              @click="startExecution"
          >
            START
          </v-btn>
        </div>

      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, useState } from '#imports'

const activeTab = ref('input') // On met 'denovo' par défaut pour tester notre nouveau composant

// État global partagé (remplace parameters_dict)
const parameters = useState('parameters', () => ({
  input_directory: [],
  output_directory: "",
  calculate_de_novo: false,
  de_novo_ppm_tolerance: 10.0,
  // ... autres paramètres
}))

const startExecution = async () => {
  // Envoi vers l'API FastAPI
  console.log("Paramètres envoyés :", parameters.value)
}
</script>