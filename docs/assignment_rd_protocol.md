# FRR 2024：法定赋值阈值设计的前估计协议

记录日期：2026-10-04，Asia/Hong_Kong。REVIEW B。**此协议是在已有边界、全国比较及匹配比较结果和完整前趋势拒绝已知之后制定的设计恢复协议；不是原研究的事前注册，也不能声称研究者未见过结果。制定时尚未读取任何新的 RD 结果变量汇总、断点估计或其显著性。** 可以先读取法律、赋值变量、人口、政策历史、空间组成、原始资格名单和不含研究结果变量的支持计数。任何后续偏离必须保留原协议、日期、理由及当时是否已见新结果。

本协议不修改现有 DID、匹配、边界或论文。新设计即使通过，也不能追溯使原来的因果解释成立。

## 1. 法定规则与冻结来源

以 [CGI 44 quindecies A 的历史版本，2024-07-01—2025-02-16](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069577/LEGISCTA000025913960/2024-09-03/?anchor=LEGIARTI000048846182) 和 [2024 年 6 月 19 日初始 arrêté](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820) 为资格基准；2025 年增补或当前网页不得替代初始名单。初始名单 17,717 个代码，COG 2023，实施日 2024-07-01；本项目的官方提取清单及 SHA-256 已留存。

赋值使用 2023-01-01 的 EPCI périmètre，以及截至 2023-07-01 可得的 INSEE 数据。人口密度用 population municipale；不能用现有回归的 population_2021 或当前人口直接重算法定密度。

| 路径 | 初始 2024 年条件及阈值 | 本设计处理 |
|---|---|---|
| 常规 EPCI-FP | 市镇人口 <30,000；EPCI 密度 ≤63.57；EPCI 可支配收入 UC 中位数 ≤€21,570 | 主收入断点与辅助密度断点的来源 |
| 山地 EPCI | 山地人口占比 ≥50%；同一密度阈值；收入 ≤€22,822.5 | 收入候选排除任何含山地市镇的整 EPCI，作为保守上界屏障；密度候选可保留，见第 3 节 |
| bassin de vie | 拟纳入市镇人口 <30,000，BV 密度 ≤70.84、收入 ≤€21,600；仍需 préfet de région 基于 intérêt général 提议 | 人口门槛逐市镇适用，**不要求 BV 全部成员 <30,000**；只满足指标不代表实际获选；保守排除所有潜在合格 BV，不按观察到的 classified reason 删点 |
| département | 市镇人口 <30,000；省密度严格 <35；省收入 ≤€21,665 | 排除合格省份或其相应市镇；跨省 EPCI 扫描所有成员 |
| 无 EPCI 的特殊市镇 | 法律另用市镇指标 | 不混入 EPCI RD |

数值来源是 [DGCL FAQ juillet 2025](https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/FAQ%20FRR_MAJ%20juillet2025.pdf) 第 5—6 页明确归于 **LFI 2024 初始条件**的章节；已读取本地 `data/raw/faq_2025.pdf`。2024-09-13 FAQ 旧网址本次 HTTP 404，不能声称已读取该旧 PDF。山地的法律人口份额与“任一山地成员”筛选不是同一条件：后者是预定的过度排除，必须据实标注。

