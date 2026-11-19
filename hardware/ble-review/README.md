# Mini Companion BLE-A1｜两台样机硬件

**当前交付状态：可评审、可询价。** KiCad 10.0.6 保存态 ERC、全严重度严格 DRC、未连接、原理图与 PCB 一致性问题均为零。两台实物及含税到手报价待取得。

| 你要做什么 | 打开这里 |
|---|---|
| 查看图纸 | [完整原理图 PDF](quote/Schematic.pdf) · [KiCad 工程](project/mini_companion_integrated.kicad_pro) |
| 查看主板正反面 | [正面 PDF](verification/pcb_front.pdf) · [背面 PDF](verification/pcb_back.pdf) |
| 找供应商报价 | [两台完整询价 ZIP](quote/Mini-Companion-RFQ.zip) · [范围与三种加工路线](sourcing/供应商询价草稿_未发送.md) |
| 评估成本和缺料 | [内部预算与物料说明](sourcing/README.md) · [缺料备选](sourcing/缺料替代核对_20261119.md) |
| 后续写固件 | [GPIO、供电与软件接口](design/硬件与固件接口.md) · [普通 USB 线烧录与恢复](design/USB服务模式设计依据.md) |
| 看外壳或安排代装 | [后盖维护孔、打印件与装配](mechanical/README.md) · [两线 POWER、探头与线束](sourcing/线束与探头代装要求.md) |
| 核对版本 | [最终文件指纹](quote/manifest.json) · [ERC](quote/ERC.json) · [DRC](quote/DRC.json) · [基线及工具核验](verification/README.md) |

从 11 月 13 日的 BLE-A0 迁入。BLE-A1 保留 ESP32-S3、彩屏、三键、受保护电池和双机/手机 BLE。正常插线充电时停机。需要开发时，用有电的电池和背面维护开关切换为 USB 烧录；首次 ROM 恢复的设计期步骤见上表。为降低首次费用与结构工作量，本版省去声音器件。

主板每台 94 个需要采购并装配的器件，合并为 48 个物料行。目标为两台 400–600 元，整个项目支出上限 1000 元。电池、电芯温度探头、线束、屏幕和外壳加工均纳入询价。正式金额需供应商确认。下一步实物验收优先验证充电温升、烧录恢复、低电压/无线发射时的主轨、闭壳 BLE 与实测续航。

USB 只按 Full-Speed 开发口评审。两种插入方向下，D+/D− 的板上路径长度差分别约 24.8 mm、19.6 mm。需用普通数据线做双向枚举、故障恢复、整镜像烧录和回读校验。[走线度量](verification/usb_route_metrics.json)。
