<template>
  <v-container class="fill-height d-flex flex-column justify-center">
    <v-row justify="center" align="center" class="mb-6">
      <v-col cols="auto" class="d-flex align-center">
        <v-switch
            v-model="parameters.calculate_de_novo"
            :true-value="1.0"
            :false-value="0.0"
            color="success"
            inset
            hide-details
            class="mr-4"
        ></v-switch>
        <span class="text-h6">Calculate fragment formula</span>
        <span class="text-caption text-error font-italic ml-4">
          (warning: not compatible with most reprocessing software)
        </span>
      </v-col>
    </v-row>

    <v-row justify="center" align="center">
      <v-col cols="auto" class="d-flex align-center">
        <span class="text-body-1 mr-4">ppm tolerance:</span>
        <v-text-field
            v-model.number="parameters.de_novo_ppm_tolerance"
            type="number"
            variant="outlined"
            density="compact"
            hide-details
            style="width: 120px;"
        ></v-text-field>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
const parameters = useState('parameters')
</script>