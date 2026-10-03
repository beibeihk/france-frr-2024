# REVIEW B — 实际新稿最终科学范围审查

结论：**当前实际新稿已经构成具有实质贡献的非因果制度重构、行政数据测量与识别诊断working paper，达到该明确范围的公开工作论文科学标准。因果路线保持 CLOSED。** 该判断不是把原因果gate改名通过；新稿重新组织了问题、证据顺序、制度与测量结果，并把比较与RD失败作为需解释的证据。可公开工作论文不以必须识别一个因果效应为前提，也不以另聘真人同行或法语母语同行为前提。

本轮逐句审读 `paper/main_fr.tex`、`paper/appendix_fr.tex`，读取其全部生成表、引用元数据与估计实现；实际SHA及审读范围记录在配套 `review_B_final_scope.json`。原V结果已经从原始validated panel独立聚合及复算，本轮不为既有结果追加重复估计。无EPCI岛的广域/匹配修正另作一次必要独立复核，见 `review_B_broad_islands_audit.json`。我没有改论文、主估计输出或其他角色的报告。

## 实际科学范围与贡献是否落地

1. **制度重构为主体事实贡献。** 摘要、引言、制度章和结论明确说明2020原始变量、2023地理、mandatory A/C、B/D可能路径及部分mountain人口不可见。metropolitan 34,816个市镇中17,672列入，14,316 mandatory、3,356 residual，3013/304/39的剩余分解与17,144无路径未列入构成完整算术。17,717原始全清单与metropolitan、当前map和stable universe明确区别。没有从集合吻合倒推出prefect个别决策、真山地人口或外生性。
2. **登记测量定义与效度主张相称。** 新独立测量章明确dateCreation与dateDebut、全登记与税资格、历史HQ与currentHQ、单位法律/establishment、succession absence、O雇主标识、行政A状态和经济survival的区别。11,285,045 entries以及HQ/nonHQ/unknown三项恰好相加；6,953,847可定位UL不是同一经济对象。新增measurement表是source-to-aggregate口径检查，正文明确不声称与INSEE经济创造统计同范围的外部数值benchmark。这是透明的行政数据研究，而非假装已验证经济新创造或免税take-up。
3. **比较是描述性证据。** 广域和匹配near zero、边界正差异均与样本/权重绑定；正文没有称national causal null。边界774个disjoint pairs、三项匹配covariates、same-H2与May2023事件参考清楚。共同per-capita rates与count totals分开；不能把相邻control上涨当不存在spillover，也不能把设计间差异当已证明位移。就业和cohort状态也未越界。
4. **识别失败真正进入主结果。** 摘要已经包含BV支持虽足够但选择/历史断点失败；正文先报告覆盖−44.4个百分点、oldZRR份额+30.7点，完整63字段/46非恒定family、四h、完整53clean-pre、HC3与rank32/9及full-member10巨簇。主RBC0.444的HC3区间包含0明确保留；不挑较窄cluster区间。旧三设计的全pre拒绝、季节性调整后拒绝，以及弱H2检验不替代强monthly限制，都在正文落地。
5. **方法身份没有伪装。** 主h=b1000固定，非mserd；x=21600−income把tie放eligible右侧；p1/q2/triangular官方RBC及限定q2恒等写清，联合cross-side score避免软件sidewise cluster遗漏。PPML消去pair-time仍估pair intercept、finite-sample风险及相对ratio明确；没有说所有FE消去或自己侧增长5.6%。restricted wild test与nonrestricted score interval分开。post-pre、reference、primary/source freeze和事后诊断chronology亦明确。
6. **既有文献与当前主张相符。** 旧ZRR与ZFU文献没有被搬成2024FRR先验效果；空间、incidence、pair-FE与parallel-trends敏感性文献只承担实际对应的作用。新增ref11/12/13现已真实加入bib并被正文引用；分别支持RBC、离散score的拟合/推断限制、continuity/assignmentITT与receipt的区别，不支持声明本设计已通过。未把local randomisation或multicutoff无实际应用的文献塞入新稿。

本稿新增知识不仅是重印名单或公布一个失败p：它将法定多路径、vintage和旧权利转接还原为可复用数据，量化公开登记测量的不同对象，再用支持、选择和历史轨迹说明何时公开边界比较不能承担因果问题。这个证据组合符合严谨、可重复的working paper贡献。其结果不是FRR有效或无效，而是暴露、可测对象和当前识别边界。

## 必要岛屿修正的真实独立复算

`broad_and_matched.py`目前对九位真实EPCI用 `E:code`，非真实EPCI用 `C:commune_code`。在广域2,117T/14,361C中，旧字符串计数722含一个ZZ伪共同标签；真实为721个EPCI加 **22016、29083、85113** 三个独立无EPCI市镇，故 **724** clusters。三者都是control。四个全部无EPCI岛中的29155属于其他政策历史组，不在这个广域样本。

从原panel独立构造pre24个月和post6个月后，beta=−0.0067292538841104，点不变；正确724G的SE=0.0297048590801375、p=0.82084770623403、区间[−0.06504733453,0.05158882676]。反事实错误ZZ合簇得到SE=0.0297048051333264，差 **5.39468e−8**。这不是仅把输出G改成724：方差确实按三个不同primitive重算。

matched1908 pairs不含这三岛；其assignment primitives仍逐项核对正确，joint EPCI-dep图61组件、beta=−0.01714004546、SE=0.04162012164与主表一致。未来若包含孤岛，当前代码仍以C:code连接真实department，未将ZZ标签当机构。

## 本轮局部修正与完成状态

- 初读缺失的ref11/12/13已加入 `paper/references.bib`，正文已有真实对应引用；**已回核修正**。
- 初读缺失的 `AssignmentFieldChecksN`已定义为真实1,044,480；来源结果为34,816×30 fields；**已回核修正**，不是猜数。
- BV覆盖表的百分号现为正确LaTeX转义；**已回核修正**。
- main制度B句现明确“`le respect des deux seuils de bassin, une proposition ... et un classement ...`”；数值条件、prefect提案和部长决定三者连接清楚；**已回核修正**，不改法定含义。
- 附录现明确保留alternative的E路线主h1000为14/34 EPCI、eligible13 distinct scores，h1500为16/50、四h均因支持不足关闭，没有估新业务Y；**已回核修正**，失败路线审计完整。
- `log(1+y)`敏感性实际针对**月度原始count**取log，随后不除人口；main现明确 `log(1+n), n=dénombrement mensuel brut`，表标签已改“log(1+nombre)”；**已回核修正**。只改标签，无需改估计。

以上本轮提出的局部表达/披露事项均已实际落实，JSON记录本轮读取版本及回核状态，**没有剩余科学或本轮必改表达blocker**。未发现需要重做样本、改Y、筛窗口或重新搜索因果路线的问题。数字四舍五入显示p=0,000可改为<0,001，属编辑建议，不能当真实p严格等于0。

## 判定边界

**non-causal scientific working-paper scope：PASS。causal evaluation route：CLOSED。** 这是对我实际阅读及复算证据的判断，不是外部同行审稿认证或期刊录用保证。PDF完整布局、sourcepack最终内容与HAL操作不在本轮审查范围，不在此声称已完成。

AI声明准确写Codex实质参与、内部检查由AI进行、Kun Huang为sole human author并承担内容与传播责任；没有虚构作者亲自重做每个检查、真人同行审核或母语真人阅稿。本报告不额外规定必须聘请人类同行，也不替作者报告任何尚未实际发生的人类阅读、授权或HAL提交事实。作者身份、署名责任和平台法律流程须据其真实状态办理，不能由本科学范围结论制造完成记录。
