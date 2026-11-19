# USB PCB 布线与封装复核

对象为两台 BLE-A1 USB Full-Speed 原型。PCB SHA-256：`35675f68e93142e07def0e88f09073ee1605d7398833b505377b71d052818954`。保存态全规则、全部严重度 DRC、未连接及原理图一致性问题均为零，未新增排除项。电气架构见 [USB 服务模式设计依据](USB服务模式设计依据.md)；正式保存态证据以 [报价包 DRC](../quote/DRC.json) 与 [manifest](../quote/manifest.json) 为准。

## 布线度量与边界

[可复算度量](../verification/usb_route_metrics.json) 从保存的 KiCad 铜线提取。下表的总长包含同网的连接器重复触点、ESD 等分支；不能把它直接当成端到端信号延迟。

| 网络 | 全部铜线中心线合计 mm | 全网通孔数 |
|---|---:|---:|
| USB_DP_CONN | 72.419 | 6 |
| USB_DM_CONN | 52.554 | 5 |
| USB_DP_ISO | 12.446 | 0 |
| USB_DM_ISO | 9.628 | 0 |
| MCU_USB_DP | 4.869 | 0 |
| MCU_USB_DM | 2.599 | 0 |

按连接器 → U1101 → 串联电阻 → MCU 的最短铜线中心线路径相加：A6/A7 取向为 DP 82.526 mm、DM 57.694 mm，差 24.833 mm；B6/B7 取向为 80.494/60.901 mm，差 19.593 mm。未计过孔纵向、器件内部和封装延迟。

F 面配对主干宽 0.284 mm、间隙 0.21 mm；封装逃线宽 0.15 mm。输入部分经过 B 面并多次换层，局部拆对和上述长度差保留为这两台原型的已知偏差，未声称满足高速 USB 或阻抗认证。对主干中心线按不大于 0.1 mm 间隔采样，保存态 In1 GND 覆盖率为 DP_CONN 97.162%、DM_CONN 100%、DP_ISO 100%、DM_ISO 87.5%；单段内未覆盖连续采样最长分别约 0.799/0/0/0.500 mm。这个几何抽样不能替代场求解，也不能证明 B 面逃线的返回电流品质。

新增就近地过孔，并补齐 U1101 地脚及去耦地。局部内层分割后的逻辑电源区域用 0.8 mm 铜线补实连接。原电池主电源与背光功率铜的统计对比见 [供电铜线检查](../verification/power-copper-comparison.json)。未放宽原有 0.6 mm 非地通孔约束；新地通孔最小 0.5/0.2 mm，符合现有规则。

首板须用选定的可传数据 USB 线、正反插，执行空白芯片 ROM 恢复、连续全镜像写入及读回/校验。还需覆盖插拔、正常充电关机、SERVICE 切换、主电源上升/下降以及待开发固件中的持续通信。两台均通过再认定该布局达到本项目用途；上述 DRC 零项不替代这些实测。

## 操作件与封装

| 器件 | 板坐标 mm | 面 / 旋转 | 操作及名义高度 |
|---|---|---|---|
| SW7301 SERVICE | 154.65, 77.70 | B / 90° | 沿板 Y 方向拨动；3/6 档为 SERVICE，1/4 档为 NORMAL；名义总高 5.5 mm |
| SW7302 BOOT | 163.20, 79.50 | B / 0° | 从背面垂直按压；名义高 1.55 mm |

SERVICE 3/6 焊盘在板 y=75.20 mm，1/4 焊盘在 y=80.20 mm。外壳操作标签和实际到料开关的通断应在装配时一并核对。机械设计使用了额外 0.15 mm 工程裕量，该裕量不是厂家给出的最大公差。

`BLE_Candidate:CK_JS202011SCQN` 对照 [C&K JS 系列制造商图纸](https://www.littelfuse.com/assetdocs/littelfuse-ck-slide-js-series-datasheet?assetguid=aba42b08-0d2c-423b-813d-a2faa5a3bb14) 第 4 页创建；实际核图另使用 [RS 托管的制造商 PDF](https://docs.rs-online.com/f34d/A700000009337422.pdf) 第 4 页。SC 引脚焊盘为 1.2×2.5 mm、列距 2.5 mm、两行中心距 5.5 mm；不是系统库中 JC 端子版本。图纸的 3 mm 是内侧行间距，不是焊盘长度。

U7302 使用冻结的 KiCad `WSON-6_1.5x1.5mm_P0.5mm`，无 EP，间距 0.5 mm。其 1 脚焊盘长 0.85 mm，其余 0.75 mm，宽 0.28 mm；相对 TI 图纸的 0.8/0.7×0.25 mm 有小幅扩展，保持 0.22 mm 同列间隙及至少 0.30 mm 对侧间隙。工程判断接受用于两台原型，但仍需供应商钢网/阻焊 DFM 与首板桥连检查。

已查看实际导出的 [正面铜与 Fab 图](../verification/pcb_front.pdf) 和 [背面铜与 Fab 图](../verification/pcb_back.pdf)。这些图用于复核位置和布线；重叠的 Fab 位号不是最终外壳操作标签或供应商贴片方向确认。

## 复算入口

在项目根目录运行：

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' hardware\ble-review\tools\inspect_usb_routes.py
```

该入口只读 PCB，重写度量 JSON；不填铜、不保存板、不生成生产放行结论。一次性同步/布线脚本和中间失败证据已移到工作树外的本机开发留档，避免误重跑覆盖最终布局。
