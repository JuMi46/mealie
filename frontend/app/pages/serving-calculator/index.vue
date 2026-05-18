<template>
  <div>
    <p>Serving calculator</p>
    <label>Container type:
      <v-select
        v-model="servingCategory"
        :items="servingCategories"
        style="width: 160px;"
      />
    </label>
    <label>Container:
      <v-select
        v-if="containerWeights"
        v-model="containerWeight"
        :items="containerWeights"
        item-title="labelText"
        item-value="weight"
        style="width: 240px"
      />
      {{ containerWeight }} g
    </label>
    <label>Total weight:
      <v-text-field
        v-model="totalWeight"
        type="number"
        style="width: 100px"
      />
    </label>
    <table v-if="totalWeight && totalWeight - containerWeight > 0">
      <thead>
        <tr>
          <th style="padding-right: 14px;">
            Serving
          </th>
          <th>Weight</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td>{{ calculateServings(1) }}</td>
        </tr>
        <tr>
          <td>2</td>
          <td>{{ calculateServings(2) }}</td>
        </tr>
        <tr>
          <td>3</td>
          <td>{{ calculateServings(3) }}</td>
        </tr>
        <tr>
          <td>4</td>
          <td>{{ calculateServings(4) }}</td>
        </tr>
        <tr>
          <td>5</td>
          <td>{{ calculateServings(5) }}</td>
        </tr>
        <tr>
          <td>6</td>
          <td>{{ calculateServings(6) }}</td>
        </tr>
        <tr>
          <td>
            <v-text-field
              v-model="servingCount"
              type="number"
              :min="7"
              :max="99"
            />
          </td>
          <td>{{ calculateServings(servingCount) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { useToolStore } from "~/composables/store";

const auth = useMealieAuth();
const userHousehold = computed(() => auth.user.value?.householdSlug || "");
const toolStore = useToolStore();

const servingCategory = ref("");
const containerWeight = ref(0);
const totalWeight = ref();
const servingCount = ref(7);

const myTools = computed(() => toolStore.store.value
  .filter(tool => tool.householdsWithTool?.includes(userHousehold.value) && tool.servingCategory)
  .toSorted((a, b) => { return (a.position || 100) - (b.position || 100); }));

const servingCategories = computed(() => [...new Set(myTools.value.map(tool => tool.servingCategory))].sort());

const containerWeights = computed(() => myTools.value.filter(tool => tool.servingCategory == servingCategory.value));

watch(servingCategories, (newServingCategories) => {
  if (newServingCategories[0]) {
    servingCategory.value = newServingCategories[0];
  }
});

watch(containerWeights, (newContainerWeights) => {
  if (newContainerWeights[0]?.weight) {
    containerWeight.value = newContainerWeights[0]?.weight;
  }
});

const calculateServings = function (servings: number) {
  if (!servings || !totalWeight.value || !containerWeight.value) return "";

  const servingWeight = Math.floor(
    (totalWeight.value - containerWeight.value) / servings,
  );

  return servingWeight > 0 ? servingWeight : "";
};

useSeoMeta({
  title: "Serving calculator",
});
</script>

<style scoped>
  label {
  display: grid;
  grid-template-columns: max-content max-content max-content;
  align-items: center;
  gap: 10px;
}
</style>
