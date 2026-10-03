# REVIEW C：赋值路径独立核对

审查日 2026-10-04；AI 独立审查，不是人类专家认证。未读取研究结果变量。

从官方人口 ZIP、各层级原生 Filosofi MED20、官方 EPCI/BV 工作簿独立重建 34,816 个 metropolitan 市镇。与主线程 `assignment2024_commune_paths.csv` 对照 30 个字段、1,044,480 个市镇×字段值，差异 **0**。状态：PASS_CURRENT_INPUT_NUMERICAL_RECONSTRUCTION。

| 条件 | 市镇数 |
|---|---:|
| metropolitan_communes | 34,816 |
| listed_metropolitan_initial2024 | 17,672 |
| original_arrête_all_communes | 17,717 |
| original_list_codes_outside_metropolitan_2023 | 45 |
| A_real_epci | 13,421 |
| A_isolated_commune | 1 |
| C_department | 3,871 |
| mandatory_union_A_or_C | 14,316 |
| mandatory_A_and_C_overlap | 2,977 |
| mandatory_missing_from_official_list | 0 |
| B_potential_numeric | 14,613 |
| D_potential_upper | 3,043 |
| listed_only_possible_B_or_D | 3,356 |
| listed_without_reconstructed_possible_path | 0 |
| not_listed_but_possible_path | 0 |
| BV_indicators_unknown | 0 |
| isolated_communes_missing_income | 1 |
| isolated_A_unresolved_unknown_AND | 0 |

A 和 C 的并集是确定性必要资格路径；B 仅为数值上的可能生活圈补充资格，D 仅为山地人口上界下的可能资格。完整重叠组合见 `review_C_assignment_path_overlaps.csv`。省长提案及精确山地人口分部没有被观察，因此不能把 listed_only_possible_B_or_D 的每个市镇都归因于某条确定路径。

unknown AND 的规则：有一个已知 false 条件即可排除路径；其他已知条件均 true 而某条件 unknown 时，路径 unresolved。Île-de-Sein 的收入缺失，但密度已超阈值，因此其 own-COM A 路径为 false。主脚本 BV 对任意缺失均视为潜在资格，这是更保守屏障；当前 BV 输入全完整，实际计数没有差异。

山地 COG2022→COG2023 的 10 个周界/代码变化目标已另查官方 movements；没有任何前身在 mountain 列表中，本次未发现上界漏入。主脚本 unknown 仅检查代码是否存在，不能一般化为周界稳定；后续版本仍应做 movements 核查。上界本身不等于实际人口比例。

本次核对建立的是法定数值必要条件与可能集合对原始名单的兼容性；不代表取得全部实际路径、并行趋势成立或 RD 支持充足。主脚本及输出 SHA256：

- `data/processed/assignment2024_commune_paths.csv`：`ecfd53d4eb0f4976fae025480e98c8e1c2f3fc8d67b4e84475fa1bb6743b8bad`
- `src/construct/assignment2024.py`：`a4ab2fbe0ee74f2fbe19a3cabd0c72ae3238c61a6f127ac4c9c0218d80bfec04`
