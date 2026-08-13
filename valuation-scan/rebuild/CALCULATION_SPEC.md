# valuation-scan 语义计算规范

版本：semantic-reconstruction-2026-08-09

本文件只描述从原项目代码、两个 valuation skill、已有指标快照和测试中核验到的计算语义。它不规定操作系统、目录、依赖、MCP、凭据或具体 API 客户端。另一个 agent 可以使用不同语言、不同数据适配器实现同一语义。

标记含义：

- CONFIRMED：原项目代码或 skill 明确实现，或已有指标/测试直接给出结果。
- LEGACY：已有产物明确使用过，但与当前源码口径存在版本差异。
- UNKNOWN：旧资料没有足够信息唯一确定，不能自行补规则。
- PRODUCT_CONFIRMATION：可以从旧资料知道存在选择，但产品负责人仍需决定未来是否保持兼容。

## 1. 适用范围与总边界

这是单标的“价格隐含现金流增长压力”扫描，不是目标价、完整 DCF、公允价值或买卖建议。

支持两类语义路径：

1. US：以年度标准化财务数据为基础，若存在合格且更新的四季度 TTM 资料，当前 Owner FCFF 可采用 TTM；历史 Revenue/NOPAT/Owner FCFF 仍按完整财年计算。
2. CN_A / CN_AH：以 A 股披露口径为基础。年度 Owner FCFF 使用经营现金流减长期资产购建现金；累计中期数据按 TTM bridge。A/H 是同一发行人的两种价格视图，不是两个发行人。

银行、保险、证券公司/券商在旧 A 股 skill 中明确返回 unsupported_financial_sector，不得套用工业企业的这套 FCFF/EV bridge。该状态如何映射到外层 failed、rejected 或单独的 unsupported，旧资料没有唯一规定，见 DECISION_LOG.md。

## 2. 通用输入规范

### 2.1 数值解析

CONFIRMED：旧计算器的数值解析行为：

- None、布尔值、无法转换为浮点数、非有限数（NaN、正负无穷）均视为缺失；
- 可转换的数字字符串转为浮点数；
- 不把缺失、字符串 MISSING 或非法数字静默当作 0；只有各字段明确写明 assumed zero 时才使用 0；
- 计算前所有参与相加/相减的数值必须属于同一币种、同一单位尺度和可比期间。

### 2.2 单位和币种

CONFIRMED：

- US 财务金额以报告币种保存；估值计算要求分析币种为 USD。报告币种不是 USD 时，只有 FX 层明确完成换算才允许使用 TTM/估值；否则回退到可用年度口径或标记缺失。
- A 股估值币种为 CNY。Tushare 的 total_mv 原始单位为“万元”，转为 CNY 时乘以 10,000；total_share 原始单位为“万股”，转为股时乘以 10,000。
- 财务报表流量（Revenue、CFO、CapEx、利润、税）按期间累计；资产负债表、现金、债务、租赁、NCI、优先/永续工具和股数为报告期末点值。
- US 标准化的 CapEx 数值保存为正的 gross CapEx（对原始资本支出取绝对值）。A 股 CONSTRUCT_LONG_ASSET 通过 max(value, 0) 变为非负长期资产购建现金。

PRODUCT_CONFIRMATION：旧 US 规范要求财务币种和市场分析币种一致，但当输入是非 USD 时，明确的 FX 转换优先级、汇率日期和跨表汇率锁定方式没有完整固定；重实现时必须把 FX 记录为显式输入和 provenance，不得隐式换汇。

### 2.3 期间和报告日期

CONFIRMED：

- US 年度行须来自 FMP annual standardized statement，优先使用 fiscalYear，没有时使用 calendarYear，再没有时使用 period_end 的年份。标准化层最多保留最近 10 个财年，但估值只要求当前、3 年前和 5 年前精确端点。
- SEC 例外补充只接受允许的年度表单（代码允许 10-K、20-F），fp=FY，排除 Q1/Q2/Q3 frame，并要求财年结束月份与发行人财年结束月份一致。
- A 股报告日期读取 REPORT_DATE，备用字段为 报告期 或 日期；支持 YYYY-MM-DD 和 YYYYMMDD。
- A 股完整财年：报告日期为 12 月 31 日，或 REPORT_TYPE 包含“年报”。
- 价格日期不得由估值代码重新请求或猜测。应优先使用数据快照的 data_as_of / analysis_date / fetch_date / fetched_at 中已有且明确的日期；若只有抓取日期而没有交易日，必须声明这是抓取日而非确认的交易日。

