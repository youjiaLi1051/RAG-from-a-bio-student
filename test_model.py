"""快速验证 bge-m3 模型是否可用"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from FlagEmbedding import BGEM3FlagModel

print("加载模型...")
model = BGEM3FlagModel("D:/biograph/.cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181", use_fp16=True)

print("编码测试...")
output = model.encode(
    ["细胞膜的结构是什么？", "What is the structure of cell membrane?"],
    return_dense=True,
    return_sparse=True,
)

dense = output["dense_vecs"]
sparse = output["lexical_weights"]

print(f"\ndense 向量形状: {dense.shape}")
print(f"sparse 条目数: {len(sparse)}")
print(f"\n模型加载成功，可以使用！")
