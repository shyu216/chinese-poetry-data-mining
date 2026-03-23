<script setup lang="ts">
interface Props {
  sentences: string[]
  mode?: 'text' | 'meter'
  animate?: boolean
  animationDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'text',
  animate: true,
  animationDelay: 0
})

const getCharDelay = (sentenceIndex: number, charIndex: number) => {
  const baseDelay = props.animationDelay
  const sentenceDelay = sentenceIndex * 200
  const charDelay = charIndex * 30
  return baseDelay + sentenceDelay + charDelay
}
</script>

<template>
  <div class="poem-content" :class="`mode-${mode}`">
    <template v-if="mode === 'text'">
      <p
        v-for="(sentence, index) in sentences"
        :key="index"
        class="poem-sentence"
        :class="{ 'animate-in': animate }"
        :style="animate ? { animationDelay: `${animationDelay + index * 100}ms` } : {}"
      >
        {{ sentence }}
      </p>
    </template>

    <template v-else-if="mode === 'meter'">
      <div class="meter-grid">
        <div
          v-for="(sentence, rowIndex) in sentences"
          :key="rowIndex"
          class="meter-row"
        >
          <div
            v-for="(char, charIndex) in sentence.split('')"
            :key="charIndex"
            class="meter-cell"
            :class="{ 'animate-in': animate }"
            :style="animate ? { animationDelay: `${getCharDelay(rowIndex, charIndex)}ms` } : {}"
            :title="`第${rowIndex + 1}句 · 第${charIndex + 1}字`"
          >
            {{ char }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.poem-content {
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
}

/* Text Mode */
.mode-text .poem-sentence {
  font-size: 18px;
  line-height: 2;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 12px;
  text-align: center;
  letter-spacing: 2px;
  opacity: 1;
}

.mode-text .poem-sentence.animate-in {
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
}

.mode-text .poem-sentence:last-child {
  margin-bottom: 0;
}

/* Meter Mode */
.meter-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.meter-row {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.meter-cell {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--color-ink, #2c3e50);
  background:
    linear-gradient(to right, rgba(139, 38, 53, 0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(139, 38, 53, 0.1) 1px, transparent 1px),
    linear-gradient(45deg, transparent 49.5%, rgba(139, 38, 53, 0.05) 49.5%, rgba(139, 38, 53, 0.05) 50.5%, transparent 50.5%),
    linear-gradient(-45deg, transparent 49.5%, rgba(139, 38, 53, 0.05) 49.5%, rgba(139, 38, 53, 0.05) 50.5%, transparent 50.5%);
  background-size:
    50% 100%,
    100% 50%,
    100% 100%,
    100% 100%;
  background-position: center;
  border: 1px solid rgba(139, 38, 53, 0.15);
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 1;
}

.meter-cell.animate-in {
  opacity: 0;
  transform: scale(0.8);
  animation: cellPopIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.meter-cell:hover {
  background-color: rgba(139, 38, 53, 0.05);
  border-color: rgba(139, 38, 53, 0.3);
  transform: scale(1.05);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes cellPopIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 768px) {
  .mode-text .poem-sentence {
    font-size: 16px;
    line-height: 1.8;
  }

  .meter-cell {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .meter-cell {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }
}
</style>