## 3. US 计算规范

### 3.1 US 税率

#### 公式：单年有效税率

CONFIRMED

~~~text
raw_tax_rate_y = income_tax_y / pretax_income_y
effective_tax_rate_y = min(0.50, max(0.00, raw_tax_rate_y))
~~~

- 输入变量：income_tax_y、pretax_income_y。
- 输入来源：FMP income_statement.incomeTaxExpense 与 incomeBeforeTax；SEC 备用字段见 FIELD_MAPPING.csv。
- 单位：两者同一报告币种的货币金额；税率为无量纲比例。
- 期间：同一完整财年。
- 缺失行为：任一缺失，或 pretax_income_y = 0，该年税率为缺失；不得把该年当作 0% 税率。
- 负数行为：原始税率可为负，但实际税率裁剪到 [0%, 50%]；原始值仍应保留在 provenance。
- 示例：tax=20.719B, pretax=132.729B，原始税率约 15.61%，裁剪后仍为 15.61%。
- 期望输出：raw_tax_rate、effective_tax_rate_clipped。

#### 公式：用于 Owner FCFF bridge 的税率

CONFIRMED

~~~text
tax_rate_used = mean(the latest 3 years with pretax_income > 0 and valid tax)
~~~

若有效年份少于 3 年，使用所有有效年份的平均值；没有有效年份则为缺失。

- 输入变量：各年 effective_tax_rate_y。
- 输入来源：上一个公式的结果。
- 单位：无量纲比例。
- 期间：截至选定最新完整财年；旧实现示例使用 2023/2024/2025 或 2024/2025/2026。
- 缺失行为：没有有效税率时，Owner FCFF 无法完成，估值状态不是 ready。
- 舍入：US 指标在输出前用 4 位小数的比例值；当前源码的 `compute_prescreen_tax_rate` 返回未舍入平均值，bridge 也使用未舍入平均值。已有 MSFT 指标产物的 bridge 组件显示使用了 0.1842，而未舍入平均值约为 0.1841907886；这是版本差异，黄金案例同时保留两种值。
- 示例：有效税率 0.1823, 0.1763, 0.1940，未舍入平均值约为 0.1841907886，legacy 产物展示/使用值为 0.1842。
- 期望输出：未舍入 `tax_rate_used`、输出显示值、及其年份列表；不能只保存一个无法解释精度的数字。

### 3.2 US NOPAT

#### 公式：单年 NOPAT

CONFIRMED

~~~text
NOPAT_y = operating_income_y * (1 - effective_tax_rate_y)
~~~

- 输入变量：operating_income_y、该年 effective_tax_rate_y。
- 输入来源：FMP income_statement.operatingIncome、FMP 税和税前利润；SEC OperatingIncomeLoss、税和税前利润候选字段。
- 单位：同一报告币种货币金额。
- 期间：完整财年；历史 NOPAT 使用逐年税率，而不是 tax_rate_used 的三年平均税率。
- 缺失行为：经营利润、税或税前利润缺失，或税前利润为 0，NOPAT 年份不可用。
- 负数行为：旧代码不把负的 operating income 自动改成正值；如果 NOPAT 非正，该年不进入 CAGR 端点。
- 示例：operating_income=155.237B，税率 0.194，NOPAT=125.126818572B。
- 期望输出：每个财年的 operating_income、raw_tax_rate、effective_tax_rate_clipped、nopat。

### 3.3 US Owner FCFF

#### 公式：年度/TTM Owner FCFF bridge

CONFIRMED（当前源码语义）

~~~text
positive_interest_expense = max(interest_expense, 0)
positive_interest_income  = max(interest_income, 0)
after_tax_interest_expense = positive_interest_expense * (1 - tax_rate_used)
after_tax_interest_income  = positive_interest_income  * (1 - tax_rate_used)

Owner_FCFF = CFO - abs(gross_CapEx)
             + after_tax_interest_expense
             - after_tax_interest_income
