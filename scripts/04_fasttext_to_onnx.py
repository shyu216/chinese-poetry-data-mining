"""
script: 04_fasttext_to_onnx.py
stage: P3-向量模型
artifact: ONNX 词向量模型
purpose: 将 Gensim FastText 模型导出为 ONNX，以便在 JS 环境中推理。
inputs:
- results/fasttext/poetry.model
outputs:
- results/fasttext/poetry.onnx
- results/fasttext/token_to_id.json
- results/fasttext/onnx_metadata.json
depends_on:
- 04_fasttext_train.py
- onnx
notes:
- 该导出为词表向量查表模型（Gather），不包含 FastText 子词 OOV 逻辑。
- JS 端需先做分词并将 token 映射到 token_id，未知词映射为 0。
develop_date: 2026-03-25
last_modified_date: 2026-03-25
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import onnx
from gensim.models import FastText
from onnx import TensorProto, helper, numpy_helper


PAD_TOKEN = "<UNK>"


def patch_numpy_pickle_compat() -> bool:
    """兼容旧模型中的 bit_generator class pickle 格式。"""
    try:
        import numpy.random._pickle as np_pickle  # type: ignore[attr-defined]
    except Exception:
        return False

    original_ctor = getattr(np_pickle, "__bit_generator_ctor", None)
    if original_ctor is None:
        return False

    if getattr(original_ctor, "__name__", "") == "_compat_bit_generator_ctor":
        return True

    def _compat_bit_generator_ctor(bit_generator_name: Any = "MT19937"):
        # 旧 pickle 里可能是 class 对象，新版构造器只接受字符串名称
        if isinstance(bit_generator_name, type):
            bit_generator_name = bit_generator_name.__name__
        elif hasattr(bit_generator_name, "__name__"):
            bit_generator_name = getattr(bit_generator_name, "__name__")
        return original_ctor(bit_generator_name)

    np_pickle.__bit_generator_ctor = _compat_bit_generator_ctor
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 FastText 模型导出为 ONNX")
    parser.add_argument(
        "--model",
        default="results/fasttext/poetry.model",
        help="输入 FastText 模型路径",
    )
    parser.add_argument(
        "--onnx",
        default="results/fasttext/poetry.onnx",
        help="输出 ONNX 文件路径",
    )
    parser.add_argument(
        "--token-map",
        default="results/fasttext/token_to_id.json",
        help="输出 token->id 映射路径",
    )
    parser.add_argument(
        "--meta",
        default="results/fasttext/onnx_metadata.json",
        help="输出导出元数据路径",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=13,
        help="ONNX opset 版本",
    )
    return parser.parse_args()


def load_embedding_matrix(model: FastText) -> tuple[np.ndarray, dict[str, int], int]:
    vector_size = model.wv.vector_size

    # id=0 保留给未知词，向量置零
    token_to_id: dict[str, int] = {PAD_TOKEN: 0}
    vectors: list[np.ndarray] = [np.zeros((vector_size,), dtype=np.float32)]

    # Gensim 4.x: key_to_index 顺序稳定且与训练词表对应
    for token in model.wv.key_to_index:
        token_to_id[token] = len(vectors)
        vectors.append(model.wv[token].astype(np.float32))

    embedding_matrix = np.stack(vectors, axis=0).astype(np.float32)
    vocab_size = embedding_matrix.shape[0]
    return embedding_matrix, token_to_id, vocab_size


def load_embedding_matrix_from_sidecar(model_path: Path) -> tuple[np.ndarray, dict[str, int], int]:
    """当 FastText.load 失败时，直接从 sidecar 文件恢复词向量。"""
    vectors_path = Path(str(model_path) + ".wv.vectors_vocab.npy")
    vocab_path = model_path.parent / "vocab.json"

    if not vectors_path.exists():
        raise FileNotFoundError(f"未找到向量文件: {vectors_path}")
    if not vocab_path.exists():
        raise FileNotFoundError(f"未找到词表文件: {vocab_path}")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    if not isinstance(vocab, list) or not vocab:
        raise ValueError(f"词表文件格式异常: {vocab_path}")

    vectors = np.load(vectors_path)
    if vectors.ndim != 2:
        raise ValueError(f"向量矩阵维度异常: {vectors.shape}")
    if vectors.shape[0] != len(vocab):
        raise ValueError(
            f"词表长度与向量行数不一致: len(vocab)={len(vocab)}, vectors={vectors.shape}"
        )

    vector_size = int(vectors.shape[1])
    token_to_id: dict[str, int] = {PAD_TOKEN: 0}
    embedding_rows: list[np.ndarray] = [np.zeros((vector_size,), dtype=np.float32)]

    for idx, token in enumerate(vocab):
        token_to_id[str(token)] = idx + 1
        embedding_rows.append(vectors[idx].astype(np.float32))

    embedding_matrix = np.stack(embedding_rows, axis=0).astype(np.float32)
    vocab_size = embedding_matrix.shape[0]
    return embedding_matrix, token_to_id, vocab_size


def build_onnx_model(embedding_matrix: np.ndarray, opset: int) -> onnx.ModelProto:
    vocab_size, vector_size = embedding_matrix.shape

    input_ids = helper.make_tensor_value_info(
        "token_ids",
        TensorProto.INT64,
        ["N"],
    )
    output_embeddings = helper.make_tensor_value_info(
        "embeddings",
        TensorProto.FLOAT,
        ["N", vector_size],
    )

    embedding_initializer = numpy_helper.from_array(embedding_matrix, name="embedding_table")

    gather_node = helper.make_node(
        "Gather",
        inputs=["embedding_table", "token_ids"],
        outputs=["embeddings"],
        axis=0,
    )

    graph = helper.make_graph(
        nodes=[gather_node],
        name="FastTextEmbeddingLookup",
        inputs=[input_ids],
        outputs=[output_embeddings],
        initializer=[embedding_initializer],
    )

    model = helper.make_model(
        graph,
        producer_name="chinese-poetry-data-mining",
        opset_imports=[helper.make_opsetid("", opset)],
    )

    model.ir_version = onnx.IR_VERSION
    onnx.checker.check_model(model)

    print(f"已构建 ONNX 模型: 词表大小={vocab_size}, 向量维度={vector_size}, opset={opset}")
    return model


def save_json(path: Path, data: dict | list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()

    model_path = Path(args.model)
    onnx_path = Path(args.onnx)
    token_map_path = Path(args.token_map)
    meta_path = Path(args.meta)

    print("=" * 60)
    print("FastText -> ONNX 导出")
    print("=" * 60)
    print(f"输入模型: {model_path}")
    print(f"输出 ONNX: {onnx_path}")
    print(f"输出词表映射: {token_map_path}")

    if not model_path.exists():
        raise FileNotFoundError(f"未找到模型文件: {model_path}")

    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    token_map_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    embedding_matrix: np.ndarray
    token_to_id: dict[str, int]
    vocab_size: int

    print("\n加载 FastText 模型...")
    try:
        model = FastText.load(str(model_path))
        print("提取词向量矩阵...")
        embedding_matrix, token_to_id, vocab_size = load_embedding_matrix(model)
    except ValueError as e:
        error_text = str(e)
        if "is not a known BitGenerator module" in error_text:
            print("检测到旧模型随机状态兼容问题，尝试启用 NumPy 兼容补丁后重试...")
            if patch_numpy_pickle_compat():
                try:
                    model = FastText.load(str(model_path))
                    print("提取词向量矩阵...")
                    embedding_matrix, token_to_id, vocab_size = load_embedding_matrix(model)
                except Exception:
                    print("补丁重试失败，改用 sidecar 文件回退加载...")
                    embedding_matrix, token_to_id, vocab_size = load_embedding_matrix_from_sidecar(model_path)
            else:
                print("无法注入 NumPy 兼容补丁，改用 sidecar 文件回退加载...")
                embedding_matrix, token_to_id, vocab_size = load_embedding_matrix_from_sidecar(model_path)
        else:
            print("FastText 反序列化失败，改用 sidecar 文件回退加载...")
            embedding_matrix, token_to_id, vocab_size = load_embedding_matrix_from_sidecar(model_path)
    except Exception:
        print("FastText 反序列化失败，改用 sidecar 文件回退加载...")
        embedding_matrix, token_to_id, vocab_size = load_embedding_matrix_from_sidecar(model_path)

    print("构建 ONNX 图...")
    onnx_model = build_onnx_model(embedding_matrix, opset=args.opset)

    print("保存 ONNX 文件...")
    onnx.save(onnx_model, str(onnx_path))

    print("保存 token->id 映射...")
    save_json(token_map_path, token_to_id)

    export_metadata = {
        "version": "v1",
        "timestamp": datetime.now().isoformat(),
        "source_model": str(model_path),
        "onnx_model": str(onnx_path),
        "token_map": str(token_map_path),
        "unk_token": PAD_TOKEN,
        "unk_id": 0,
        "vocab_size_with_unk": vocab_size,
        "vector_size": int(embedding_matrix.shape[1]),
        "opset": args.opset,
        "limitations": [
            "该 ONNX 模型仅支持已分词 token_id 的向量查表。",
            "不包含 FastText 原始子词 OOV 组合逻辑。",
        ],
    }
    print("保存导出元数据...")
    save_json(meta_path, export_metadata)

    print("\n" + "=" * 60)
    print("导出完成")
    print("=" * 60)
    print(f"ONNX: {onnx_path}")
    print(f"token->id: {token_map_path}")
    print(f"metadata: {meta_path}")


if __name__ == "__main__":
    main()
