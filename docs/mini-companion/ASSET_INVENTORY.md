# mini-companion 硬件资产审计

审计日期：2026-09-19。本文只记录仓库内文件证据；“文档声明”与“实际验证”分开。没有删除任何硬件/软件资产。

## 资产范围与数量

| 范围 | 实际文件数 | 证据 |
|---|---:|---|
| 仓库全部文件 | 215 | `Get-ChildItem -Recurse -File` |
| `hardware/`（含子目录） | 55 | KiCad 工程、原理图、PCB、图片、库、生产文件 |
| `hardware/jlcpcb/gerber/` | 13 | Gerber、钻孔文件及钻孔图 PDF |
| `hardware/jlcpcb/production_files/` | 3 | BOM、CPL、GERBER ZIP |
| `hardware/libs/` | 22 | EasyEDA/FS8205A 符号、封装、3D 模型 |
| `case/exploration/` | 102 | 48 个概念文本、48 个 SVG、FreeCAD 脚本/模型/尺寸 |
| `docs/` | 13 | 架构/协议及 MCU、显示、电源数据手册 |
| `firmware/` | 1 | `firmware/README.md`；未发现固件源文件 |

关键硬件资产均存在：`hardware/devotchi.kicad_pro/.kicad_sch/.kicad_pcb`、`display.kicad_sch`、`feedback.kicad_sch`、`mcu.kicad_sch`、`power.kicad_sch`、`user_input.kicad_sch`；PCB 前/后/3D 渲染图；JLCPCB Gerber、BOM、CPL；FreeCAD `devotchi_case.FCStd`、`case.py`、`params.py`、`dimensions.md`。`hardware/~devotchi.kicad_pro.lck` 是锁文件，也应保留并在工程打开时确认是否为活动锁。

根目录 `LICENSE` 为 MIT，版权行是 `Copyright (c) 2026 Hussam Koman`。README 与硬件 README 均声明项目是原型/WIP；README 还声明 PCB 已设计并下单。仓库内有本地许可证文本，但没有对外部 LCSC/厂商数据手册授权条款作额外声明，应把其视为供应商资料而非本项目 MIT 代码许可的延伸。

## 采购、BOM、贴片实际概览

- `BOM-devotchi.csv` 实际 28 行、数量合计 46；其中 `U301 HS20HS072RX` 数量为 **0**。这与 purchase-list 将显示器列为单独采购相符，但 BOM 条目容易被误读为“已纳入贴片订单”。
- `CPL-devotchi.csv` 实际 44 行，全部 `top` 层；没有 `SW503`、`C503`、`R503`、`U301`、`J401` 的贴片坐标。`J401` 是电机焊盘/外接件，显示器也是外接件，CPL 缺失本身合理；但 SW503/C503/R503 的缺失是功能版本选择问题，需在下单前定版。
- 采购清单声称 PCB 贴片用户键为 `SW501-SW504` 四只；实际 BOM/CPL 只有 `SW501` ACTION、`SW502` APPROVE、`SW504` REJECT 三只。`user_input.kicad_sch` 仍有 `SW503 BTN_WAKE`、`C503 100n`、`R503 10k`，而 `devotchi.kicad_pcb` 只有 SW501/SW502/SW504，故当前可制造 PCB 的证据是三只用户键，第四键只存在于原理图分支，且明确标记 DNP/exclude_from_board/exclude_from_bom，并非意外漏贴。
- BOM 的 `U101` 值为 `ESP32-S3-MINI-1-N4R2`，但 footprint 字段为 `ESP32-S2-MINI-1`；`mcu.kicad_sch` 与 README/purchase-list 均支持 S3。S2/S3 可存在共用封装；此处仅列核对项，不据名字判定错误。必须比对厂商推荐焊盘和模组引脚，采购按准确S3料号。
- BOM 中 `J401 Motor` 的 LCSC 为 `C2895081`，数量 1，但 purchase-list 把 `C2895081` 对应的 `LCM0720A3134F` 作为单独采购并注明“焊到 J401”；应把 BOM 行解释为外接候选/连接器，不要让 JLCPCB 按贴片料采购电机。
- BOM 与 purchase-list 的核心器件总体一致：ESP32-S3-MINI-1-N4R2/C3013941、TP4056/C725790、DW01A/C351410、ME6211/C82942、FS8205A/C2830320、AO3400A/C20917、1N5819W/C42441798、LED/C19189745、USB-C/C165948、电池座/C7433648、FPC/C262661。显示器 HS20HS072RX/C5329582 和电机 LCM0720A3134F/C2895081 为外接件候选。

