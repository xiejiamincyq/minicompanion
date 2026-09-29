# 硬件实施任务队列

更新：2026-09-29。Astra负责集成和二审；已实际调用Terra进行电源/NFC审计、Luna进行资产清点。反馈支路已从原理图和PCB移除；主板电源仍是原电路，独立候选已绘制并完成充电核心与后级连接。用户已接手软件，本任务只推进硬件及必要接口交付。每次启动硬件子任务必须展开用户规定的TASK ID/MODEL/OBJECTIVE/INPUTS/MUST KEEP/ALLOWED TO MODIFY/DO NOT MODIFY/TOOLS/VALIDATION/OUTPUT/RISK模板。

## 当前完成

- [x] HW-NFC-016-CANDIDATE：既有升压图加入TMUX1511及模块I2C接口，18器件/56引脚，旧26引脚不变，ERC和3项错接检查通过。仅候选连接完成，异常掉电联锁/电平/独立二审未完成，见validation/nfc-016/REVIEW.md。

- [x] HW-NFC-015-CANDIDATE：独立TPS61023升压评审图完成，11器件/26引脚/ERC零违规及3项错接检查通过；仅候选连接验收。两级损耗已复算，触发体验、I²C掉电、器件定型及主板集成未完成。见validation/nfc-015/REVIEW.md。

- [x] HW-PWR-012：TPS259470L输入保护候选已串入，六页71器件，ERC零违规及网表/故障注入通过；仅候选连接验收，动态保护、封装、普通USB和成本仍待完成。见validation/power-012/REVIEW.md。
- [ ] HW-PWR-013：HOST许可候选接口和限流余量修改完成，74器件ERC零违规，网表及故障注入通过；完成部分价格核对，预算与独立审查未闭环。详见validation/power-013/REVIEW.md。
- [ ] HW-PWR/NFC-014：已完成U216官方原理图、固定版本主机库和成本/续航敏感性审查，见validation/nfc-014/REVIEW.md；候选5V供电、无IRQ的待机/唤醒、国内5/10件报价，以及HOST电平与普通USB仍待完成。Type-2模拟交换可评估，不再强制Type-4。

- [x] HW-PWR-007：U1专用DLA封装、L1 DFE201612E真实料号及专用封装、SW1 PCM12SMTBR及标准封装已指派；POWER未用触点改NC，消除BBM依赖。焊盘数值、唯一网络差异和ERC校验通过；电容/背光/USB/NFC及整板集成仍未完成。

- [x] HW-PWR-006：TPS63802独立后级/机械POWER评审图；13器件、8网络、逐脚及开关故障校验通过，ERC零违规。未接入主板；生产封装、真实料号、动态电压、背光和USB/ADC反灌尚待落实。见hardware/candidates/system_power_review/README.md。

- [x] HW-BASE-001：Astra，Git/官方CLI/ERC/DRC/网表/PCB基线；报告与证据。
- [x] HW-BASE-002：Luna，资产/BOM/CPL/许可证/机械清点；Astra纠正R402归属并确认第四键排除标志。
- [x] PHASE 1产品范围记录；硬件参数未冻结。
- [x] HW-LIB-001：恢复项目库表；已提交21a55fe。
- [x] HW-FB-001：反馈六器件及TP104已移除，GPIO37/38释放；网表对比通过，官方CLI DRC零错误/零未连接，保留既有USB封装及Datasheet字段警告。详见FEEDBACK_REMOVAL.md。
- [x] HW-DISP-001：移除孤立、排除贴板的U301占位符，屏幕本体列入OFF_BOARD_ASSEMBLY.csv；FPC逐脚核对、其余网表端点不变。恢复pin_to_pin与lib_symbol_mismatch检查后ERC为0错误、24警告；提交5ff8058。未改变PCB。
- [x] HW-PWR-005-CORE：BQ24072T独立KiCad充电核心评审图，三线电池/NTC、Power Path、设定电阻及去耦；19器件15网络核对，候选ERC零违规。仅完成核心评审草图，USB控制、后级及整板集成仍未完成；见hardware/candidates/power_path_core_review/README.md。
- [ ] HW-PWR-AUDIT-001：Terra报告、Astra二审、用户已批准PowerPath+电芯NTC，进入具体设计。
- [x] HW-PWR-008：切换后系统电源及TPS60231背光候选子页；58mA名义值，ERC和独立逐脚检查通过；未集成主板，模拟全范围待验证。
- [x] HW-PWR-009：TPS70933/TUSB320LAI USB检测前端已入候选工程，32器件ERC零违规；只完成检测，未实现充电许可。
- [ ] HW-PWR-010：USB电源有效状态、充电许可组合及Default/BC1.2路径；核查旁路最大电流，随后整合充电核心与系统电源。
  - 2026-09-27已绘制TPS3808及施密特门候选，40器件ERC零违规；只完成CC条件组合。最终低压钳位、充电EN及Default/BC1.2未完成，整项保持未勾选。
  - 2026-09-28：HW-PWR-011已把CC许可接至实际充电EN；Default/BC1.2、快速掉压和前端保护仍待完成，HW-PWR-010保持未勾选。
