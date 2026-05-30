<template>
  <v-app>
    <v-main>
      <v-container class="fill-height position-relative pa-0" fluid>

        <div class="background-logo">
          <v-img
              src="~/assets/FragHub_icon.png"
              max-height="350"
              max-width="350"
              alt="FragHub Background Logo"
          ></v-img>
        </div>

        <v-card
            class="w-100 h-100 d-flex flex-column bg-transparent"
            elevation="0"
        >
          <v-tabs
              v-model="activeTab"
              bg-color="transparent"
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

          <v-card-text class="flex-grow-1 overflow-y-auto pa-0 pb-16">
            <v-tabs-window v-model="activeTab" class="h-100">
              <v-tabs-window-item value="input" class="h-100"><InputTab /></v-tabs-window-item>
              <v-tabs-window-item value="output" class="h-100"><OutputTab /></v-tabs-window-item>
              <v-tabs-window-item value="filters" class="h-100"><FiltersTab /></v-tabs-window-item>
              <v-tabs-window-item value="denovo" class="h-100"><DeNovoTab /></v-tabs-window-item>
              <v-tabs-window-item value="output_settings" class="h-100"><OutputSettingTab /></v-tabs-window-item>
              <v-tabs-window-item value="projects" class="h-100"><ProjectsTab /></v-tabs-window-item>
            </v-tabs-window>
          </v-card-text>
        </v-card>

        <v-btn
            color="success"
            size="x-large"
            elevation="8"
            class="start-btn text-h6 font-weight-bold"
            @click="startExecution"
        >
          START
        </v-btn>

      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, useState } from '#imports'

const activeTab = ref('input')

const parameters = useState('parameters', () => ({
  input_directory: [],
  output_directory: "",
  calculate_de_novo: false,
  de_novo_ppm_tolerance: 10.0,
}))

const startExecution = async () => {
  console.log("Paramètres envoyés :", parameters.value)
}
</script>

<style scoped>
/* Centre le logo de fond parfaitement au milieu */
.background-logo {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0; /* Le place tout au fond */
  pointer-events: none; /* TRÈS IMPORTANT : Empêche le logo de bloquer les clics de la souris */
  opacity: 0.10; /* Opacité à 10% pour l'effet filigrane. Ajuste si tu le veux plus ou moins visible */
  width: 100%;
  display: flex;
  justify-content: center;
}

/* Fixe le bouton en bas de l'écran, peu importe la taille de la fenêtre */
.start-btn {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10; /* Le place tout devant */
  min-width: 250px;
  border-radius: 30px; /* Un petit arrondi sympa pour un bouton flottant */
}
</style>