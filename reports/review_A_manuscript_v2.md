# REVIEW A — 新增制度重构的稿件终审

日期：2026-10-04。实际审读 `paper/main_fr.tex`、`paper/appendix_fr.tex`、三张生成赋值表、`paper/generated/facts.tex`、原始历史法律及赋值审计；另读 V 的冻结协议 §§10–11 和 assignment-only 接口，没有读取 V 的登记结果或运行 RD。未修改正文、生成器、根级 claims 或已有结果。逐文件 SHA256 和 11 项制度宏的实际展开值保存在 `review_A_manuscript_v2_scope.json`。

结论：新增重构及其数字总体有可核验依据，已经正确区分 B 数值条件与行政决定、D 人口上界与实际山地资格、分类与领取优惠。发现一项生成宏错误，主线程已修复并经本审查确认；仍需下面几处精确化。**无因果识别不是以数据重构、测量和诊断为贡献的工作论文当然不可公开的理由。** 制度审查也不替代作者终审、新的 V 结果审查或整稿质量判断。

## 已查出并修复：314 被错误显示为 340

初次实际读取 `facts.tex` 时，`AssignmentBOnlyBVN` 展开为 340；同一 3,013 commune 的独立筛选明确给出 314 个不同 bassin。主线程确认原因是生成器读取 CSV 时行政代码出现 int/string 混合推断，已为行政代码显式设置 `str`，并设置 `low_memory=False` 后重新生成。

本审查随后重新读取当前宏，确认 **314**，并用当前路径表的 `listed_only_potential_B_or_D & eligible_B_potential & ~eligible_D_potential` 复算出 3,013 commune / 314 bassin / 276 EPCI。原始路径 CSV 没有这项错误，错误发生在宏生成读取阶段。当前修复生成器 SHA256：`6cbb694bf9f2ede0c1193d41972098c5d8ae8d6b7bc79045e66a24ef343af5ff`。此项状态为已解决，不应保留“340 个官方获批 bassin”之类说法。

11 项宏全部核验：34,816、17,672、14,316、3,356、17,144、3,013、304、39、314、6、1。三张赋值表的数值与本审查及 REVIEW C 一致；未仅核对宏名称。

## 必须精确化的文字与来源

行号对应本次快照；主线程后续插入 V 部分时，以节标题和段落开头定位。

### V2-R02：阈值来源、C 的收入分母与 B 的最终行政程序

位置：主稿 §3.2 第二段，当前 `main_fr.tex:43`。

现有 `médiane départementale` 容易被读成单个 département 自己的收入中位数；C 的比较对象应是各 département 收入中位数构成的分布。数字阈值也不能只由一般法律脚注支持，因为原法条写分位数、不写所有具体金额。建议整个段落替换为：