~~~

- 输入变量：CFO、gross_CapEx、interest_expense、interest_income、tax_rate_used。
- 输入来源：FMP cash flow netCashProvidedByOperatingActivities 或 operatingCashFlow；CapEx capitalExpenditure、capitalExpenditures 或 investmentsInPropertyPlantAndEquipment；利息字段来自 FMP income statement。
- 单位：全部为同一分析币种、同一期间的货币金额。
- 期间：年度行是完整财年；TTM 行是同一组四个离散季度的滚动累计。
- 缺失行为：CFO 或 CapEx 缺失，或税率缺失，Owner FCFF 为缺失；利息费用/收入缺失时旧代码各自假设 0 并追加显式 note，不把该情况伪装成完整披露。
- 负数行为：CapEx 取绝对值；负利息费用或负利息收入在 bridge 中裁剪到 0，但原始负值应保留并标记。
- 示例（MSFT）：182.935B - 115.948B + 3.051B*(1-0.1842) - 3.301B*(1-0.1842) = 66.78305B。
- 期望输出：Owner FCFF、四个 bridge 组件、使用税率、缺失/裁剪 notes。

LEGACY：已有 AAPL 指标的历史 FCFF 序列采用 CFO - gross CapEx，没有保存利息费用加回和利息收入扣除组件；这与当前源码的完整 bridge 不一致。AAPL 黄金案例同时保存“观察到的旧产物”和“按当前语义重算值”，不得把两者差异静默抹平。

### 3.4 US TTM 合格条件

CONFIRMED：当前 Owner FCFF 采用 TTM 仅在以下条件全部满足时成立：

1. TTM 资料存在且 statement values currency 为 USD；如果报告币种与分析币种不同，必须有已应用 FX。
2. income statement 和 cash flow statement 均标记 quarters_used=4，两者 period_end 相同。
3. 两者各自都有四个离散季度日期，日期集合相同；相邻日期间隔在 45–140 天。
4. TTM period_end 晚于最新完整年度 period_end。
5. CFO 和 CapEx 均四季度有值；正 CapEx 若未解决其符号，TTM 回退年度。
6. 利息数据可完整、部分或缺失；部分利息按报告值使用，缺失项假设 0 并记录 note。

旧 US TTM builder 已存在“最近四个季度求和”的实现。PRODUCT_CONFIRMATION：原项目资料同时讨论过 YTD + prior FY - prior same YTD，但 US 旧执行器实际验收依赖的是 provider-built four-quarter aggregate；不得把两者当成同一实现。

### 3.5 US Operating EV

#### 公式

CONFIRMED

~~~text
Operating_EV = market_cap
             + total_debt
             + max(minority_interest, 0)
             + max(preferred_stock, 0)
             + perpetual_instruments
             - broad_financial_assets_deducted
~~~

其中：

~~~text
broad_financial_assets_deducted
  = cash_and_equivalents
  + short_term_investments (若 cash 字段未包含它)
  + current_financial_assets (若有)
  + noncurrent_financial_assets (若有)
~~~

- 输入变量：market_cap、债务、NCI、优先股、永续工具、现金类资产。
- 输入来源：market quote snapshot；FMP balance sheet；SEC 只对旧 normalizer 明确列出的债务/现金字段做备用或例外补充。
- 单位：分析币种货币；market cap 是价格时点，资产负债表组件是同一最新报告期末。
- 期间：优先使用与 Owner FCFF 对应或不晚于价格日期的最新完整资产负债表。
- 缺失行为：缺 market_cap、total_debt 或 broad_financial_assets 时，旧 US prescreen 的 missing_inputs 包含对应字段，估值 block 不为 ready。NCI、preferred、perpetual 的处理有明确零默认见下文。
- 负数行为：NCI 和 preferred 只加入非负值；perpetual 工具在旧 US prescreen 没有可用字段，固定为 0 并记录 perpetual_instruments_unavailable_assumed_zero。
- 示例（MSFT）：3,450.801596T + 128.8083B + 0 + 0 + 0 - 76.843B = 3,502.766896T。
- 期望输出：EV、所有组件、债务口径说明、现金类扣除明细。

#### 债务与租赁处理

