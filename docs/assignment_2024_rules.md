# REVIEW A — 2024 年首次 FRR 赋值规则与阈值设计边界

审计日期：2026-10-04。范围：2024 年 7 月 1 日首次分类；仅核查法律、赋值输入、原始分类及候选支持，不读取研究结果，不运行 RD。审计人为 AI 独立复核者，不构成人类法律意见或论文质量认证。

已核验原始法律和 INSEE 输入，3,009 个地域指标行重现全部官方公布阈值。原始法国本土分类与“确定性通道 ∪ 数值上可行的 bassin 通道 ∪ 保守山地人口上界通道”之间没有观察到遗漏或多余分类。这个结果验证了候选规则集合的覆盖，不能恢复每个 commune 的实际行政赋值路径。全国初始 bassin 提议/批准记录、准确山区人口份额和原始 DGCL 计算工作簿仍未获得。

当前三个经过其他通道筛除的 EPCI 阈值候选域，合格侧分别只有 0、6、至多 1 个 EPCI，均不支持开展可信的局部 RD。本审查不授权任何新的因果结论或 HAL 提交。

## 1. 历史版本和证据层级

法律依据是 [LFI 2024 第 73 条的原始 JORF 文本](https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000048727426)，与 [CGI 44 quindecies A 于 2024-07-01 的历史版本](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049130324/2024-07-01/)逐项对照。历史页面明确标示有效期 2024-07-01 至 2025-02-16。下述规则取自 II A–E 和 IV，未用后续修订倒推初始制度。

[2024 年 6 月 19 日原始 arrêté](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820)于 6 月 20 日公布、7 月 1 日生效，附录使用 COG2023。官方原文提取的名单有 17,717 个独立 commune 代码，其中 20 个 Réunion 代码仅部分地域分类；法国本土列入 17,672 个。代码和部分分类标记保存在 `data/processed/frr_2024_codes_verified.csv`，34 份官方页面文本快照及校验和见 `data/raw/legal/frr_2024_official_extraction_manifest.json`。附录提供实际名单，没有逐 commune 的 A/B/C/D 通道、指标或 prefect 提议字段。

证据分为四层：原始法律与原始 arrêté 决定规则及实际名单；同期政府发言说明指标观察年；同期国民议会报告公布数值阈值；2025 年政府答复只用来补充明确指向初始制度的个别实例。当前地图、2025 新增规则、补充 beneficiary、FRR+ 名单不能替代初始名单或路径。

