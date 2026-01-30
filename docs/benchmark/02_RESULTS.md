# Results by Model

## GPT-5.2 Medium Reasoning

| Metric               | Without AUx | With AUx   | Delta     |
|----------------------|-------------|------------|-----------|
| **Context consumed** | 182k (47%)  | 117k (30%) | **-36%**  |
| **Tool calls**       | ~30         | 20 (81 ops)| —         |
| **Files read**       | ~30         | 43         | +43%      |
| **Tokens/operation** | 6,067       | 1,444      | **-76%**  |
| **Coverage quality** | Excellent   | Excellent+ | Improved  |

**Outcome**:  
AUx skills reduced context consumption by over a third while enabling deeper analysis (+43% more files read).

## GPT-5.2 Low Reasoning

| Metric               | Without AUx | With AUx  | Delta     |
|----------------------|-------------|-----------|-----------|
| **Context consumed** | 93k (24%)   | 64k (17%) | **-31%**  |
| **Tool calls**       | 9 (36 ops)  | 28        | —         |
| **Files read**       | 22          | 11        | -50%      |
| **Tokens/operation** | 2,583       | 2,286     | **-11%**  |
| **Coverage quality** | Excellent   | Excellent | Same      |

**Outcome**:  
AUx skills enabled a cheaper, low-reasoning model to outperform the baseline while reading half as many files.