CONFIRMED：

- FMP totalDebt 存在时，直接信任该总债务；租赁负债不再单独加入 EV，防止双重计算。
- FMP 直接总债务缺失但债务组件存在时，先计算短期债务 + 一年内到期长期债务 + 长期债务；若有租赁负债，使用 max(债务组件合计, 租赁负债)，并记录 derived source。
- 所有债务组件都缺失但有租赁负债时，租赁负债是最低债务 fallback。
- 现金字段若已经是 cashAndShortTermInvestments，不得再次加 shortTermInvestments；否则按 cash + STI。更宽的 current/noncurrent financial assets 仅在字段存在时加入。

UNKNOWN：美国租赁负债在各供应商字段之间的完整同义词覆盖、以及 SEC 端 NCI/优先股/永续工具的唯一 taxonomy 映射，旧资料未形成完整一致的字段集；重实现必须保留字段来源和“未映射”，不能借普通债务标签猜测。

## 4. A 股计算规范

### 4.1 A 股年度 Owner FCFF

#### 公式

CONFIRMED

~~~text
gross_construct_long_asset = max(CONSTRUCT_LONG_ASSET, 0)
Owner_FCFF_FY = NETCASH_OPERATE - gross_construct_long_asset
~~~

- 输入变量：NETCASH_OPERATE、CONSTRUCT_LONG_ASSET。
- 输入来源：Tushare cashflow 的 NETCASH_OPERATE、CONSTRUCT_LONG_ASSET；AKShare public-source financial fallback 使用同语义字段，字段名必须在适配层明确转换。
- 单位：CNY；Tushare 现金流通常是报表原始货币金额，不按“万元”再乘倍数，除非适配器的实际返回 schema 明确声明了其他单位。
- 期间：完整 FY。
- 缺失行为：任一字段缺失，年度 Owner FCFF 为缺失；不得用单个季度或半年度累计值直接年化。
- 负数行为：长期资产购建现金通过 max(value,0)；CFO 的负值保留，因此可能得到负的 Owner FCFF。
- 示例（600519 观察到的 TTM components）：CFO 79,622,900,612.10，长期资产购建 2,831,282,151.49，FCFF 76,791,618,460.61。
- 期望输出：Owner FCFF、CFO、CapEx、basis=FY 或 fallback basis。

### 4.2 A 股累计中期 TTM bridge

#### 公式

CONFIRMED

对 CFO 和长期资产购建现金分别做同一桥接：

~~~text
TTM_CFO = latest_YTD_CFO + prior_FY_CFO - prior_same_YTD_CFO
TTM_Construct = latest_YTD_Construct
                + prior_FY_Construct
                - prior_same_YTD_Construct
TTM_Owner_FCFF = TTM_CFO - TTM_Construct
~~~

- 输入变量：最新累计中期、上一完整财年、上一年同月同日累计中期的两个现金流字段。
- 输入来源：Tushare/AKShare cashflow records；原始行必须按 REPORT_DATE 去重后使用。
- 单位：同一 CNY 单位。
- 期间：最新累计中期报告日期作为 TTM period_end。
- 缺失行为：缺上一 FY、缺上一年同 YTD、或缺任一组件时，不能做 TTM。若有完整 FY，使用最新完整 FY 并标记 FY_fallback；若无完整 FY，允许 YTD_partial，但必须标记 partial，不能把它当成年度可比值。
- 日期匹配：上一同 YTD 使用上一年相同月和日，不是“最接近日期”的模糊匹配。
- 示例（600519）：
  - CFO = 26,909,891,269.13 + 61,522,204,989.35 - 8,809,195,646.38 = 79,622,900,612.10；
  - Construct = 604,791,583.89 + 3,127,594,916.41 - 901,104,348.81 = 2,831,282,151.49；
  - FCFF = 76,791,618,460.61。
- 期望输出：桥接的六个原始输入、两个 TTM 组件、公式文本、period_end、basis=TTM。

### 4.3 A 股财年、去重和重述

CONFIRMED：

- 每个 REPORT_DATE 只保留一行。
- 同日期优先 UPDATE_FLAG=1；其次 ANN_DATE 较晚；再次 F_ANN_DATE 较晚。
- 没有这些字段的 AKShare 行比较相等，保留先出现的行。
- 这是旧代码实际的“重述/更正”处理：它通过 update flag 或公告日期选择候选行，并不保证跨来源完全重述一致。