> Les seuils du tableau~\ref{tab:thresholds} correspondent aux valeurs publiées décrivant les règles initiales de la loi de finances pour 2024. Les densités affichées sont arrondies ; les tests emploient les médianes recalculées avant arrondi. La voie de droit commun A requiert densité et revenu EPCI inférieurs ou égaux aux médianes métropolitaines. La voie départementale C retient une densité strictement inférieure à 35 et un niveau de vie médian inférieur ou égal à la médiane des niveaux de vie médians par département ; treize départements satisfont cette intersection. La voie montagne D conserve le seuil de densité EPCI, relève celui de revenu au troisième quartile et exige au moins la moitié de la population dans les zones définies par l’article 3 de la loi Montagne de 1985. La voie bassin B requiert les deux seuils de bassin, une proposition du préfet de région motivée par l’intérêt général et un classement par arrêté interministériel. La limite de population s’applique à la commune à classer : une grande ville membre d’un bassin ne rend pas tous les autres membres inéligibles.\footnote{\source{https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049130324/2024-07-01/}{CGI 44 quindecies A, version applicable au 1er juillet 2024}, II et IV ; \source{https://www.assemblee-nationale.fr/dyn/17/rapports/cion-dvp/l17b0486-tviii_rapport-avis.pdf}{Assemblée nationale, avis n° 486-VIII, 25 octobre 2024}, p. 18.}

已核实：1232 EPCI、1681 bassin、96 département 的指标分布复现全部六个阈值。C 原条文没有再次明写其收入分布分母为 métropole；公开行政阈值 21,665 与本土 96 个分布匹配，含公开收入海外单元的 98 个分布为 21,620。现有表列 96 正确，不能扩展成“把所有公开 département 行一概纳入同一分布”。Q75 的公开值匹配也不证明已获得行政软件的原始算法或未取整微观收入。

### V2-R03：山地 COG2022 档案与 COG2023 重构的对应必须可见

位置：主稿 §3.2 第四段，当前 `main_fr.tex:49`。前文统一介绍 COG2023，当前山地段落没有披露档案实际为 COG2022；这会使读者误认为已有冻结2023年的精确山地资料。建议替换为：

> L’archive officielle DGALN-SIDAUH de la loi Montagne utilisée ici est exprimée dans le COG 2022. Elle identifie les communes concernées, y compris certaines parties de communes, et les fusions historiques, sans fournir la population résidant dans les seules parties classées. La population entière des communes concernées, ou dont la correspondance est incertaine, définit un \emph{majorant} de la part de population de montagne. Le raccordement au COG 2023 est contrôlé avec les mouvements officiels, y compris les modifications conservant un code communal. Ce contrôle ne reconstitue pas la population infracommunale ni d’éventuelles modifications du zonage juridique absentes du fichier de mouvements. Le majorant reste conditionnel à la couverture de l’archive utilisée. Les critères numériques B déterminent une qualification possible sans observer les propositions préfectorales. « Possible » ne signifie donc pas « effectivement accordé par cette voie ».\footnote{\source{https://www.data.gouv.fr/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022}{DGALN-SIDAUH, communes de la loi Montagne en COG2022}, ressource du 23 mars 2022 ; les contrôles de correspondance sont documentés dans les rapports institutionnel et de données.}

Cette formulation préserve la possibilité d’utiliser une exclusion conservatrice et une union de chemins possibles. Elle ne transforme pas un fichier de présence en mesure du seuil de 50 % de population.

L’audit des 79 mouvements enregistrés entre les deux dates de géographie n’a trouvé aucun code survivant absorbant un ancien membre montagne qui aurait été omis à la fois de la liste et du drapeau d’incertitude. REVIEW C a séparément identifié 10 cibles de changement de périmètre/code et aucune ancienne commune montagne parmi ces cibles. Ces deux comptages portent sur des objets différents et ne sont pas contradictoires. Le test « code existe déjà en 2022 » n’est pas à lui seul une preuve de stabilité territoriale ; le contrôle des mouvements est nécessaire. Aucun de ces contrôles ne mesure la population classée dans une commune partielle.

### V2-R04：固定样本并不等于只使用政策前特征

位置：主稿 §5.3 第一段，当前 `main_fr.tex:131`；也应在即将插入的 V 部分适用。

`analysis_stable` 排除从2017起至 COG2026 数据中记载的非更名区划变动；因此包含2025/2026信息。现有文字说“champ fixe”而没有直接谎称纯事前筛选，但为评价阈值设计必须披露这一区别。在介绍稳定域之后添加：

> Le contrôle de stabilité utilise aussi les mouvements recensés après juillet 2024 jusqu’au COG 2026. Il est fixé avant ces estimations, mais ne constitue pas un filtre composé exclusivement de caractéristiques antérieures à la politique ; sa couverture autour du seuil doit être examinée.

现有 V 协议 §11 已正确要求报告完整 BV 与 selected commune 的人口/成员覆盖、被 A/C/D 屏蔽的份额及行政变化。正文不能把“读新 Y 前固定”扩展成“法律赋值前完全决定”。如果报告 V 的单位是选中 commune 子域，其 outcome 不能被命名为整个 bassin 的全部经济活动。

### V2-R05：工作论文质量门槛须与因果识别门槛分开

位置：主稿结论第二段，当前 `main_fr.tex:189`。现有最后一句要求解决识别限制之后才可扩散，超出了现在以测量、重构和诊断为贡献的工作论文范围。建议整个段落替换为：

> Le projet fournit une reconstruction de l’exposition, des mesures administratives et des diagnostics reproductibles. Ce document de travail limite ses conclusions aux faits établis et rend explicites les hypothèses d’une éventuelle interprétation causale. La diffusion sous le nom de l’auteur reste soumise aux vérifications finales de la chaîne de données, de la cohérence de l’analyse et du texte, ainsi qu’à sa validation scientifique et éditoriale. Aucun dépôt HAL n’a été effectué pour cette version.

附录 §6 最后一句，当前 `appendix_fr.tex:57`，也应避免让“没有因果效应识别”自动成为非因果工作论文不可公开的理由。可替换为：

> Les limites d’identification sont maintenues dans les conclusions. Les vérifications internes ne permettent pas d’affirmer qu’un auteur humain ou un éditeur francophone a déjà relu et approuvé cette version, et aucun dépôt scientifique achevé n’est déclaré.

这些建议不声称稿件已经可提交，也不声称真人作者、母语编辑或同行审稿者已经完成审读。本轮没有创建、注册或提交 HAL 记录。

## 已通过的重点与允许的表述

**B 裁量。** §3.2 的最后一句明确“集合一致不是外生性证明”，正确。所有数值上可能者与原始名单吻合只是在已观测单元和输入中的对应。3,013 条件性 B-only commune /314 basin 是排除其他重构通道之后的逻辑诊断，不是原始提议表，也不能推出区域 prefect 在反事实边界附近随机提议。

**V 可以继续审查。** 上轮对 0/6/1 的否决只针对原始 EPCI 设计域 A/B/D。V 使用实际 BV 收入 21,600，不是这些 EPCI 方案的重命名。assignment-only 接口在 ±1000 中有119个低收入合格侧、79个高收入侧，67/56 distinct scores、1个 tie，样本名单资格对应无冲突，满足冻结操作支持线。足够支持与清晰第一阶段不证明 potential outcome continuity、selection continuity 或有效空间推断。V 的制度目标可表述为数值阈值与初始地域指定的局部比较；只有完整新增诊断支持时才能给予对应因果解释。本轮未读新 Y，不预判 V 的最终估计。

**四个岛。** §3.2 当前把四个没有 EPCI 的 commune 放入 A 的自身指标规则，正确；`Sans objet` 不是共同 EPCI。可以明确追加 `mentionnées au V de l’article L.5210-1-1 du CGCT`，但不得推广成任意一个未知 EPCI 代码都适用例外。实际四码22016/29083/29155/85113中只有29155满足A并列入。29083收入保密未补值，已知密度失败即排除A，符合三值 AND。V 选中域要求真实EPCI，实际未包含这四个例外；完整BV依赖接口使用各自COMMUNE primitive，没有假共享ZZ节点。

**人口年份。** 同期部长发言确认 recensement/Filosofi2020；INSEE 发布日期早于2023-07-01。法律明示密度采用 municipal population，政府 Nevers 答复明确30,000 commune上限使用municipale2020。当前正文已分开可得性日期、观察年和地域年份。建议在§3.2第一段增一句 `Le plafond communal est appliqué à la population municipale de 2020`，脚注可加[Nevers政府答复](https://www.senat.fr/questions/base/2025/qSEQ250102997.html)；属于来源精确化，不是发现原计算使用错年。加入V后要分别交代：既有commune比较的固定rate denominator是2021，V冻结rate denominator是2020，不应统称全部比率使用同一年。

**集合吻合。** 原始本土34,816中列入17,672；M=A∪C（含岛例外）14,316，剩余3,356=3,013+304+39；未列入17,144。当前摘要、表注和最后段均表明未观察具体行政原因，属有意义的全国一致性结果。加入山地档案年代及覆盖假定后，可保留“重构联合集与名单一致”的表述；不可改成“官方真实策略逐 commune 精确识别”。

**D 的法律状态。** D 在真实50%人口资格满足时也是强制法律分类通道。当前表述“voies obligatoires regroupent A et C”结合注释是指本次可核验的强制路径，建议为最大清晰度改成 `Les voies obligatoires vérifiées regroupent A [...] et C ; la voie D reste possible faute de population classée observée.` 不能让读者误以为 D 在法律上与 B 一样裁量。

**摘要的 EPCI 限定。** 当前 `Les voies EPCI sans qualification alternative...` 对A/B/D仍正确，没有否决所有 BV 设计。当新增 V 正式结果进入摘要，应单独介绍 V 和其诊断，不得保留泛化的“所有阈值设计支持不足”说法；目前稿件尚未这样泛化。

## 新增 claim inventory 与终审范围

`reports/assignment_claims_audit.csv` 单独记录此次新增制度及重构事实，字段为 `claim,paper_location,source_url,source_type,verified,notes`。派生数字明确标注为从官方资料独立计算，未冒充官方文档逐项打印的数字；条件性B/D结论保留条件；未在稿件断言的V信息标为源审计专用，最新实际断言的位置见下方补核。没有覆盖、重写或直接合并根级43条制度claims。

初审主稿SHA256为 `661232178efc6413a0df0f76587bd6e788285ca952e694a4081700c357f429cb`，附录为 `c8ada00b4c50488516c9e8c1889b602dae2ec5ce3d6cd33303d261fb95917cd7`。此后文字和V结果加入，需要按新快照复核相应位置；本报告不虚构已审读将来的稿件。

## 完成前对最新制度和方法段落的补核

主线程随后加入V部分并由语言审查更新表达。为避免把旧问题报告为仍未处理，本审查再次只读§3.2、§5.3、新增§5.4方法及结论相关段落，没有核验V的结果表或估计值。此时主稿SHA256为`62701b0611341b7e9e824dde7adc41761e95aab9fe40bdbdf99642062950e4c8`；其他更新哈希保存在scope JSON的`later_institutional_only_recheck`。

- §3.2第1段改为“recensement et des fichiers Filosofi, tous deux de 2020”，以及密度为人口总和/面积总和，含义正确；岛屿`Sans objet`改写也正确。
- 新增§5.4第一段(`main_fr.tex:138`)明确bassin收入21600、density≤65.84，保留119/79独立bassin，实际名单暴露与数值阈值逐市镇对应；最后明确prefect提议不因此随机。两个119/79宏已核验。建议把`ne satisfont ni A, ni C, ni le majorant de D`精确写成`ne satisfont ni A, ni C, ni les conditions de la voie D évaluées à partir du majorant de population de montagne`；Dpossible为多个必要条件的交集，并非只比较山地人口上界。
- 新增§5.4第2段(`:140`)已明确V用2020人口、selected target population，并披露稳定域使用政策之后的区划信息。**V2-R04对V现已解决**；原§5.3可作交叉引用，无需重复冗长声明。既有commune率用2021而V用2020的区分也已经落实。
- 原EPCI方案仍明确没有应用RD，新增V单列，不存在把0/6/1设计偷偷改名为有充分支持的方案的问题。
- V2-R02（阈值脚注及C分母）、V2-R03（山地档案COG2022披露）、V2-R05（非因果论文公开条件）在这次补核时仍待应用；结论第二段移至`:210`。
- 新增claim inventory共**42行**；V的119/79支持和事后稳定筛选两行已更新到当前§5.4实际断言的位置，其余V源审计专用事实仍标专用。根级claims未改。

这次补核只为制度和方法叙述，不能被称为已审通过V的估计、全月诊断、推断或其新增结果。