DGCL 的 2024-09-13 FAQ 旧 URL 仍能被搜索发现，但当前下载返回 404，地方官方镜像也未成功恢复文件，故本报告不把它列为已获得证据。同期 [国民议会 2024 年预算意见第 486-VIII 号](https://www.assemblee-nationale.fr/dyn/17/rapports/cion-dvp/l17b0486-tviii_rapport-avis.pdf)第 18 页独立记载全部六个数值阈值。2025 年 FAQ 第 3.1.1 节明确回述 LFI2024，与其相符；第 3.1.2 节的新增路径不纳入本重构。

## 2. 日期、观察年与地域冻结

法律 IV 要求使用 INSEE 在分类前一年 7 月 1 日已可获得的数据，EPCI 边界取前一年 1 月 1 日。对首次 2024 分类，相应为 **可得性截止 2023-07-01**、**EPCI 边界 2023-01-01**。截止日期不是观察年份，不能据此写成收入/人口观察于 2023 年。

[2023-11-26 Sénat 会议实录](https://www.senat.fr/cra/s20231126/s20231126.pdf)PDF 第 66 页、印刷第 63 页的部长发言直接说明采用 recensement 2020 与 Filosofi 2020。以下公开 INSEE 输入均与该观察年一致，并独立重现官方阈值；仍未声称取得原始 DGCL 生产工作簿。

| 变量或地域 | 实际公开输入 | 年份/日期 | 使用规则和限制 |
|---|---|---|---|
| 收入 | Filosofi 各层级 `MED20` | 观察 2020；COG2023；网页 2023-04-24 发布 | 直接使用 COM/EPCI/BV2022/DEP 各层级收入中位数，不能从 commune 中位数求和或人口加权构造 EPCI 中位数。 |
| 人口 | 历年普查表 `P20_POP` | 观察 2020；COG2023；2023-06-27 发布 | 用同一冻结地域的人口；密度法定概念为 population municipale。政府 Nevers 答复明确 commune 30,000 上限也按 population municipale 2020 解释。 |
| 面积 | 普查历史表 `SUPERF`，km² | COG2023 | 地域密度为成员人口之和除以成员面积之和，不能取 commune 密度简单平均。 |
| EPCI-FP | 历史 composition 工作簿 | 2023-01-01 | 1,232 个真实法国本土 EPCI-FP；`ZZZZZZZZZ / Sans objet` 不是第 1,233 个 EPCI。 |
| bassin | BV2022 历史 composition | 2022 是分区定义；commune 地理为 2023-01-01 | 1,681 个法国本土 bassin；BV2022 不是人口或收入观察年。历史档案原始上线日期未单独确证。 |
| département | 96 个法国本土 département | COG2023，2020 指标 | 原 C 条收入分布分母没有重复写“métropole”；96 个本土单元复算出官方 21,665，而含公开收入的海外单元 98 个所得为 21,620。 |
| 山区 | 1985 Loi Montagne 第 3 条名单 | 可获得档案为 COG2022，2022-03-23 发布 | 只提供涉及法律山区的 commune 及历史合并信息，没有 commune 内山区人口数；先做历史代码检查，仍保留精确份额缺失。 |

45 个 Paris/Lyon/Marseille 市辖 arrondissement 行不与整个城市行重复相加。较早发布的 COG2022 法定人口表只用于概念与历史地域交叉核对，不能直接当作 COG2023 输入。收入公开值存在取整及统计保密，不能称为取得未取整个体收入数据。

## 3. 可执行的初始规则

记 commune 人口为 `p_c`，地域人口密度为 `d_g`，地域可支配收入每 consommation unit 的中位数为 `m_g`。法国本土各通道共同要求 `p_c < 30000`；等于 30,000 不满足。单个 commune 的人口上限不能改成 EPCI 或 bassin 的人口上限。

| 法律通道 | 且/或结构和准确界限 | 数据可得性 |
|---|---|---|
| II-A，普通 EPCI | commune 属于 EPCI-FP，且 `d_EPCI ≤ median(d_EPCI)`，且 `m_EPCI ≤ median(m_EPCI)` | 公开历史 composition、人口面积及 EPCI 收入都已获得。原条款没有另外要求 INSEE rural grid 分类。 |
| II-A，孤立岛 commune | CGCT L.5210-1-1 V 例外 commune 用自己的密度及收入，比较与 A 相同的两个全国 EPCI 阈值 | 四个例外为 22016、29083、29155、85113，不能共用一个虚构 EPCI 或 cluster。 |
| II-B，bassin 补充 | `d_BV ≤ median(d_BV)` 且 `m_BV ≤ median(m_BV)`；还须区域 prefect 认为公共利益足以提出补充名单，最终由两部长 arrêté 决定 | 数值条件可复算；全国完整提议、批准及实际路径表未找到。公开数值合格只能编码为 `B_numerically_possible`。 |
| II-C，département | `d_DEP < 35` 且 `m_DEP ≤ median(m_DEP)` | 严格 `<35`，不是 `≤35`；13 个本土 département 合格：04、05、09、12、15、23、32、36、46、48、52、55、58。 |
| II-D，山区 EPCI | EPCI 中 `山区人口 / 总人口 ≥ 0.5`，且 `d_EPCI ≤ median(d_EPCI)`，且 `m_EPCI ≤ Q75(m_EPCI)` | 缺少精确山区人口。不能以山区 commune 个数占比、面积占比、massif 或农业山区名单替代。 |
| II-E，海外 | Guyane commune；Réunion décret 划定 ZSAR 内的地域 | 不纳入本土 EPCI 阈值域；Réunion 部分 commune 不能按整个 commune 全覆盖解释。 |

同一 commune 可以同时满足多条通道。A、C 以及已完全确认的 D 是法律分类条件；B 的数值条件还须行政程序。完整分类由 arrêté 决定，重叠候选不能人为指定唯一实际路径。III 的 FRR+ 是另外的强化层，并非上述 2024 socle 的补充资格通道。

| 比较量 | 同期官方显示阈值 | 本次公开输入复算值 | 分母/方法 |
|---|---:|---:|---|
| A/D EPCI 密度中位数 | 63.57 | 63.569845464551264 | 1,232 个真实本土 EPCI 密度的中位数。 |
| A EPCI 收入中位数 | 21,570 | 21,570 | 同一 1,232 个 EPCI 的直接 `MED20`，地域等权。 |
| D EPCI 收入第 75 百分位 | 22,822.5 | 22,822.5 | 公开 `MED20` 的线性插值 Q75 匹配；官方软件的具体分位数算法未单独确认。 |
| B bassin 密度中位数 | 70.84 | 70.84363836218742 | 1,681 个本土 BV2022 密度。 |
| B bassin 收入中位数 | 21,600 | 21,600 | 1,681 个本土 bassin 的直接 `MED20`。 |
| C département 收入中位数 | 21,665 | 21,665 | 96 个本土 département 的直接 `MED20`。 |

阈值判定用复算完整精度密度，63.57/70.84 只是官方两位小数显示，不能据显示值创造边界内外差异。Q75 的数值重现也不构成对行政软件算法或原始未取整指标的完整复制。

可运行的三值规则见 `docs/sources/assignment2024/candidate_rules.py`：`True` 为满足，`False` 为已知必要条件失败，`None/NaN` 为未知。多个必要条件中任一已知失败时，该通道为 False，即使另一条件缺失。29083 Île-de-Sein 的 commune 收入仍为 NaN；其密度 443.3333 已高于 A 阈值，因此 A 为 False，不能给保密收入补值，也无需把这个通道误标为悬而未决。

## 4. 山地人口上界与区划审查

官方 `mountain_cog2022.xlsx` 的 `Perimetre` 有 5,611 行，`CommunesFusionnees` 有 233 条历史合并记录。该档案可能包含部分地域受分类的 commune，未给出实际山区人口比例。

当前全国重构把任何涉及山区、或 COG2022 中尚不存在而须保守处理的 COG2023 commune 的全部人口放入山区人口**上界**，其余成员放 0。该上界达到 50% 仅表示 D 仍可能成立；上界低于 50% 才排除 D。上界达到 50% 不能证明 D 实际满足。

独立检查 INSEE 官方 COG 变动表中 `2022-01-01 < DATE_EFF ≤ 2023-01-01` 的 79 条记录，未发现“保留旧代码、吸收旧山区成员，但既未在山区名单出现也未被新代码 unknown 标记覆盖”的存续 commune。检查结果保存在 `docs/sources/assignment2024/independent_assignment_checks.json`。这核对的是公开区划变动，不是对 COG 文件不记载的法律山区边界调整作证明，也没有恢复 commune 内山区人口。

收入阈值设计需要清除 D 的较宽收入资格。最保守做法是排除任何有山区成员或山区地域未知成员的整个 EPCI，且不得依据正在研究的收入 score 再决定是否排除山区。密度阈值设计若固定 `m_EPCI ≤ 21570`，D 与 A 共用同一个密度必要条件，D 不再构成越过该密度 cutoff 的独立分类通道，因此无需仅因存在山区成员而删去全部山区 EPCI。

## 5. 原始名单与候选集合的独立数值核对

3,009 个地域指标由独立脚本重新按官方 composition 汇总人口面积，并直接连接各地域收入中位数。人口和收入的最大差为 0；密度最大差小于 `5×10^-13`，是浮点误差。计数分母为 COG2023 的 34,816 个法国本土 commune；不应与经过多年区划稳定性限制后的实证样本分母混用。

定义 `M = A_EPCI ∪ A_isolated ∪ C`，`B*` 为 bassin 数值条件，`D*` 为山区人口上界达到 50% 且其他 D 条件满足。原始名单与这些集合的关系如下。

| 不属于 M 的 commune | 列入原始 arrêté | 未列入 | 解释 |
|---|---:|---:|---|
| B*=False、D*=False | 0 | 17,144 | 没有本次重构的候选路径。 |
| B*=True、D*=False | 3,013 | 0 | 在既定输入、原始法律及山地覆盖假定下，B 是解释列入的条件性必要通道。 |
| B*=False、D*=True | 304 | 0 | 只有山地人口上界路径仍可行，不能据上界宣称实际 D 赋值。 |
| B*=True、D*=True | 39 | 0 | B 与 D 候选重叠，实际路径不可分辨。 |

M 的 14,316 个 commune 全部列入；其外的 3,356 个列入者正好等于 3,013+304+39。没有 M 满足却遗漏、没有列入者完全超出候选联合集，也没有 B*/D* 候选未列入。不能因此把 B 的行政裁量改写成法定自动资格。

3,013 个条件性必要 B commune 分布于 314 个 bassin、276 个 EPCI、73 个 département。**314 是该 commune 子集中不同 bassin 的覆盖数，不是取得了 314 个 prefect 提议，也不是全国批准 bassin 数量。** 这个逻辑分解使用原始实际分类，但只用于行政路径诊断，不能用来按观察到的 treatment 选择新的 RD 样本。

个别实际 B 路径存在官方政府说明。例如 [Corsica 政府答复](https://questions.assemblee-nationale.fr/q17/17-2634QE.htm)明确 Borgo、Lucciana、Vignale 属于 bassin de Borgo；[Saint-Lô Agglo 政府答复](https://www.senat.fr/questions/base/2025/qSEQ250705373.html)说明其 13 个 classées commune 与三个合格 bassin 的关系。这些是政府回述的个案路径，不能推广成完整原始提议档案。

## 6. 阈值设计的可清除部分与实质支持

原则上可以把数值上任何可能合格的 bassin 全部排除，因此不必为了排除 B 就先取得实际提议名单。前提是使用完整、冻结地域、无缺失的数值资格信息；未知必须按可能成立处理。C 可按完整 département 指标直接清除；收入阈值另须山区屏障；四个孤立例外及海外通道单独处理。

如果研究整个 EPCI 的 outcome，屏障须对全部 EPCI 成员成立。只移除单个 commune，留下的不是整个 EPCI outcome，而是选定 commune 子域的 outcome；须另检验选中人口份额和 commune 数在 cutoff 的连续性。选择域应完全由政策前状态、法律和地域构成决定，不得依据新 FRR 与未处理标签或新 outcome 来确定。

主线程脚本的候选 A/B/D 是内部方案名，**不是 CGI II-A/II-B/II-D 的实际赋值标签**：方案 B 仍研究普通 EPCI 收入阈值，方案 D 研究共同密度阈值。三个方案共同要求政策前无旧 ZRR effects、既定多年区划稳定性、法国本土、真实 EPCI、commune 人口低于 30,000；它们不按新 FRR/未处理的观察标签选域。

| 候选设计 | 法律屏障和固定 margin | 带宽 | 合格侧 / 不合格侧 EPCI |
|---|---|---|---|
| `A_income_whole_epci_barrier` | 所有成员均无可能 B、无 C；整个 EPCI 无山区/地域未知成员；密度≤58.57 | 收入 500/750/1000/1500 | 0/2、0/4、0/5、0/6 |
| `B_income_commune_barrier` | 保留 commune 无可能 B、无 C；整个 EPCI 无山区/地域未知成员；密度≤58.57 | 收入 500/750/1000/1500 | 6/9、6/13、6/17、6/24 |
| `D_density_commune_barrier` | 保留 commune 无可能 B、无 C；固定收入≤21,270，较 A 阈值低 300 | 密度 10/15/20/30 | 0/10、0/18、1/23、1/29 |

方案 B 合格侧只有 6 个独立收入 score，包含一个 cutoff tie；最近不合格收入 score 为 +50。方案 D 最近合格密度 score 为 -16.904739847238403，最近不合格 score 为 +0.12881682129712857；密度带宽低于约 16.9 时没有合格侧。扩大带宽不能凭空产生局部合格侧。所有候选中 observed assignment 与简单 score 资格没有冲突，是有限候选域的必要核对，不构成 first stage 或 RD 连续性验证。

脚本中的“每侧至少 20 EPCI、15 个独立 score”只是筛查门槛，不是 RD 的理论充分条件。当前 0/6/1 的合格侧支持已经足以否决直接开展这一候选 RD；没有用 outcome 选择带宽，也没有报告 RD 估计。公开 MED20 的离散取整、cutoff tie、候选样本份额连续性、协变量平衡和行政选择仍须在任何替代设计中处理。

## 7. 论文可表述的边界与后续缺口

可以明确写：初始 FRR 同时依赖 EPCI、département、法律山区人口条件及行政 bassin 补充；2020/COG2023 公开指标重现全部公布阈值；原始名单在候选联合集内得到完全覆盖；实际路径记录仍不完整；当前清除其他通道后的 EPCI cutoff 支持不足，因此不实施 RD。

可用于稿件的法语表述（建议文字，未写入 manuscript）：

> Nous reconstruisons les critères initiaux à partir de la version légale applicable au 1er juillet 2024 et des données publiques de 2020 sur la géographie de 2023. Les seuils publiés sont reproduits. Sur les 34 816 communes métropolitaines, 14 316 communes classées satisfont une voie déterministe A ou C ; les 3 356 autres communes classées relèvent exclusivement de voies B ou D encore possibles. Cette concordance ne restitue ni les propositions préfectorales exhaustives ni la population située dans les parties classées en zone de montagne. Après exclusion conservatrice des voies alternatives, le soutien observé du côté éligible aux seuils d’EPCI est trop faible pour justifier une régression sur discontinuité.

不能写“全部 commune 的官方真实路径已精确复刻”“所有数值合格 bassin 自动获批”“山区名单给出了 50% 人口资格”“FRR 仅是一项企业免税 treatment”或“候选赋值吻合即证明因果识别”。指定仍是 territorial designation，实际税收/社保领取和其他地方政策渠道不由该名单观测。本轮赋值审查不修复原有比较设计的平行趋势缺陷，也不改变 HAL 暂停状态。

若继续追求收入阈值设计，应取得完整原始 prefect→minister 提议及接受记录，或对全体可能 B 单元保持保守排除；取得法律山地区域内人口或可靠的无山区成员证明；并在看到 outcome 前固定设计域与支持规则。当前调查未找到全国初始分类工作簿或路径表；对 DGCL ArcGIS 旧应用的检查显示现有图层已指向更新后的 FRR+，不能用来补初始2024路径。

## 8. 可复现记录

本轮审查基准：`src/construct/assignment2024.py` SHA256 为 `a4ab2fbe0ee74f2fbe19a3cabd0c72ae3238c61a6f127ac4c9c0218d80bfec04`。输出与输入版本 SHA256、法律规则、官方 URL、确已保存/未取得状态、条件性必要 B 定义及 RD 支持表均保存在 `reports/review_A_assignment_2024.json`。独立核对可运行：

```powershell
C:\ProgramData\anaconda3\python.exe docs/sources/assignment2024/independent_assignment_checks.py
```

该脚本只写自己的审计 JSON，不改变根级 claims、manuscript、既有回归或研究 outcome。官方下载来源与哈希见 `data/raw/assignment2024/official_download_manifest.json` 及 `reports/review_C_assignment_sources.json`；本轮未取得的文件不会被冒充为已保存。