PRODUCT_CONFIRMATION：是否把“晚公告行”定义为对同一期间的正式重述、以及是否要保存旧值与新值双轨，旧资料没有单独的产品规则。重实现至少要把被舍弃行数量和选择依据留在 provenance。

### 4.4 A 股 NOPAT

#### 公式

CONFIRMED

~~~text
raw_tax_rate_y = INCOME_TAX_y / TOTAL_PROFIT_y
effective_tax_rate_y = min(0.50, max(0.00, raw_tax_rate_y))
NOPAT_y = OPERATE_PROFIT_y * (1 - effective_tax_rate_y)
~~~

- 输入变量：TOTAL_OPERATE_INCOME（备用 OPERATE_INCOME）、OPERATE_PROFIT、TOTAL_PROFIT、INCOME_TAX。
- 输入来源：Tushare income；AKShare fallback 映射到同一语义字段。
- 单位：CNY；年度完整 FY。
- 缺失行为：Revenue 缺失只影响 Revenue CAGR；OPERATE_PROFIT、税前利润或税缺失则 NOPAT 该年不可用。
- 负数行为：税率按 0%–50% 裁剪；NOPAT 可为负，但不得进入正数 CAGR 端点。
- 示例：OPERATE_PROFIT=100, TOTAL_PROFIT=120, INCOME_TAX=24，税率 20%，NOPAT=80。
- 期望输出：年度 revenue map、NOPAT map、字段 provenance。

### 4.5 A 股 Operating EV

#### 公式

CONFIRMED

~~~text
debt = SHORT_LOAN
     + NONCURRENT_LIAB_1YEAR
     + LONG_LOAN
     + BOND_PAYABLE
     + SHORT_BOND_PAYABLE
     + SHORT_FIN_PAYABLE

cash_like = MONETARYFUNDS
          + TRADING_FINANCIAL_ASSETS
          + OTHER_CURRENT_FINASSET

Operating_EV = market_cap
             + debt
             + LEASE_LIAB
             + MINORITY_EQUITY
             + preferred_instruments
             + perpetual_instruments
             - cash_like
~~~

- 输入变量：市场价值、六类债务、租赁、NCI、优先工具、永续工具、现金及金融资产。
- 输入来源：Tushare daily_basic/quote、balancesheet；字段见 FIELD_MAPPING.csv。
- 单位：CNY；市场价值是价格日期的值，资产负债表组件是最新报告期末点值。
- 缺失行为：旧 A 股实现对这些 EV 组件逐项 assumed_zero 并写 notes，而不是把每个缺失组件列为 missing_inputs；但市场 cap、FCFF 和必要的 A/H market-cap 输入缺失会使结果 partial。
- 负数行为：组件读取使用 nonnegative；负数变为 0 并应留 note。市场 cap 只有正值才作为有效市值。
- 示例（600519）：债务 53,309,216；租赁 189,112,340.75；NCI 10,241,850,759.42；现金 48,786,691,397.55；market cap 1,688,359,999,999.9998；EV=1,650,057,580,918.6196。
- 期望输出：EV、各组件、每个 assumed-zero note、market-cap basis。

#### A 股 market cap 选择

CONFIRMED：

1. A-only：优先使用 provider 的正 market_cap；否则用正 price * verified_total_shares；否则缺失。
2. total_share/股本字段不能自动当作已核验的发行股数，除非 share-count provenance 明确允许；旧代码允许显式 verified shares 或合格已有快照复用。
3. A/H：不得把 A vendor market cap 和 H vendor market cap 相加；按下一节单独计算两条 price legs。

## 5. A/H 双重上市

### 5.1 Consolidated market value

CONFIRMED

使用一套已核验的 A 股和 H 股发行股数：

~~~text
A_leg_CNY = A_shares * A_price_CNY
H_leg_CNY = H_shares * H_price_HKD * HKD_CNY
combined_market_cap_CNY = A_leg_CNY + H_leg_CNY
equivalent_shares = A_shares + H_shares
~~~

