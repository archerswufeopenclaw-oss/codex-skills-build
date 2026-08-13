# valuation-scan 决策记录与不确定性清单

版本：semantic-reconstruction-2026-08-09

本记录只保留影响“语义重实现”的判断。没有复制任何操作系统路径、依赖配置、MCP 配置、凭据或 API 认证材料。

## 1. 已确认的原项目选择

| ID | 主题 | 原项目实际选择 | 证据层级 | 重实现要求 |
|---|---|---|---|---|
| D-01 | US Owner FCFF | CFO - gross CapEx + 税后利息费用 - 税后利息收入；利息缺失各自假设 0，负利息在 bridge 中裁剪到 0 | CONFIRMED：当前 calculator 函数与 MSFT 产物 | 实现完整 bridge，并保存每个组件和 note |
| D-02 | A 股 Owner FCFF | NETCASH_OPERATE - max(CONSTRUCT_LONG_ASSET,0) | CONFIRMED：A 股 executor | 不加入 US 利息 bridge，除非产品另立规则 |
| D-03 | A 股 TTM | 最新 YTD + 上一 FY - 上一年同日期 YTD，对 CFO 和 Construct 分别桥接 | CONFIRMED：A 股 executor | 同日期匹配；桥接失败时 FY fallback 或 YTD_partial |
| D-04 | US TTM | 使用四个离散季度 provider-built aggregate；要求两张表四季度、日期集合一致、期间晚于最新 FY、币种/FX 合格 | CONFIRMED：US calculator | 不把 A 股 YTD bridge 直接套到 US |
| D-05 | 税率裁剪 | 单年 tax/pretax，裁剪到 0%–50%；US bridge 税率取最新三个正 pretax 有效年份平均 | CONFIRMED | 保留 raw rate 和 clipped rate |
| D-06 | NOPAT | US operating income*(1-effective tax)；A 股 OPERATE_PROFIT*(1-clipped INCOME_TAX/TOTAL_PROFIT) | CONFIRMED | NOPAT history 使用逐年税率，不使用三年平均税率 |
| D-07 | Operating EV US | market cap + total debt + nonnegative NCI + nonnegative preferred + perpetual - broad financial assets | CONFIRMED | 所有组件必须可追溯 |
| D-08 | Operating EV A 股 | market cap + 六项债务 + lease + NCI + preferred + perpetual - cash - trading assets - other current financial assets | CONFIRMED | 组件缺失的 assumed-zero 必须显式留下 |
| D-09 | US direct debt | FMP totalDebt 存在时直接信任；lease 不单独加入 | CONFIRMED | 防止租赁双重计算 |
| D-10 | US debt fallback | 组件合计；存在 lease 时取 max(debt components, lease)；只有 lease 时可 lease-only fallback | CONFIRMED | 不能同时把 direct total debt 和 lease 再相加 |
| D-11 | 历史 CAGR | 精确端点公式，3/5 个财年，不插值；端点缺失或非正则 null | CONFIRMED | 状态必须区分 missing_exact_window 与 non_positive_or_invalid_values |
| D-12 | pressure | 六项有效 CAGR 的最小值作为 conservative floor；gap=implied-floor；阈值 2/8/15 个百分点 | CONFIRMED | 见 CALCULATION_SPEC.md |
| D-13 | reverse DCF | 5 年、10% hurdle、0% terminal growth；g 在 -95% 到 100% 二分 80 次 | CONFIRMED | terminal denominator 必须检查 r>g_terminal |
| D-14 | A/H | A/H 是同一发行人的替代价格视图；共享 FCFF/历史 reference；分别算 A/H EV、Yield、implied CAGR、gap、pressure；不相加两条 vendor market cap | CONFIRMED：A/H skill 与 executor |
| D-15 | 金融企业 | 银行、保险、证券公司/券商返回 unsupported_financial_sector | CONFIRMED：A 股 skill | 不伪造工业企业 FCFF |
| D-16 | A 股去重 | 同 REPORT_DATE: UPDATE_FLAG=1 > ANN_DATE 晚 > F_ANN_DATE 晚；再按日期倒序 | CONFIRMED | 将选择依据写入 provenance |
| D-17 | US 财年筛选 | FMP annual standardized；SEC 例外只用允许年度表单、FY、匹配财年结束月份 | CONFIRMED | 不把季度/累计中期当年度 |
| D-18 | 输出 precision | US ratio/derived metrics 通常 4 位比例；A 股 reverse solver 6 位；A 股 historical CAGR 旧产物保留原始浮点 | CONFIRMED + LEGACY | 不在无产品决定时擅自统一精度 |

