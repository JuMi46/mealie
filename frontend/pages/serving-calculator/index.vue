<template>
  <div>
    <p>Serving calculator</p>
    <label>Container type: <v-select v-model="state.containerType" :items="containerTypes" style="width: 160px;" @change="containerType_onChange($event)"></v-select></label>
    <label style="">Container: <v-select v-if="containerWeights" v-model="state.containerWeight" :items="containerWeights" style="width: 240px"></v-select>
    {{state.containerWeight}} g</label>
    <label>Total weight: <v-text-field v-model="state.totalWeight" type="number" style="width: 80px"/></label>
    <table v-if="state.totalWeight && state.totalWeight - state.containerWeight > 0">
        <thead>
          <tr>
            <th style="padding-right: 14px;">Serving</th>
            <th>Weight</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>1</td>
            <td>{{calculateServings(1)}}</td>
          </tr>
          <tr>
            <td>2</td>
            <td>{{calculateServings(2)}}</td>
          </tr>
          <tr>
            <td>3</td>
            <td>{{calculateServings(3)}}</td>
          </tr>
          <tr>
            <td>4</td>
            <td>{{calculateServings(4)}}</td>
          </tr>
          <tr>
            <td>5</td>
            <td>{{calculateServings(5)}}</td>
          </tr>
          <tr>
            <td>6</td>
            <td>{{calculateServings(6)}}</td>
          </tr>
          <tr>
            <td>
              <v-text-field
                v-model="state.servingCount"
                type="number"
                :min="7"
                :max="99"
                style="width: 40px"
              />
            </td>
            <td>{{calculateServings(state.servingCount)}}</td>
          </tr>
        </tbody>
      </table>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, reactive } from "@nuxtjs/composition-api";

export default defineComponent({
  middleware: "auth",
  setup() {
    const containerTypes = [
      { text: "Pots", value: "pots" },
      { text: "Pans", value: "pans" },
      { text: "Bowls", value: "bowls" },
      { text: "Ovenpans", value: "ovenpans"}
    ];
    const containerWeightsList:{ [key: string]: { text: string, value: number }[] } = {
      pots: [
        {text: "XS", value: 385},
        {text: "S", value: 619},
        {text: "M", value: 760},
        {text: "L", value: 1209},
        {text: "Frech", value: 4554},
        {text: "Kahari", value: 894},
        {text: "Crock M", value: 1628},
        {text: "Crock L", value: 3260},
        {text: "Rice", value: 136},
      ],
      pans: [
        {text: "XS", value: 402},
        {text: "M", value: 654},
        {text: "L", value: 882},
        {text: "Scan", value: 1590},
        {text: "Cast iron", value: 1891},
        {text: "Square", value: 699},
        {text: "Square grooved", value: 861},
      ],
      bowls: [
        {text: "S", value: 204},
        {text: "M", value: 292},
        {text: "L", value: 337},
        {text: "Kitchen aid", value: 684},
        {text: "Measuring S", value: 38},
        {text: "Measuring L", value: 64},
        {text: "Mixer", value: 196},
        {text: "Mixer + blade", value: 246},
      ],
      ovenpans: [
        {text: "Bread pan clear", value: 636},
        {text: "Bread pan orange", value: 800},
        {text: "Pie pan", value: 1092},
        {text: "Casserole 9x13", value: 1596},
        {text: "Casserole square", value: 1296},
        {text: "Casserole rörstrand", value: 1752},
      ]
    };

    const containerWeights = computed(() => {
      return containerWeightsList[state.containerType];
    });

    const state = reactive({
      containerType: containerTypes[0].value,
      containerWeight: containerWeightsList[containerTypes[0].value][0].value,
      totalWeight: null,
      servingCount: 7
    });

  const containerType_onChange = function(value: string) {
    console.log(value);
    if (containerWeightsList[value]) {
      state.containerWeight = containerWeightsList[value][0].value;
    }
  }

  const calculateServings = function(servings:number) {
    if (!servings || !state.totalWeight || !state.containerWeight) return "";

    const servingWeight = Math.floor(
      (state.totalWeight - state.containerWeight) / servings
    );

    return servingWeight > 0 ? servingWeight : "";
  }

    return {
      state,
      containerTypes,
      containerWeights,
      containerType_onChange,
      calculateServings
  //     ...toRefs(state),
    };
  },
  head() {
    return {
      title: "Serving calculator",
    };
  },
});
</script>

<style scoped>
  label {
    display: grid;
    grid-template-columns:  max-content max-content max-content;
    align-items: center;
    gap: 10px;
  }
</style>
