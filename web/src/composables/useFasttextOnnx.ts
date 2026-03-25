import { ref } from 'vue'
import * as ort from 'onnxruntime-web'

export function useFasttextOnnx() {
  const session = ref<any | null>(null)
  const tokenToId = ref<Record<string, number> | null>(null)
  const idToToken = ref<string[] | null>(null)
  const vectorSize = ref<number>(0)

  const base = import.meta.env.BASE_URL || '/'
  const modelUrl = `${base}data/fasttext/poetry.onnx`
  const tokenMapUrl = `${base}data/fasttext/token_to_id.json`

  async function init() {
    try {
      // 加载 token->id 映射
      const res = await fetch(tokenMapUrl)
      if (!res.ok) throw new Error('Failed to fetch token map')
      tokenToId.value = await res.json()
      // 构建 id->token 列表（保证索引顺序）
      const tokenMap = tokenToId.value as Record<string, number>
      const maxId = Math.max(...Object.values(tokenMap))
      const arr: string[] = Array(maxId + 1).fill('')
      for (const [t, id] of Object.entries(tokenMap)) {
        arr[id as number] = t
      }
      idToToken.value = arr

      // 创建 inference session（使用构建期依赖 onnxruntime-web）
      session.value = await ort.InferenceSession.create(modelUrl)

      // 从模型输出推断向量维度：查询单个 id
      const ids = new BigInt64Array([0n])
      const tensor = new ort.Tensor('int64', ids, [1])
      const feeds: Record<string, any> = { token_ids: tensor }
      const out = await session.value.run(feeds)
      const embeddings = Object.values(out)[0] as any
      vectorSize.value = embeddings.dims[1]

      return { ok: true }
    } catch (e) {
      console.error('[useFasttextOnnx] init failed', e)
      return { ok: false, error: e }
    }
  }

  // 计算 topK 相似词（余弦相似度）
  async function getSimilar(word: string, topK = 30) {
    if (!session.value || !tokenToId.value || !idToToken.value) {
      throw new Error('Model not initialized')
    }

    const tokenMap = tokenToId.value!
    const idTo = idToToken.value!
    const id = tokenMap[word]
    if (id === undefined) throw new Error('Unknown token')

    // 获取目标向量
    const targetIds = new BigInt64Array([BigInt(id)])
    const targetTensor = new ort.Tensor('int64', targetIds, [1])
    const targetOut = await session.value.run({ token_ids: targetTensor })
    const targetEmb = (Object.values(targetOut)[0] as any).data as Float32Array

    // 批量获取所有词向量（一次性查询所有 id）
    const allIds = new BigInt64Array(idTo.length)
    for (let i = 0; i < idTo.length; i++) allIds[i] = BigInt(i)
    const allTensor = new ort.Tensor('int64', allIds, [idTo.length])
    const allOut = await session.value.run({ token_ids: allTensor })
    const allEmb = (Object.values(allOut)[0] as any).data as Float32Array

    const dim = vectorSize.value
    // 计算余弦相似度
    const scores: Array<{ token: string; score: number }> = []
    // 预计算 target norm
    let tnorm = 0
    for (let i = 0; i < dim; i++) {
      const v = targetEmb[i] ?? 0
      tnorm += v * v
    }
    tnorm = Math.sqrt(tnorm) || 1

    for (let i = 0; i < idTo.length; i++) {
      const baseIdx = i * dim
      let dot = 0
      let norm = 0
      for (let d = 0; d < dim; d++) {
        const v = allEmb[baseIdx + d] ?? 0
        const tv = targetEmb[d] ?? 0
        dot += v * tv
        norm += v * v
      }
      norm = Math.sqrt(norm) || 1
      const cos = dot / (tnorm * norm)
      const token = idTo[i] ?? ''
      scores.push({ token, score: cos })
    }

    // 排序并返回 topK（排除自身）
    scores.sort((a, b) => b.score - a.score)
    const filtered = scores.filter(s => s.token !== word).slice(0, topK)
    return filtered
  }

  return {
    init,
    getSimilar,
    loading: session,
    tokenToId,
    idToToken,
    vectorSize
  }
}

export default useFasttextOnnx