## 2. 无法由旧资料唯一确定的事项

### U-01：AAPL 历史 FCFF 的版本差异

已有 AAPL 指标观察值：

- fcff_3y = -0.0395；
- fcff_5y = 0.0613；
- Owner FCFF = 98,767,000,000；
- pressure = high_pressure。

用当前源码的完整 after-tax interest bridge 对同一年度输入重算：

- fcff_3y = -0.0397；
- fcff_5y = 0.0634；
- 当前 Owner FCFF 仍为 98,767,000,000，因为选定年度利息字段为 0。

无法从旧资料唯一确定：AAPL 指标生成时是使用了早期 CFO-CapEx 公式、不同版本的 interest 字段、还是另一个已被覆盖的 calculator。GOLDEN_CASES.json 因此同时保存 observed_legacy_output 和 canonical_spec_recomputed。产品负责人必须选“历史产物兼容”或“当前公式一致”，不能要求重实现同时只返回一个无 provenance 的数字。

### U-02：US tax_rate_used 的舍入时点

当前源码的平均函数返回未舍入均值；展示的 rates 会四舍五入。MSFT 旧指标的 bridge 组件使用 0.1842，三年未舍入平均约 0.1841907886。两者差异会使 FCFF 约差数千美元，但在 4 位 CAGR/收益率上通常不明显。

PRODUCT_CONFIRMATION：未来计算应在内部使用未舍入平均值，还是为了 legacy compatibility 在 bridge 前先四舍五入到 4 位。建议将两者都写入 receipt；若协议只能保留一个值，需负责人确认。

### U-03：US TTM bridge 的定义边界

资料中出现过两种概念：

1. provider-built 最近四季度相加；
2. latest YTD + prior FY - prior same YTD。

US 旧 calculator 的实际资格检查针对 provider-built 四季度 aggregate；A 股 executor 明确实现第二种 bridge。没有证据证明 US 两种口径在所有供应商、会计期间和 CapEx 符号下等价。不能跨市场合并。

### U-04：FMP 相同 fiscal year 的重述选择

FMP extraction 按 fiscal year 建 map，重复年份保留输入顺序中的第一行；而 SEC facts 的同 period_end 记录按 filing date 较晚者优先。A 股另有 UPDATE_FLAG/公告日期规则。

旧资料没有一条跨 provider 的“正式重述优先”产品政策。应当保留 provider 原始行、选择规则和被舍弃行数量。是否统一改成最新 filing 优先，需要产品确认。

### U-05：US 非 USD 的 FX

旧逻辑要求 statement values currency 为 USD，或存在已应用 FX；但没有完整定义：

- 使用哪个交易日/报告日；
- bid、ask、mid 还是 close；
- 财务流量和点值资产是否使用同一 FX；
- 市值与财务数据日期不一致时如何锁定。

因此这些信息不能从旧资料补猜。适配器必须把 FX rate、date、direction、source 和 applied 状态作为显式输入；缺任一关键项时保守标记 partial/UNKNOWN。

### U-06：SEC NCI、优先股和永续工具

旧 normalizer 明确列出了 Revenue、Operating Income、Tax、Pretax、CFO、CapEx、现金、短投和债务的 SEC candidates；但没有形成同样完整、唯一的 NCI、preferred、perpetual taxonomy 映射。US calculator 对缺少的 NCI/preferred 使用 0，对 perpetual 固定使用 0 并记录 unavailable。

这是 legacy fallback，不是证明这些项目经济上为零。产品负责人需决定是否扩展 SEC 字段；在扩展前不得从相似 tag 自动猜测。

### U-07：宽口径现金类资产的边界

旧 US 逻辑：

- cashAndCashEquivalents 若实际上包含 short-term investments，则不重复加；
- 否则 cash + short-term investments；
- current/noncurrent low-risk financial assets 有字段才加入；
- 缺少的宽口径资产被排除并记录 note。

没有足够资料证明所有供应商的 cash 字段语义相同，也没有为 restricted cash 设定统一扣除政策。重实现必须保存 cash field name 和“是否包含 STI”判定；restricted cash 的估值处理为 UNKNOWN，不能默认加入或扣除。

### U-08：A 股缺失 EV 组件的零默认

A 股 executor 对六项债务、lease、NCI、preferred、perpetual、现金类组件的单项缺失使用 assumed_zero；市场 cap、FCFF 和 A/H 两腿输入则会进入 missing_inputs/partial。