## feedback 原理图实际元件候选

`hardware/feedback.kicad_sch` 的已编号元件为：

| Ref | 原理图值 | 功能/采购解释 |
|---|---|---|
| J401 | Motor，`Conn_01x02` | 外接电机焊盘/连接器；不应当作贴片电机 |
| Q401 | AO3400A | 电机低侧 MOSFET 驱动 |
| D401 | 1N5819W S4_C42441798 | 电机反灌/续流二极管 |
| R401 | 150R | 绿色调试 LED 串联电阻 |
| D402 | FC-1608G1-520 | 绿色 0603 调试 LED |
| R402 | 1k | MOTOR_PWM/Q401 栅极到 GND 的下拉电阻 |

因此 feedback 的实际候选组合是“6 mm、3 V、约 85 mA 的 LCM0720A3134F 外接电机 + AO3400A + 1N5819W”以及“FC-1608G1-520 绿色 0603 LED + R401”；R402 属于电机支路；其中电机本体仍需单独采购并焊线。README 对 feedback 的 GPIO/MOSFET 描述与这些编号一致，但尚无实物装配或通电验证证据。

## FreeCAD/机械资料

`dimensions.md` 与 `params.py` 的主模型假设为外壳 60 x 60 x 15.1 mm、壁厚 1.5 mm；显示模块 51.8 x 36.2 x 2.5 mm、有效区 40.8 x 30.6 mm；PCB 45 x 50 x 1.6 mm，位置 X=7.5/Y=8.5/Z=6.5；电池假设为 503450、1000 mAh、34 x 50 x 5 mm；USB-C 开孔约 9.34 x 3.66 mm。`devotchi_case.FCStd` 实际存在，尺寸脚本可追溯这些参数。

机械风险：

1. `hardware/README.md` 的外壳仍写“约 50 x 40 x 20 mm”，而 FreeCAD 资料已经是 60 x 60 x 15.1 mm；两者不能同时作为制造尺寸。
2. `hardware/README.md` 写“4 buttons”开孔，README、硬件器件说明和 `dimensions.md` 主布局写三键；`params.py` 仍定义 `WAKE_HEX_*`/`BTN_WAKE_Y` 和 4 键 cap 输出。外壳 STL/打印前必须决定是否保留 SW503 醒按钮，并同步 PCB、CPL、C503/R503 和开孔。
3. 采购清单电池范围是 300–500 mAh，FreeCAD 却固定 503450、1000 mAh；电池外形、厚度、JST 线出口和实际可用容量必须以最终供应商料号为准。现有 5 mm 深度堆栈只验证了模型假设，没有实物公差/线束验证。
4. 尺寸表称 PCB 有 3 个 M2 孔并移除 TL 孔以避让 FPC；`case.py` 的 `PCB_POST_POSITIONS` 仍列出四个角点，脚本与尺寸文字不一致，需在导出/打印前核对孔位。
5. 盒体深度堆栈按“PCB 后 0.5 mm 间隙 + 5 mm 电池”计算，但 `params.py` 同时注释 `GAP_PCB_BATT = 5.0`（JST 连接器间隙）和公式使用 0.5；这是机械包络高风险项。

## 结论与下单前动作

当前资产齐全，且必须保留全部硬件、软件、Gerber、FreeCAD、库和许可证文件。可确认的硬件基线是 ESP32-S3 + HS20HS072RX 外接显示 + 三个已布 PCB 用户键 + feedback 电机/LED 外接件；但 MCU footprint、SW503 是否装配、电池型号/容量、外壳尺寸版本和 FreeCAD 孔位仍未统一。建议下单前锁定一个版本，并重新生成 BOM/CPL/PCB 与外壳参数；在此之前不要依据现有 purchase-list 的“SW501-SW504 x4”、`ESP32-S2-MINI-1` footprint 或 1000 mAh 电池假设直接采购。