- [x] HW-PWR-011：独立五页集成候选，BQ24072T OUT连接TPS63802，新增双通道串联EN控制；61器件ERC零违规，逐脚合约和三项故障注入通过。此项仅验收候选连接，不代表主板、USB全来源、PCB或电池安全验收；见validation/power-011/REVIEW.md。
- [ ] HW-NFC-001：Terra比较、Astra复核；两设备验证前不能宣布方案可靠。

## 依赖和验收

| ID / 模型 / 风险 | 输入与允许修改范围 | 依赖 | 验收与产物 |
|---|---|---|---|
| HW-LIB-001 / Luna / 低 | 项目sym-lib-table、fp-lib-table；不改器件网络 | 工具连接明确，基线提交 | 恢复easyeda/libs路径，CLI ERC/DRC不再缺库；不盲替USB封装 |
| HW-FB-001 / Luna / 中 | feedback页、顶层层级、MCU反馈连接及PCB对应对象；保护其余模块 | 基线、恢复点、可验证修改工具 | 删除六器件、专属走线/网络；审查TP104；37/38释放；网表差异无其他功能变化，ERC/DRC无新增电气错误 |
| HW-PWR-002 / Terra / 高 | power页及必要电源接口，先输出电源树和POWER_STATE_TABLE | 用户安全路线决策、电芯规格、NFC预算 | 充电/保护/NTC/USB限流/开关参数可核算；Astra签审后才动PCB |
| HW-NFC-002 / Terra / 高 | nfc页、GPIO接口；保留显示和三键 | NFC角色方案和模块料号、双机验证 | 两端均记录同一次相遇，重试不重复计数，失联可恢复；线束/连接器/电平确定 |
| HW-SCH-001 / Terra / 高 | MCU/top及新接口集成；保留既定MCU/显示 | 电源/NFC接口冻结 | ERC真错误清零，U301表示合理，GPIO/电平/启动脚表一致 |
| HW-LAYOUT-001 / Terra / 高 | PCB电源局部，后独立NFC连接局部 | 已审原理图 | 不改板框与关键机械点，保存覆铜DRC/网表一致；USB/电源/天线keepout复核 |
| HW-MECH-001 / Terra / 高 | case参数/模型，先修已证实版本矛盾 | 电池/NFC/开关包络 | 三键和POWER开口正确，柱孔/线束/电池厚度干涉检查；重大增大先询问 |
| HW-VERIFY-001 / Astra / 高 | 只读全设计 | 前项完成 | ERC/DRC、极性、数据表焊盘、3D、BOM/CPL二审；异常电源和RF实测计划 |
| HW-MFG-001 / Luna / 中 | 新制造输出目录，不覆盖上游包 | 设计放行 | 新Gerber/Drill/BOM/CPL对应同一提交，MANUFACTURING_NOTES和采购表完整；实际下单单独确认 |
| HW-INTERFACE-001 / Astra / 中 | 仅最终硬件接口资料，软件由用户自行负责 | 硬件冻结 | 全部GPIO/电平/电源状态与最终原理图一致；不扩写应用软件要求 |

同一KiCad工程不并行写入；Terra设计与Luna机械操作不能同时修改PCB。每阶段开始git status，结束git diff/--stat、校验、Astra审阅、小提交；禁止reset --hard、覆盖未知修改、自动push/PR。

当前安全路线已批准：推进具体电源设计，NFC模块研究并行；没有电芯、RF样机或完整工具能力时不伪造制造验收。