旧资料没有说明“缺一个可选 EV 组件就继续 ready”是否是长期产品意图，还是 fast scan 的临时容错。产品负责人需决定：保留旧行为，或把关键资本结构缺失统一提升为 partial。

### U-09：A/H 日期和 FX 选择

A/H 逻辑确认了股数、A price、H price、HKD/CNY 和替代 view 公式，但未唯一确定：

- A/H 两个交易日不同时的共同 as-of；
- FX 的 bid/ask/mid/close；
- H price 与 FX 是否必须同一时点；
- consolidated market cap 是否用于内部审计以外的任何 headline。

重实现必须显式记录这些输入；无法满足时，至少 H view 为 partial。

### U-10：shares outstanding 的经济口径

US quote 使用 price-date sharesOutstanding，profile 或 round(marketCap/price) 可作为 fallback；normalized income statement 的 weighted-average diluted shares 只是年度报表字段。A/H 则要求已核验 issued A/H share legs，不能用 share capital。

旧资料未形成跨市场统一的“issued vs weighted-average”字段协议。产品负责人需确认 receipt 是否必须同时返回 share_count_type。

### U-11：历史端点的共同 end_year

US 使用 normalized fiscal_years 的 latest year；A 股旧 executor 取 annual FCFF、Revenue、NOPAT 三个 map 的并集的最大年份，再分别计算各 metric 的 exact window。这可能导致不同 metric 实际可比覆盖不完全一致。

旧资料未决定是否要求六个历史 CAGR 共用同一财年且所有起点都存在。当前黄金案例保留旧行为；若产品要求可比性更强，需要另行确认。

### U-12：A 股历史 CAGR 精度

600519 旧 indicator 保存：

- fcff_3y = 0.2298468444787214；
- fcff_5y = 0.03327155972916218；
- implied = 0.193773。

A 股 solver 明确 round 6 位，但历史 CAGR 在旧产物中未按同一精度 round。不能从 public receipt schema 推出一个新的精度规则。

### U-13：600519 原始输入的可复现性

保留资料中有 600519 的 indicator、TTM bridge、EV 组件和历史 FCFF CAGR，但没有对应的完整原始年度 Tushare/AKShare rows。因此：

- Owner FCFF、EV、Yield、implied growth 可以按保留的中间值复核；
- Revenue/NOPAT 3Y/5Y 无法离线独立重算；
- GOLDEN_CASES 将 observed legacy receipt 标为 ready，同时把 semantic expected receipt 标为 partial provenance。

这不是数值否定，而是证据边界。

### U-14：000858.SZ

原项目保留资料中没有该标的的原始响应、缓存、fixture、indicator、报告或测试输入。黄金案例只包含标识和缺失项，所有数值为 UNKNOWN；不能以 600519、任何其他 A 股或通用合成数据代填。期望状态是 partial、pressure=not_assessed。

### U-15：失败状态的外层映射

旧资料明确了计算 block 的 ready/partial，也明确了金融企业的 unsupported_financial_sector；terminal schema 允许 execution_status=completed/failed/rejected。但没有一条唯一规则规定：

- provider 超时但已有部分输入时是 completed+partial 还是 failed；
- unsupported_financial_sector 是 rejected 还是 completed+unsupported；
- malformed receipt 是否归 executor failed 还是 router invalid。

这些是协议层产品决策，不应由计算器偷偷决定。

## 3. 产品负责人必须确认的最小集合

如果目标只是“另一个 agent 能按原语义重实现并复核四个案例”，以下保留双口径即可：

1. 是否以当前完整 US interest bridge 为规范，还是以 legacy AAPL 指标为兼容基线；
2. US tax rate 的舍入时点；
3. A 股可选 EV 缺失的 zero/default 是否继续允许 ready；
4. A/H 日期和 FX 的 as-of 规则；
5. unsupported_financial_sector 与 terminal 状态的映射；
6. 是否统一 US/A 股历史 CAGR 的精度；
7. 是否扩展 SEC NCI/preferred/perpetual 映射；
8. 是否要求所有六个历史 CAGR 使用共同 end_year 且共同可比数据集。

未确认前，重实现应：

- 按 CALCULATION_SPEC.md 执行已确认公式；
- 对 UNKNOWN 输入输出 UNKNOWN/null 和 provenance；
- 保留 observed legacy 与 canonical recomputed 两个字段；
- 不用 fallback 静默掩盖版本差异；
- 不把任何 UNKNOWN 变成 0，除非规范明确写了 assumed zero。