- A/H 股数必须来自同一发行人、同一已核验股本结构；不得用资产负债表“股本”字段替代。
- H leg 可直接使用已核验的 H market cap CNY；若没有，则用 H price × H shares × FX。
- A/H 股数和市场价值必须能内部核对；旧 share-structure 逻辑要求总股数与 A/H 分项和的差异不超过 max(1股, total*1e-8)。

### 5.2 Alternative price views

CONFIRMED：A 价和 H 价是同一公司的替代 whole-company price views，不可相加为人类展示 headline。

~~~text
A_view_market_cap = A_price_CNY * equivalent_shares
A_view_EV = A_view_market_cap + debt_like_adjustments - cash_like_assets

H_price_CNY = H_leg_CNY / H_shares
H_view_market_cap = H_price_CNY * equivalent_shares
H_view_EV = H_view_market_cap + debt_like_adjustments - cash_like_assets
~~~

两条 view 共享：Owner FCFF、财务期间、历史 Revenue/NOPAT/FCFF 参考。每条 view 分别计算 Yield、reverse-DCF implied 5Y CAGR、gap 和 pressure label。旧实现可保留 combined EV 供内部兼容，但不得把它作为唯一人类展示值。

UNKNOWN：A/H 价格日期不一致时采用哪个共同 as-of 日、FX 使用 bid/ask/mid/close 哪一个，旧资料没有产品级统一规则；必须在输入中显式给出 price_date、fx_date、fx_method，否则标记 partial 或 UNKNOWN。

## 6. 历史增长率和压力

### 6.1 精确 3Y/5Y CAGR

#### 公式

CONFIRMED

~~~text
CAGR(metric, end_year, n) = (metric[end_year] / metric[end_year-n]) ** (1/n) - 1
~~~

- 输入变量：metric 为 Revenue、NOPAT 或年度 Owner FCFF；end_year；n=3 或 5。
- 输入来源：US 标准化年度 map；A 股完整 FY map。
- 单位：分子分母必须同币种、同 metric；结果无量纲比例。
- 期间：恰好相隔 3 或 5 个财年；不做插值、不用最近年份替代、不把 interim 当 FY。
- 缺失行为：任一端点缺失，状态 missing_exact_window；任一端点 <=0、非有限或无效，状态 non_positive_or_invalid_values；值为 null，不得设为 0。
- 示例：MSFT Revenue 2021–2026：(331.839/168.088)^(1/5)-1 = 14.5719%，US 输出比例四舍五入到 0.1457。
- 期望输出：status, value, start_year, end_year, period_years。

### 6.2 历史 reference、gap 和 pressure

CONFIRMED：收集六个候选：revenue_3y、revenue_5y、nopat_3y、nopat_5y、fcff_3y、fcff_5y。过滤 null 后：

~~~text
conservative_floor_cagr = min(all valid six CAGRs)
gap = implied_owner_fcff_cagr_5y - conservative_floor_cagr
~~~

pressure 边界：

| gap | label | 含义 |
|---:|---|---|
| gap <= 0.02 | light | 较轻 |
| 0.02 < gap <= 0.08 | explainable | 可解释 |
| 0.08 < gap <= 0.15 | stretched | 紧张 |
| gap > 0.15 | high_pressure | 高压 |
| gap 缺失 | not_assessed | 未评估 |

US 另有 primary_historical_cagr：优先用 FCFF，在可用窗口中选择较大的 3Y/5Y 值作补充比较；headline pressure 仍使用最低有效 CAGR。A 股旧实现只保留相同的最低有效规则，600519 旧快照只提供 FCFF 3Y/5Y，因此其历史 reference 不是完整六项 reference。

### 6.3 NOPAT 与 FCFF 历史口径的版本差异

LEGACY：AAPL 旧指标的 fcff_3y=-0.0395、fcff_5y=0.0613 来自旧的 CFO-CapEx 结果；按当前源码的 after-tax interest bridge 从相同 normalized rows 重算会得到略有不同值。MSFT 旧指标与当前 bridge 在 4 位比例规则下可对齐。详细差异和产品选择见 DECISION_LOG.md 与 GOLDEN_CASES.json。

## 7. Reverse DCF：反推五年 Owner FCFF CAGR

