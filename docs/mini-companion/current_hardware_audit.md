# Mini Companion V1 — 当前硬件基线审计

日期：2026-09-19。基线提交：`5023d4d`；分支：`mini-companion-v1`；开始时 `git status --short` 为空。PHASE 0 未修改任何原理图、PCB、项目配置、固件或旧生产文件。

## 结论

现有工程有较完整的可复用设计资产，但尚不满足 Mini Companion 的制造放行条件。优先保留 MCU、显示接口、三操作键、USB 和板框；电源、NFC、独立 Power、机械一致性必须先完成工程验证。原项目是 WIP，仓库内没有足以证明整机、电池异常工况和双设备 NFC 已实测通过的记录。

## 工具与证据

- 本会话工具目录未提供 KiCad MCP，也没有可用的工具搜索入口能加载它；不声称使用过 MCP。
- 使用本机官方 `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`，版本 **10.0.6**。源文件为 KiCad 9 格式；没有保存或升级源设计。
- 官方 `pcbnew.LoadBoard` 只读读取板框、层数、焊盘网络和元件位置；没有调用 SaveBoard。
- `baseline/netlist.xml`：官方导出的整个层级网表；`connections.txt`：便于复核的节点列表。
- `baseline/board-inventory.json`：PCB 焊盘网络、位置和层。
- `baseline/source-sha256.json`：设计与旧生产文件哈希；审计结束时复核。
- `baseline/erc.json`、`drc.json`、`drc-refilled.json`：原始检查报告。
- 资产/机械交叉检查见 [ASSET_INVENTORY.md](ASSET_INVENTORY.md)；电源专项见 [POWER_AUDIT.md](POWER_AUDIT.md)。

## 层级与器件

主文件 `hardware/devotchi.kicad_sch` 包含 mcu、power、display、feedback、user_input 五个子页，所有文件存在并成功导出网表。

| 模块 | 实际元件/说明 | 复用判断 |
|---|---|---|
| MCU | U101 ESP32-S3-MINI-1-N4R2；名义 4MB Flash/2MB PSRAM | 保留；封装名为 ESP32-S2-MINI-1，需核对共享焊盘兼容性，不能仅凭名字认定选错芯片 |
| 显示 | FPC301 AFC01-S12FCA-00，U301 HS20HS072RX，Q301 AO3400A，R301 22Ω，R302 1kΩ栅极下拉 | 保留接口设计，复核 FPC 接触面/Pin1 与显示器料号 |
| USB | J201 USB-C，R203/R204 各5.1kΩ，D+/D−直连MCU | 保留基础拓扑；ESD、下载恢复路径待审 |
| 电源 | U202 TP4056，U201 DW01A，Q201 FS8205A，U203 ME6211 | 必须审计后决定，不直接冻结 |
| 操作键 | SW501 ACTION、SW502 APPROVE、SW504 REJECT，10kΩ上拉+100nF | 三键可复用，低有效 |
| 非装配唤醒键 | SW503、R503、C503、TP503：DNP且排除PCB/BOM，原理图连GPIO7 | 不是现有独立电源控制，不可计入实装功能 |
| 反馈 | D402/R401；J401/Q401/D401/R402 | 删除候选已核实网络，尚未删除 |

旧 BOM 有28行、数量合计46；CPL有44个顶层条目。U301数量0、J401电机料号与连接焊盘混用，不能把旧BOM视为完整采购清单。旧生产文件实际位于 `hardware/jlcpcb/production_files/`。MIT许可证及原作者版权保留。

## 当前 GPIO map（网表与PCB焊盘交叉核对）

| 信号 | GPIO | 模组焊盘 | 实际用途/注意 |
|---|---:|---:|---|
| BAT_ADC | **2** | 6 | R207/R208各100kΩ分压；README写GPIO1，错误 |
| BTN_APPROVE | 4 | 8 | SW502，低有效；最终LEFT须按装配视角核对 |
| BTN_REJECT | 5 | 9 | SW504，低有效；最终RIGHT须按装配视角核对 |
| BTN_ACTION | 6 | 10 | SW501，低有效；OK |
| BTN_WAKE | 7 | 11 | 原理图存在，PCB未装该按键 |
| DISP_RST | 8 | 12 | FPC6，低有效复位 |
| DISP_DC | 9 | 13 | FPC3 |
| DISP_CS | 10 | 14 | FPC2，低有效 |
| DISP_MOSI | 11 | 15 | FPC5 |
| DISP_SCLK | 12 | 16 | FPC4 |
| DISP_BL | 13 | 17 | Q301栅极，高电平导通背光；1kΩ下拉有静态负载 |
| PWR_STDBY | 17 | 21 | TP4056开集电极状态，低有效；未见外部上拉 |
| PWR_CHRG | 18 | 22 | 同上 |
| USB_DN | 19 | 23 | J201 A7/B7 |
| USB_DP | 20 | 24 | J201 A6/B6 |
| MOTOR_PWM | 37 | 33 | 实际网络名不是任务书预估MOTOR_EN |
| LED_PWM | 38 | 34 | R401及TP104 |
| UART TXD0 | 43 | 39 | TP102 |
| UART RXD0 | 44 | 40 | TP103 |
| MCU_EN | — | 45 | SW101复位，10kΩ/1µF；不是电源开关 |

GPIO0目前标为NC，没有专用BOOT按钮；USB下载失败时的恢复可达性必须设计验证。未连接GPIO不能一概当作可自由使用，后续按N4R2的模组限制和启动配置逐项分配。

