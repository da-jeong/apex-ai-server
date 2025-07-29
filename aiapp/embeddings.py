import numpy as np

def dummy_embedding(text):
    # 텍스트를 고정된 1536 차원 임
    np.random.seed(hash(text)%(2**32))
    return np.randomm.rand(1536).tolist()