### 7.1 现金流现值公式

CONFIRMED：给定当前 FCFF_0 和增长率 g：

~~~text
FCFF_t = FCFF_0 * (1 + g)^t

PV_explicit = Σ[t=1..N] FCFF_0 * (1+g)^t / (1+r)^t

FCFF_N_terminal = FCFF_0 * (1+g)^N * (1+g_terminal)
Terminal_Value = FCFF_N_terminal / (r - g_terminal)
PV_terminal = Terminal_Value / (1+r)^N

V(g) = PV_explicit + PV_terminal
~~~

- 输入变量：FCFF_0、g、r、g_terminal、N。
- 输入来源：Owner FCFF bridge；固定估值参数；Operating EV 作为目标值。
- 单位：金额均为分析币种，V(g) 与 Operating EV 相同。
- 期间：显式预测 N 个年度，terminal 从第 N 年后开始。
- 缺失行为：FCFF_0 或 EV 缺失/非正，solver=invalid_inputs；r <= g_terminal，solver=invalid_hurdle_terminal_spread。
- 示例参数：N=5, r=0.10, g_terminal=0.00，所以 Terminal_Value = FCFF_5/0.10。
- 期望输出：给定 g 的企业价值，以及反解后的 g。

### 7.2 固定估值尺和求解器

CONFIRMED：

- explicit_years = 5；
- hurdle_rate = 0.10；
- terminal_growth = 0.00；
- g 搜索区间 [-0.95, 1.00]；
- 如果 EV <= V(-0.95)，solver=below_lower_bound；
- 如果 EV >= V(1.00)，solver=above_upper_bound；
- 否则执行 80 次二分，目标是 V(g)=EV；
- US 输出 g 四舍五入 4 位比例；A 股旧执行器输出 g 四舍五入 6 位比例。

PRODUCT_CONFIRMATION：A 股历史 CAGR 未统一四舍五入，而 reverse solver 统一 6 位；是否将 US/A 股所有比例统一到一个协议精度，旧资料未决定。

## 8. 状态判定

### 8.1 计算 block

CONFIRMED：

- ready：核心输入齐全且计算成功。US 核心输入至少包括 market cap、total debt、broad financial assets、有效税率、CFO、CapEx 和有效 reverse DCF 输入；A 股至少包括 market cap、可用 FCFF、必要的 EV 组件和 reverse DCF 输入。A 股可选组件的零默认必须写 notes。
- partial：执行过程能产出结构化结果，但缺少核心数据、TTM bridge、完整 FY、market cap、A/H 股数或历史比较的一部分。A 股旧实现将 missing_inputs 非空、YTD_partial 或缺少 CFO/CapEx 的结果标为 partial。
- failed：无法读取/解析输入，或执行器在生成结构化结果前发生未分类 fatal error；不得用已有旧数值拼接成成功结果。
- unsupported_financial_sector：金融企业的能力边界状态，skill 明确要求返回该枚举；它不是工业 FCFF 计算的 partial。

### 8.2 pressure/diagnostic block

即使 EV/FCFF 可以计算，若 implied growth 或所有历史 CAGR 缺失，pressure 必须为 not_assessed。旧 US prescreen 的 valuation status 可能仍因核心 EV/FCFF 完整而为 ready，而 expectation diagnostic 单独为 missing_required_inputs；重实现应保留两个状态，不要把它们混成一个布尔值。

## 9. 不能由旧资料唯一确定的事项摘要

完整清单在 DECISION_LOG.md，最重要的包括：

1. AAPL 旧 FCFF 历史序列与当前 after-tax interest bridge 的版本差异；
2. US 非 USD 的 FX 日期、汇率类型和跨表换算锁定；
3. SEC 端 NCI、preferred、perpetual 的完整统一字段；
4. A/H 价格日期不一致及 HKD/CNY 的 bid/ask/mid 选择；
5. FMP 相同 fiscal year 多行到底是重述还是输入顺序优先；
6. A 股缺失 EV 组件使用 0 的适用边界，以及是否应将它们提升为 partial；
7. unsupported_financial_sector 与 terminal failed/rejected 的外层映射；
8. A 股历史 CAGR 与 US 历史 CAGR 的统一舍入精度。