PCB顶层坐标中 SW504 x=131、SW501 x=145、SW502 x=159，均y=105.4。故“APPROVE必然是左键”不能从旧名称推断，需要以外壳最终观看方向复核；不在本阶段悄悄对调GPIO。

## 当前真实电源树

```text
USB VBUS ── TP4056 VCC/CE
                 BAT ── +BATT ── 电池J202.1
                          ├── ME6211 VIN/CE ── +3V3 ── MCU/显示逻辑/按键
                          ├── R301 22Ω ── 显示背光 ── Q301 ── GND
                          ├── 电机支路 ── Q401 ── GND
                          └── R207/R208分压 ── BAT_ADC
电池J202.2 ── -BATT ── Q201双MOS保护路径 ── GND（系统/USB/充电器地）
DW01A VCC经R201取+BATT；VSS=-BATT；CS经R202取GND
TP4056 PROG经R205=3kΩ接GND；TEMP仅经R206=10kΩ接GND
```

无独立SYS输出、无负载分担路径、无独立电源开关、未见电池温度探头。电池负极与系统地是不同网络，未来开关/测试连接不能旁路保护。电池ADC分压常接；旧深睡估算不能直接移植。背光取自+BATT，后续不能把新的高电压SYS直接套接过去。

## ERC / DRC 实测

| 检查 | 错误 | 警告 | 说明 |
|---|---:|---:|---|
| ERC（含所有严重级别） | 12 | 16 | 12条均为U301未连接引脚；14条easyeda库未注册；2条同网多名称 |
| PCB保存状态DRC | 11 | 16 | 保护CS/电池座机械焊盘附近的覆铜间距/阻焊错误 |
| 内存重填覆铜后DRC | **0** | 16 | 未保存板；0未连接；不能等同最终放行 |
| 原理图/PCB parity | 0 | 52 | 全为Datasheet空字符串与`~`字段不同，非52处电气不一致 |

**检查范围限制**：上游项目关闭了ERC的pin_to_pin、lib_symbol_mismatch、footprint_filter等5类检查，以及DRC的missing_courtyard、footprint_type_mismatch等7类检查（完整列表在JSON的ignored_checks）。`--severity-all`不等于重新启用这些规则，当前计数不是全规则无误证明；正式验证必须逐项审查并恢复关键电气冲突检查。

重填后11条错误全部消失，支持“保存的覆铜与当前几何不一致”的判断，不能仅凭初次报告宣布板上确定短路。正式版本必须重新填充、保存、复查并重导Gerber，旧Gerber铜形是否受影响尚未核查。

U301是DNP显示器表示，实际电气连接位于FPC301；这解释了12条悬空错误，但不授权给所有脚随意加NC。应在正式工程中明确外接器件的文档表达和检查范围。easyeda库文件在仓库内，但项目库表仅注册FS8205A；可优先修复库可移植性。USB封装与当前KiCad10库副本不同，需几何核对，不能盲目更新封装。

复现命令（在仓库根目录运行，均不保存设计）：

```powershell
$cli = 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
& $cli sch export netlist --format kicadxml -o docs/mini-companion/baseline/netlist.xml hardware/devotchi.kicad_sch
& $cli sch erc --format json --severity-all --exit-code-violations -o docs/mini-companion/baseline/erc.json hardware/devotchi.kicad_sch
& $cli pcb drc --format json --schematic-parity --severity-all --exit-code-violations -o docs/mini-companion/baseline/drc.json hardware/devotchi.kicad_pcb
& $cli pcb drc --refill-zones --format json --schematic-parity --severity-all --exit-code-violations -o docs/mini-companion/baseline/drc-refilled.json hardware/devotchi.kicad_pcb
```

报告命令因违规返回非零不代表工具未运行成功；应读报告。未使用`--save-board`。

## PCB和机械

官方API确认4铜层，板厚配置1.6062mm；Edge.Cuts中心线边界x=122.5..167.5、y=70..120，即45×50mm。API含线宽的包围盒为45.2×50.2mm，两者口径不同。

FreeCAD设计目标60×60×15.1mm，尚未做实时3D装配/干涉检查。外壳脚本、尺寸文档的键数、支撑柱和电池间隙不一致；电池503450/1000mAh与采购300–500mAh不一致。新增NFC天线、铁氧体、支架和开关必须重新核算堆叠，不能声称当前15.1mm厚度已容纳它们。

## 风险与下一步

1. **电源冻结阻塞**：无Power Path/电芯NTC；TEMP接法需对准确供货芯片的数据手册复核；低压稳压余量、充电热、保护MOS规格、USB ESD和反接未验证。
2. **NFC冻结阻塞**：两台reader不会自动互读，两台dynamic tag也不能互相建立RF场。必须选定角色切换与双方确认机制，实际两模块在拟用电池/外壳中验证。
3. **制造阻塞**：保存覆铜、库链接、外接屏符号表达、旧BOM/CPL和机械版本未闭环。
4. **计划删除**：D402/R401，J401/Q401/D401/R402，相关网络/布线/TP104关联，保留Q301显示背光。未发现需要另外拆除的RGB、蜂鸣器、光敏电阻。
5. **计划新增**：NFC模块及可靠连接、独立电源控制、经审核的电池/充电/温监方案；不写应用固件。

PHASE 0产物是可信基线及问题清单，不是打样批准。后续实施任务见V1要求及任务计划；安全架构重大选择按用户任务书第21节提交决策。