[INSEE Filosofi 2020](https://www.insee.fr/fr/statistiques/6692392) 于 2023-04-24 发布，当前下载提供 COG 2023 的 EPCI/BV/省收入指标。使用其 EPCI 原生中位数，**不得平均市镇中位数代替 EPCI 中位数**。项目已复算收入全国中位数 €21,570 和线性分位数 Q75 €22,822.5。文件后来有更新说明；需核实所需 EPCI/BV/省字段是否受修订、保留下载哈希，并完成法定名单复现，才能认定其等同实际赋值数据。人口 2020 于 2022-12-29 公布、当时法定地理为 COG 2022；须用可审核的 COG 2023 转换重建，而非凭文件年份直接认定正确。

合格省份固定为 04、05、09、12、15、23、32、36、46、48、52、55、58。潜在 BV 仅按其密度/收入指标判断，个人市镇的人口门槛另算；BV 中有 ≥30,000 大城不能证明整个 BV 不合格。若某一 BV 赋值字段缺失，可将该 BV 当作“不能证明不合格”保守排除，并单列这部分额外排除数量，不能把缺失当不合格。

## 2. 固定单位、政策前集合与端点

赋值和独立观测单位为**真实 EPCI-FP 2023**，每 EPCI 一个聚合端点。`ZZZZZZZZZ` 表示 Sans objet，无 EPCI 岛屿；必须排除该占位值，不能当一个 EPCI 或一个共同聚类。市镇数量、SIRET 数或月数不是 RD 的独立样本量。

先定义固定市镇集合 S_g：metropolitan；按赋值人口 <30,000；2017—2024-06-30 从未处于 ZRR 或保留 ZRR 效果范围；可在 2019—2024 的共同地理中精确对应。历史政策状态不完整、部分覆盖或地理转换不明确的市镇，先作为赋值资料问题处理。**不得用 2025/2026 FRR 状态、是否进入 FRR、当前存续、后期结果或现有 NEW/NEVER 分组定义 S_g。** 上、下阈值均执行同一规则。2023—2024 EPCI 变化本身不自动推翻 2023 法定赋值范围；保留初始名单与法定 périmètre 的逐市镇复现，另报排除成员变化 EPCI 的预定敏感性。跨省 EPCI 主样本保留，另报全部排除的敏感性。

主端点沿用已有已审计面板的 `establishment_births`：**全部行政 établissement 创建登记**。它不是已经领取减免的企业，也不等于经济上纯新生；NAF/法律形式不能精确识别个体税收资格。每个 S_g 汇总 2024 年 7—12 月的计数，以固定政策前人口总量为分母：

\[
Y_{g,2024H2}=\frac{1000\sum_{c\in S_g}\sum_{t=Jul\ldots Dec\,2024} establishment\_births_{ct}}{6\sum_{c\in S_g}P_{c,2020}}.
\]

这是每千固定居民的月均登记率，EPCI 内人口加权，EPCI 间不再额外人口加权。人口、地理和数据口径哈希先冻结。第二端点固定为同集合的 `births_without_recorded_continuity`，仅排除已记录的经济连续性，作为 succession 测量敏感性；不是纯新生或精准税收合格入口，不替代主端点。部门、雇主、退出、存续等不作本轮新增确认性端点。

**新 Y 前纠正记录：** 初稿将 II-B 人口限定误读为全部 BV 成员，并写入不存在的 `eligible_entries` 字段；已复读历史法律第 181—184 行并据主线程核实的现有已验证 schema 修正。主线程确认此时尚未新 Y 汇总/估计。此纠正不依据任何新结果；原先说法不可沿用。

主 RD 使用 **2024H2 水平**。2019—2022 各年 H2 以及 2019-01—2023-05 的全部月份，是新阈值样本的历史断点诊断。2023-06—2024-06 全部报告为公布/立法/实施之间的过渡期，不冒充清洁处理前。研究对象是初始资格安排在 2024H2 的短期局部响应，可能包含预期；不能仅凭实施日期分离预期效应或解释为全国净新增。

## 3. 三个平行、固定的候选

**A：收入 RD 主候选，整 EPCI 路径屏障。** 在完整 2023 EPCI 成员表扫描任一山地市镇、任一潜在合格 BV 成员、任一上述合格省成员，出现任一即排除整 EPCI；扫描不能只看 S_g。保留收入和密度资料完整、S_g 非空的 EPCI，固定密度 **≤58.57 =63.57−5**。运行变量 x_g=income_g−21,570，资格方向 Z_g=1{x_g≤0}。5 hab/km² 缓冲不得按 Y 或前断点改变。

**B：收入 RD 平行候选，市镇路径屏障。** 山地仍排除整 EPCI；从政策前固定市镇集合中仅去掉潜在合格 BV 和合格省的市镇，剩余非空集合按 EPCI 聚合；固定相同密度 ≤58.57、收入断点、端点和带宽。B 的目标是剩余未享旧政策的市镇；不是 A 失败后选择的补救样本。未纳入市镇的 BV/省暴露仍可能产生 EPCI 内溢出，B 不能凭 own eligibility 干净就声称无干扰。

**D：密度 RD 辅助候选。** 运行变量 x_g=density_g−63.57；固定收入 **≤€21,270 =21,570−300**；使用 A 式整 EPCI 的 BV/省路径屏障，S_g 同第 2 节。这里山地不构成绕开密度门槛的资格路径：普通和山地都在同一密度门槛切换，且固定收入满足二者。故山地可保留，但须单列山地构成与预定排除山地敏感性。密度带宽固定 ±5、±10、±15 hab/km²，支持主窗口 ±10。不得把收入/密度两个边缘和角点归一化后随意混合成一个分数。

三个候选的样本、人口覆盖、赋值一致性和支持**先同时报告**。不能依照新系数、前断点 p 值或显著性在 A/B/D 中挑一个“通过”的设计。可以在不读新 Y 的前提下依据下列支持规则决定是否进入正式估计，但原主候选 A 必须保留在报告中；B 不自动升级为 A 的同一目标。

## 4. 先于新 Y 的赋值和支持门槛

先输出每个剔除步骤的 EPCI 数、市镇数、固定人口；收入每个窗口 **±500、±750、±1,000、±1,500 欧元**全部报告，主支持窗口固定 ±1,000。左右分别统计真实 EPCI 数、distinct scores、距阈值最近的距离、阈值 ties、潜在路径、S_g 为空的数量、旧 ZRR 剩余份额、固定人口、纳入人口/全 EPCI 人口比例、跨省成员及缺失。界外质量问题不能选择性剔除阈值一侧。

对每个保留市镇对照初始官方名单，核验 Z_g 是否确实决定新增资格；公布全部不一致及原因。**不得删除 actual eligibility 与 Z 不吻合的 EPCI 后再声称 sharp RD。** 要先修复人口、地理、赋值年份、路径或官方提取；仍有不明差异则暂停 sharp-eligibility 解释。可报告 Z 的 reduced form，但不能在未解决赋值及其他政策同时断点时直接命名 FRR 因果效应。

本研究预定的最低运行条件是：主支持窗口两侧各 ≥20 个真实 EPCI、各 ≥15 个 distinct scores；设计矩阵满秩、没有单位完全决定局部截距；左右需接近阈值的支持，全部公开。该数值是本项目避免极小样本的操作门槛，**不是文献保证、功效保证或因果证据**。若未满足，就记录支持不足；不靠放宽 buffer、扩大主带宽或复制月份增加样本量。

## 5. 估计与推断的固定规则

第一轮固定窗口展示是两侧允许不同斜率的 local linear，三角 kernel：

\[
\min_{a,\tau,b_-,b_+}\sum_g (1-|x_g|/h)_+ [Y_g-a-\tau Z_g-b_-x_gZ_g-b_+x_g(1-Z_g)]^2.
\]

\tau 是收入/密度较低一侧减较高一侧的截距差。窗口端点权重为零；支持计数和有效权重观测数都报。收入四个 h、密度三个 h 全部展示，主展示分别 h=1,000 和 h=10。基本方差 HC3；另一套允许省内相关的聚类方差使用 EPCI—département 共属关系的 connected components：跨省 EPCI 连接其各省，同一 connected component 聚类；不能按某个唯一“主省”忽略共属。两套都不以较小者作结论。报告名义及有效聚类数、最大份额、杠杆；少于 30 个 component 不把常规 cluster t 视为充分证据。

这些固定 h 的常规 HC3/聚类区间反映抽样或依赖不确定性，**没有自动控制局部拟合偏误**；不能作为最终“RD 已通过”的依据。支持与赋值核验合格后，在读取新 Y 前记录正式 `rdrobust` 的软件版本和命令。正式报告 local linear p=1、bias fit q=2、triangular kernel、`mserd` 带宽规则及 robust bias-corrected 区间，同时列 uncorrected estimate、bias-corrected estimate、h、b 和左右有效 N。可用预定带宽选择算法读取 Y；这必须据实披露，不能声称带宽完全不使用结果。不得人工在不同 selectors、bandwidth caps 或 p 值中选最有利项。正式 RBC 算法若无法在可接受支持/空间依赖条件下工作，就报告无法取得可靠区间，而不是改名 HC3 为 RBC。

可预定加入 2019—2022 H2 平均入口率的加性协变量作为精度敏感性，主规格不加；协变量本身在阈值处的连续性须审查。以 post−pre 作 Y 是另外的 difference-in-discontinuities，需要反事实断点随时间稳定；本轮不把它当主 RD，也不能据其结果覆盖 post-level 或 pre-placebo 失败。登记税收领取不可观测，**不估计领取税收减免的 fuzzy RD/LATE**；资格若 sharp 也只是 bundle eligibility 的局部效应。

## 6. 诊断、停止规则与多重结果

收入公开到 10 欧元的离散度、阈值 ties 和密度精度必须核验。报告全分布、阈值附近支持和赋值图。不能通过 score clustering、HC3 或 wild bootstrap解决离散支持的拟合偏误；有限 distinct scores 需要额外平滑限制/有界曲率的诚实区间，或者停止连续型 RD 推断。主样本不设结果驱动 donut。

固定诊断包括：density/manipulation check（离散和全国中位数机械性质须注明）；原 EPCI 人口、密度或收入的非运行维度、旧 ZRR 人口份额、S_g 人口及其占全 EPCI 比例、BV/省/山地暴露份额、缺失/地理排除比例的断点；2019—2022 四个年度 H2 入口率及 2019-01—2023-05 全月度断点图和联合检验。全部月份保留；联合协方差秩不足时报告秩与不可识别限制，不能偷偷删月份。过渡期 13 个月全部报告。

阈值密度平滑与 baseline p>0.05 都不证明交换性。明显且经济上重要的历史入口、政策份额、覆盖率或地理构成断点，或者存在共用同一阈值的其他政策，会阻止单一 FRR 因果解释。不能靠选择 p 大的窄窗口修复。对诊断不拒绝但很宽的区间说明检测能力不足；不把缺乏检验力当通过。

local randomisation **不作为目前已认可的设计**。只有政策环境能支持指定窗口内近似随机分数、潜在结果不再随分数变化以及明确 EPCI 赋值/空间依赖机制时，才可另行冻结 LR 协议；不是“窗口内 balance 没拒绝”就能运行任意排列检验获得因果性。当前收入和密度都是结构性地区特征，尚无足够这种实质论证。

A 是主候选；B 和 D 的结果必须并列且清楚标为不同目标/辅助边缘。两端点以及多候选的确认性检验若进入正文，固定组成一个 family 并报告 Holm 校正；带宽序列以完整敏感性呈现，不挑一个 p 当确认性结果。无论系数为正、负或不显著，支持、赋值、测量、连续性、推断和人类终审门槛相同。

## 7. 实际打开的方法来源与限度

- [Calonico, Cattaneo & Titiunik (2014), Econometrica 82:2295–2326](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf)，DOI 10.3982/ECTA11757。已打开全文并读识别、离散变量限制及 RBC 部分。固定/最优带宽常规区间可能有偏；RBC 方差须计入 bias estimation 的不确定性。
- [Cattaneo, Frandsen & Titiunik (2015), Journal of Causal Inference 3:1–24](https://titiunik.github.io/files/publications/CattaneoFrandsenTitiunik2015-JCI.pdf)，DOI **10.1515/jci-2013-0010**。已打开全文并读 Assumption 1、随机机制和 window selection。LR 的恒定/排除限制强于单纯连续性；分组赋值机制需对应 EPCI。
- [Cattaneo & Titiunik (2022), Annual Review of Economics 14:821–851；公开作者稿](https://arxiv.org/pdf/2108.09400)。已打开并读 continuity、local randomisation、validation。两框架不同；诊断未拒绝不等于假设成立。
- [Cattaneo, Titiunik & Vazquez-Bare (2020), Stata Journal 20:866–891](https://rdpackages.github.io/references/Cattaneo-Titiunik-VazquezBare_2020_Stata.pdf)，DOI 10.1177/1536867X20976320。已打开全文并读 multiscore §2.3；资格区域有一整条边界，各点目标不同，归一化 pooling 需要目标和权重论证。
- [Kolesár & Rothe (2018), AER 108:2277–2304](https://www.aeaweb.org/articles?id=10.1257%2Faer.20160945)，DOI 10.1257/aer.20160945；[已打开的作者公开稿](https://arxiv.org/pdf/1606.04086)。已读离散支持与 score clustering 问题；不可把同分数聚类当对模型偏误的保险。

## 8. 冻结时的状态

法律门槛和公开收入来源有证据；原始赋值名单可得。A/B/D 的完整支持计数、人口密度法定 vintage 复现、所有资格路径、阈值附近赋值一致性、局部历史结果和正式区间尚未通过。因此本协议仅授权进行透明的可行性审查和预定估计，不是因果、署名或 HAL 清稿证明。人类终审仍未完成，HAL 尚未提交。

## 9. 新 Y 之前的支持审查：关闭 A/B/D

在第 1—8 节制定后，主线程完成 `src/construct/assignment2024.py`，REVIEW B 独立用源输入重新生成筛选、聚合和支持计数，不调用其估计或读取研究 Y。收入 A/B 数字与 `reports/rd_assignment_only_support.csv` 一致：

| 候选 | ±500 | ±750 | ±1,000 | ±1,500 | 判断 |
|---|---:|---:|---:|---:|---|
| A，资格侧/非资格侧 EPCI | 0/2 | 0/4 | 0/5 | 0/6 | 缺一侧，不能估计 RD |
| B，资格侧/非资格侧 EPCI | 6/9 | 6/13 | 6/17 | 6/24 | 资格侧仅 6 distinct scores，阈值 tie 1；全序列不达最低运行线 |

协议 D 的整 EPCI BV/省屏障在 density ±5/±10/±15 为 **0/0、0/1、0/1**。主线程另外形成更宽松的 **D_commune** BV/省市镇屏障；它不替代协议 D，属于 assignment-only 的支持上界核查。在相同三窗口为 **0/5、0/10、0/18**。把 D_commune 再扩至 ±20/±30 也分别仅 1/23、1/29，唯一资格侧距门槛 16.90474 hab/km²。这不提供局部支持，也不能靠加入月份改变独立 N。

此阶段公开数据重建的全国 median density 为 63.569845464551264、BV median density 为 70.84363836218742，与公布值舍入一致；上述密度支持复算使用这些精确中位数，非伪造官方提供了该精度。收入 buffer 58.57、income≤21,270 沿用冻结值。所有主候选样本中预测与初始名单无冲突，**但“冲突为零”不弥补缺一侧或极少 distinct scores**。

因此 **A/B/D 关闭，不进行新 Y 汇总、RD 回归或 RBC 清稿**。若另审保留替代路径的 criterion reduced form，必须作为新目标、单列协议和赋值诊断；不得声称 A/B/D 已通过，也不能把它悄悄当原 sharp-eligibility RD。

独立复核输入 SHA-256：`assignment2024_commune_paths.csv` 9636c4c20a6e389f5aed81c8ffba4dde292aee8b7beb0a0e9c0803175029d8ca；`assignment2024_territory_indicators.csv` a6fbe3af92217576e60d9c87506364b997b072bf5bcb6be0b70ddb44a039d990；`commune_treatment.csv` b5f7cedaed23d0dedbe93ec427bacbb29d11e625085044ea08febc84522ca8c8；支持表 41377e93af83d48f809e89bc3c527d6c7b31fc0ed9228259a0244c733bc2baff。

## 10. 最后两项 assignment-only 筛查的冻结

这是在 A/B/D 的 assignment-only 支持不足已知之后、仍未读取任何新研究 Y 时提出的两个**新目标**。只允许一次有限的支持/初始资格暴露核查；不得把它们作为前述候选已通过的替代证明。若不够支持，关闭；不继续改变目标和缓冲无限搜索。

**E：常规 EPCI 收入条件 reduced form。** 同样使用真实 EPCI 2023、固定 `density<=58.57`、income cutoff €21,570、收入四窗口 ±500/750/1,000/1,500（主支持 ±1,000）、S_g 的人口和历史旧政策限制。保留山地、BV、省替代资格；**不按实际是否eligible或路径排除市镇**。S_g 使用现有 metadata 的 metropolitan、`prior_zrr_effects==False`、`analysis_stable==True`，及法定人口 <30,000、真实EPCI条件。分析时必须交代 `analysis_stable` 的行政变化日期范围：若用到了2025/2026地理变化，它只是事先固定的测量限制，不应声称完全由处理前特征定义；其选择/覆盖断点需要审查。E目标为满足常规收入条件的局部ITT，不是整体FRR从0到1的sharp效应。

**V：BV 收入门槛候选。** 使用 BV2022/COG2023为独立观测；固定BV density≤65.84=70.84−5；收入 cutoff €21,600、同四欧元窗口（主支持±1,000）。从上述固定市镇集合中，只保留 `eligible_A_epci==False`、`eligible_A_isolated_commune==False`、`eligible_C_department==False`、`eligible_D_potential==False` 的市镇，即先排除其他强制路径和山地可能路径。BV人口条件仍逐市镇适用。缺失字段、非空集合和剔除份额全部报告。`D_potential`只是不确定山地人口的上界；否定它可保守排除D通道，肯定它不证明实际山地资格。不能通过actualB选中与否筛样本；prefect discretionary proposal仍未观察。

两路线先算有效单位N、distinct scores、ties、最近左右距离、固定人口/市镇和实际名单对应的初始FRR人口份额F、各侧的F范围及局部first-stage跳变。F以初始名单和固定人口定义，不能以Z本身替代。first stage采用第5节同一固定h、p1/triangular、HC3；这只是**资格赋值资料**的diagnostic，不读取登记Y，不取代正式RBC/空间依赖判断。阈值左右各≥20有效单位、≥15distinct的操作线沿用，first-stage区间与实质大小需报告；不以F的显著性挑另一个h。V即使名单样本吻合阈值，也仍需说明prefect裁量在反事实附近的机制。

任何后续研究Y都必须另记录新目标的protocol、source/hash、实际支持结论、推断和完整前期诊断规则；本节不能自动授权税收take-up或population-share Wald LATE。若推进E/V的post-level，沿用第2节 `establishment_births` 主端点、without-recorded-continuity敏感性、2019-01—2023-05全部诊断和2024H2窗口，不截短前期。

## 11. V 的正式前 Y 分析协议

§10已经冻结后完成assignment-only支持审查：E不达运行线，关闭；V在所有四窗口足够，故只推进V。本节仍在主线程未读取新研究Y汇总/估计前冻结；没有为了结果更好而选择V。A/B/D/E的失败、§10的全部支持和first-stage记录必须保留。

**V样本完全沿用§10**：BV density≤65.84、固定non-ZRR/non-beneficiary、个人population<30,000、真实EPCI/共同地理；A_epci、A_isolated、C、potentialD全部否；不依据actual FRR或Y再删点。按选中市镇固定人口聚合为每BV一行。主端点唯一：`establishment_births` 的2024Jul–Dec月均/1,000固定pop2020；主post-level，不减去pre，不新增行业或税收eligible筛选。

**运行变量方向明确处理threshold tie：** 令 `x=21600-BV_income2020`，`c=0`，则高收入未eligible在左、低收入含等号eligible在右；官方`rdrobust`默认 x≥c归右侧，正好符合法律≤income条件。返回正系数表示低收入eligible侧减高收入侧。不得直接用income作x再把原软件的阈值等号归高收入侧；至少1个BV等于€21,600。

**唯一主规格：** 官方`rdrobust`，`p=1,q=2,h=1000,b=1000,kernel='triangular',masspoints='adjust',c=0,vce='hc3',level=95`，无额外EPCI/BV人口weights、无covariates、无fuzzy。主报告conventional point、bias-corrected point、robust-bias-corrected SE/CI/p及h/b、N_h、N_b、distinct scores、warnings。h=b明确固定（rho=1），**不同时声称主带宽为mserd自动选择**。四固定窗口所有500/750/1000/1500均用相同p/q/kernel与各自b=h，并列报告全部；主要确认性结论只用h1000。官方masspoints adjustment不能被解释为它已解决所有离散支持偏误。缺秩/支持/报错时报告失败，不静默扩h或换高阶拟合。

可另报`mserd`作为预定探索性带宽敏感性，不能据p值升级替代主规格；其算法使用Y应明确。当前Anaconda环境查询未发现rdrobust已安装，实际实现者须在读新Y之前记录官方release或commit/version、源URL/hash及实际命令。本轮已打开[官方Python源码](https://raw.githubusercontent.com/rdpackages/rdrobust/master/Python/rdrobust/src/rdrobust/rdrobust.py)核实固定h时默认rho1/b=h、masspoints以及方向规则；不能把自行WLS HC3改名RBC。

**预期与前期诊断：** 2019Jan–2023May所有53个月的相同BV集合入口率断点全部报告，固定h1000；2019/2020/2021/2022 Jul–Dec年度placebo分别用同规格，完整展示。全月联合检验报告使用的covariance估计、秩和可估限制；不能只删低p月份取得满秩，也不能用4个同H2不拒绝覆盖全月失败。2023Jun–2024Jun过渡13个月全部展示、明确不属于清洁pre。任何pre跳变不得通过移除BV、改密度buffer/年限/primaryh“修好”。

**完整协变量/选择接口先固定：** full BV人口、density、full commune N；selected commune N/pop与两者coverage；old-ZRR及unknown-history人口份额；A、isolatedA、C、potentialD各自以及其并集被屏蔽的full-BV人口比例和固定prepolicy集合中的比例；administrative/membershipchange及missing-geography比例；fullBV中EPCI收入分布、≤€21,570与€22,822.5的人口比例、BV收入与所属EPCI收入重合的比例/差值；同一EPCI是否跨BV收入阈值两侧。均按固定窗口和相同运行变量审查，不只选择balanced变量。历史状态缺失不是old-ZRR=0。主要协变量审查给估计和区间；p大不自动通过。

**dependency接口：** BV为赋值和结果聚合N，不自动是独立误差单位。根据所选市镇的全部EPCI和departement成员关系构造BV共属图，分别报告EPCI-only、dep-only、EPCI+dep connected components、cross-role share、最大component及按BV计数的size-effective G；另报用全部BV成员关系构造的更保守图。不能用majority-EPCI或majority-department给BV赋单一cluster。固定主HC3 RBC表达BV间独立误差的基准；同h/b的component-cluster RBC敏感性必须并列，不按哪套显著择优。官方版本实际cluster方差类型须显式指定并记录；若joint components过少或高度不均，正常临界值/CR1不充分，不能将HC3显著当推断gate通过。独立SE与cluster SE不是必然大小有序。

**探索性结果：** `births_without_recorded_continuity`、雇主或其他代理仅探索性、先列可测口径和完整清单，并在其检验family内报告Holm；没有按税收资格和经济纯新生定名。唯一主post outcome无需为四敏感带宽挑最低p。多项pre诊断和全部协变量家族均给未调整与Holm信息/可估联合检验；p和量级服务于可证伪审查，不作机械“所有p>0.05就通过”清单。

**gate：** V已通过最低assignment support，不等于通过continuity、measurement、RBC有限样本/空间依赖或human review。实际post estimate可以正负或接近零；因果与非因果科学gate仍按各自证据判定，不由显著性决定。

### 11.1 新Y读取前的软件和跨阈值协方差修正

主线程已在隔离 `.vendor_rd` 安装官方 Python `rdrobust 2.1.0`（配套 statsmodels 0.14.5、matplotlib 3.9.4）；没有替换原系统环境。实际运行前将软件版本、源码 SHA、协议、输入和估计脚本 SHA 写入 execution freeze。此处补充取代上文“尚未安装”的状态，而不是倒签事后注册。

REVIEW B独立读取实际安装源码确认：`rdrobust.py` 的最终 `V_tau_rb` 用左右单侧方差相加。若同一EPCI/省component同时包含阈值两侧BV，软件单侧cluster接口未加入跨侧协方差。因此 **不能把package cluster参数声称为本项目全部共属关系的完备聚类推断**。主官方HC3 RBC不变；聚类敏感性用本项目明确公开的联合模型，不能以软件默认cluster结果清稿。

对于当前固定 `h=b`、同一三角kernel、无协变量、sharp截距断点、`p=1,q=2` 的限定规格，bias-corrected点等价于两侧局部quadratic截距之差。令六列设计为左右分别 `(1,x/h,(x/h)^2)`，W为三角权重，L对右截距为+1、左为−1；`omega=L(X'WX)^−1X'W`。联合HC3用quadratic残差除以 `1-H_ii`，`H_ii=w_i X_i'(X'WX)^−1X_i`；跨月协方差用全部月份同一omega及各月残差外积。每个时期的点及对角SE须与官方RBC数值吻合后才进行联合诊断。此等价性不可直接延伸到不同b/h、不同kernel、fuzzy或协变量规格。

联合component-CR1用 `s_g=sum_{i in g}(omega_i e_i)`，方差 `G/(G−1)*(N−1)/(N−6)*sum_g s_g s_g'`，同时包含两侧score；95%敏感区间用 `t_(G−1)`。按 selected-membership 与 full-BV-membership 的EPCI、省及joint图完整报告G和集中度。该有限簇修正仍不是小G、巨大单component或空间依赖假设的保证，也不是package自动输出。主h1000的selected joint G=33、size-effective=12.367；full joint G=10、最大157/198 BV、size-effective=1.572。如此集中度是明确推断限制，不能以HC3或正常CR1显著掩盖。

全53clean-pre联合协方差若秩不足，保留全部月份，报告rank、缺秩和可估投影的描述性统计；不能称作全53限制联合检验。后续2025/2026月份如展示，仅为额外描述性时间轨迹，不改变已冻结pre、transition或2024H2 primary。所有协变量/选择和完整依赖图仍需审查；上述代码数学认可仅授权实际诊断，不授予因果或HAL清稿。
