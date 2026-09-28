# HW-PWR-011：充电核心与系统电源集成候选

2026-09-28。五页、61个实际器件，官方CLI ERC零违规；目前是CC高电流广告条件下的集成评审图，不是制造版本。主板仍未替换电源；PCB布局、完整BOM和实测均未完成。

TASK ID：HW-PWR-011；MODEL：Astra实施与复核、既有power_parts代理独立只读二审；OBJECTIVE：将已审BQ24072T核心接入系统候选，并使充电输入许可受独立电源有效条件控制；INPUTS：power-004/010网表、TI正式数据表；MUST KEEP：单节电池、电芯NTC、关机充电和独立保护路径；ALLOWED TO MODIFY：system_power_review候选及本轮证据；DO NOT MODIFY：生产主板、软件、原独立充电核心；TOOLS：KiCad MCP、结构化文本修复、官方CLI和网表检查；VALIDATION：逐脚合约、故障注入、静态条件计算、ERC及PDF目视；OUTPUT：本报告、五页PDF和候选工程；RISK：普通USB来源策略及快速掉压尚未验收。

## 已实际接入的电路

- 新增charger子页，原核心编号整体加100；U101 BQ24072T的OUT实际接U1 TPS63802的VIN，电池接独立PACK_POS，电芯NTC保留独立第三线。
- VBUS_IN、SYS_RAW和VLOGIC_SWITCHED通过明确的跨页网络连接；移除被真实电源输出替代的PWR_FLAG。USB_3V3仍是独立常供电检测域，系统POWER控制后级EN，不切断充电或NTC路径。
- EN2通过R108=10k上拉VBUS，EN1通过R107=10k上拉VBUS。默认EN2/EN1=11，充电器输入处于suspend；U7 TS5A23166两通道串联闭合才将EN1拉低，进入10/ILIM模式。
- U7两路分别由USB_READY及CC_HIGH_QUALIFIED控制。TPS3808的VDD、MR和旁路电容移到VBUS；SENSE仍测USB_3V3，避免监控器随受监控电源一同失效时只靠组合门判断。此改动支持稳态低压禁止，不构成任意瞬态保证。
- READY上拉改22k，条件输出下拉改47k；前者提供电平裕量，后者兼顾轻载输出高电平及VCC=0时Ioff上界。该Ioff检查不能外推至所有中间供电电压。
- 充电电流名义约303mA、上界约335mA；ILIM设定约378–493mA，沿用核心候选。供电旁路消耗还需并入来源电流预算。

| USB_READY | CC许可 | EN2/EN1 | 稳态模式 |
|---|---|---|---|
| 0 | 0 | 11 | suspend |
| 0 | 1 | 11 | suspend |
| 1 | 0 | 11 | suspend |
| 1 | 1 | 10 | ILIM |

## 验证及证据范围

`verify_integration.py`从实际导出网表检查61个器件。旧40器件只有U5.3、U5.6、C11.1从USB_3V3移至VBUS_IN；原充电核心逐脚合约仅允许EN上拉电阻端点变化。整理图形前后网表完全一致。三项故障注入分别模拟绕过独立READY、电池NTC误接正极及充电器OUT误接电池，均能被检查发现。

在TS5A23166的4.5–5.5V参数表适用条件下，串联导通压降估算1.336mV，低于BQ逻辑低上限0.4V；READY保守高电平计算2.906V，高于TS输入高门限2.4V。47k下拉在组合门VCC=0、10µA Ioff条件下估算0.4747V，低于TS输入低门限0.8V。公式和输入记录在脚本中，不代替动态仿真及实测。

官方KiCad 10.0.6 ERC零违规，PDF五页已目视检查。ERC无法证明电池安全、动态时序、模拟参数、射频性能或续航。

## 必须继续完成

1. 当前仅响应CC广告1.5A/3A；Default USB仍保持suspend，尚不具备完整的普通USB充电能力。需完成Default/BC1.2与原生USB数据/枚举/挂起策略，不能将Default直接视为可取500mA。
2. TPS3808下降传播延迟20µs是典型值而非保证最大值；不能据此宣布快速掉压、拔插、抖动已安全验收。180nF延时表也不能忽略电容误差和偏压。TS在4.35–4.5V输入区间的参数覆盖需解决。
3. VBUS过压/ESD、CC保护、限流及所有旁路消耗未最终落实。TS满温供电电流上限表列16µA的测试条件是控制输入在电源轨；3.3V控制、5V供电条件的实际最大消耗不能照搬该值。主板原Rd应在最终采用TUSB内置Rd时同步移除。
4. 真实受保护电芯、贴电芯本体NTC、三针连接器、温度窗口及保护职责仍需定型；电池连接器顺序目前是评审合约，不是可直接采购线束定义。
5. 电容有效容量、屏幕动态电压与背光全温电流、NFC负载、整机峰值/待机/两天续航、尺寸及50–100元材料预算均未闭合；评审连接器不能直接计入最终实体BOM。

下一步先闭合USB来源和保护策略，再进入主板替换及NFC集成；不得因本候选ERC通过导出制造包。

## 复查方法

从仓库根运行：

```powershell
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o docs/mini-companion/validation/power-011/system-final.xml hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all -o docs/mini-companion/validation/power-011/erc.json hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/ProgramData/miniconda3/python.exe' docs/mini-companion/validation/power-011/verify_integration.py
```

`integrate_core.py`和`finish_layout.py`保留一次性编辑记录，依赖本地编辑前备份，不应在完成后的工程再次运行。常规复查只运行以上导出及验证命令。MCP新增子页时丢失父页自定义符号缓存，因此从备份保留父页，只移入新增sheet结构，再由官方CLI及独立网表确认；未修改原独立充电核心。

官方依据：[BQ24072T](https://www.ti.com/lit/ds/symlink/bq24072t.pdf)、[TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)、[TS5A23166](https://www.ti.com/lit/ds/symlink/ts5a23166.pdf)、[SN74LVC1G97](https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf)。此前背光、系统转换器及CC前端依据见power-006至010。
