# HW-PWR-012：USB输入保护候选

2026-09-28。已通过KiCad MCP新增usb_input子页，并串入现有充电/USB检测供电路径；六页、71个实际器件，ERC零违规。只完成候选连接和静态计算，不是主板或制造放行。

TASK ID：HW-PWR-012；MODEL：Astra实施、power_parts独立只读复核、Astra复算；OBJECTIVE：把输入过压切断和故障限流落入候选，核查普通USB识别路径；INPUTS：HW-PWR-011和TI正式资料；MUST KEEP：原充电/电芯NTC/POWER路径、USB原生数据功能；ALLOWED TO MODIFY：系统电源候选及本轮证据；DO NOT MODIFY：生产主板、软件、制造输出；TOOLS：KiCad MCP、官方CLI、结构化字段修复、逐脚检查；VALIDATION：网表差分、静态容差、故障注入、ERC和PDF目视；OUTPUT：本目录及usb_input.kicad_sch；RISK：动态保护、普通USB、成本与封装仍待闭合。

## 本次电路

J5.1改接VBUS_RAW，经U8 TPS259470LRPWR的IN5/OUT6进入VBUS_IN。充电器、USB侧LDO及许可逻辑均保留在后端；入口PWR_FLAG移至RAW。J101等仍是评审接口，最终主板不能另从原始VBUS绕过U8。

U8选择可调OVLO、主动限流、故障锁断版本。R13/R14=34.8k/10k设置过压门限；R15/R16=27.4k/10k设置欠压门限，均0.1%。R17=3.32k、0.1%设置故障限流。ITIMER悬空取最短响应，AUXOFF和FLT未使用并明确NC。C17=2.2nF、5%、50V C0G设置正常启动斜率。C15=1µF/50V、C16=2.2µF/10V；真实料号及偏压有效容量仍需定型。R18=100k提供后端泄放负载，并不意味着拔线即清零。

| 条件计算 | 结果 |
|---|---|
| OV上升门限，计入0.1%电阻及±0.1µA漏电 | 5.288–5.491V |
| OV恢复门限 | 4.810–5.011V |
| UV上升门限 | 4.415–4.583V |
| UV下降门限 | 4.016–4.183V |
| 3.32k表列限流范围 | 0.85–1.15A，另计外部电阻误差 |
| 正常启动至5V的名义斜坡时间 | 5.5ms，不是全容差上界 |
| 两分压及泄放在5V下的名义电流 | 245µA和50µA |

U8自身表列工作静态电流典型428µA、最大610µA，适用于数据表测试条件，不能漏出USB来源预算。本限流用于故障保护，**不授予从USB取1A的权利**；现有充电器ILIM和许可仍独立工作。暂不采用TPS25200，其5.4V钳位上界为5.55V，不能直接当作现有5.5V逻辑的保证。

依据：[TI TPS25947 Rev.C](https://www.ti.com/lit/ds/symlink/tps25947.pdf)的型号表、引脚表、6.5及7.3节；[TPS25200](https://www.ti.com/lit/ds/symlink/tps25200.pdf)的输出钳位范围。

## 保护范围尚未验收

- 静态OV门限不等于输出瞬态上限；过压响应表给典型时间，快速上冲仍须与后端绝限、TVS和布局配合。不能宣称输出永不超过5.5V。
- UV下降会低于4.5V，未补齐TS5A23166低压参数缺口。OV恢复绕过dVdt，不能用C17证明每次恢复都缓升；恢复门限可能低于正常5V，需要拔插或电源下降才能重启。
- 对5.25V以上合法来源的兼容性还需整体审查，当前静态门限可能提前切断。普通5V输入边界不能被扩大为所有Type-C供电情况。
- EN分压在28V时超过引脚绝限，OVLO推荐电压范围也限制可声称的故障边界；本页不宣称28V、负电压或任意错误适配器保护。输入电容耐压不能单独证明整页耐压。
- RPW0010A是专用异形焊盘，尚未指派生产封装。电容MPN、热、浪涌/ESD、CC短接VBUS、USB数据反灌及实测均未完成。小批可核验报价尚未取得，50–100元整机材料预算未通过。

## USB识别调查结论

BQ24392带内置D+/D−隔离开关，可减少插线检测和主控数据驱动冲突；但不能直接将CHG_DET当作充电许可。正式Rev.G表中DCP、部分非标准充电器及某些GOOD_BAT状态共用输出编码，CHG_DET高电平还可能达到VBUS。GOOD_BAT必须结合系统有效状态，不能常高后宣称失电隔离已解决。

独立复核还找到TI论坛对CDP电流表述可能有误的说明，以及算法与部分BC1.2测项的差异；主代理本轮访问论坛正文受限，保留为待核实线索，不作为放行依据。正式表格和完整冷启动/DBP行为尚未闭合，本轮不把BQ24392接到充电许可，不宣称普通USB充电已完成。

资料：[BQ24392正式数据表](https://www.ti.com/lit/ds/symlink/bq24392.pdf)、[CDP表述线索](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/530442/bq24392-bc1-2-voltage-detection-suspend-mode)、[BC1.2测项线索](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/742181/bq24392-fail-the-bc1-2-test)。

下一步先做一次电源方案收敛：对比当前分立控制的完整BOM和集成替代方案，区分必须由硬件独立完成的电芯安全保护与可作为软件接口交付的USB枚举策略。用户接手软件不等于禁止合理的硬件控制接口；不能因自行增加“所有USB状态必须无固件处理”的假设而无限堆叠器件。形成可实现且预算合理的路径后继续主板和NFC集成。

## 验证

`verify_input.py`确认原61器件仅J5.1由VBUS_IN改VBUS_RAW；所有旧值保持，新增10器件逐脚和值核对。布局前后除新增R18两端外网表相同。模拟输出绕过保护、充电器直接取RAW及OV分压错接UV的三项故障均检出。官方CLI ERC零违规，六页PDF中新增子页和根页已目视检查。

MCP新增子页仍会改变父页缓存，使用备份保留父页并只插入sheet结构。字段整理曾出现重叠文本替换，PDF目视发现缺失内容后从本轮备份重建；最终脚本禁止重叠替换，并重新导出网表、ERC和PDF验证。一次性编辑脚本不应对最终工程重复运行；验证脚本可重复运行。

```powershell
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o docs/mini-companion/validation/power-012/system-final.xml hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all -o docs/mini-companion/validation/power-012/erc.json hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/ProgramData/miniconda3/python.exe' docs/mini-companion/validation/power-012/verify_input.py
```
