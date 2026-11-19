# 外接屏幕表示与装配

2026-09-22。屏幕仍为HS20HS072RX，每台一块，连接FPC301；此项没有从产品中删除。

原U301为无连线、DNP、排除PCB的屏幕占位符，12个引脚全部触发ERC。现通过KiCad MCP删除此孤立实例，用OFF_BOARD_ASSEMBLY.csv明确单独采购/后装屏幕。未删除FPC301、Q301、R301/R302、去耦电容或任何屏幕连接线。正式总BOM必须合并PCB贴片清单与此后装清单，不能漏买显示屏。

依据仓库原厂HS20HS072RX_datasheet.pdf第11页逐行视觉核对，并与实际导出网表比较：

| 屏幕/FPC脚 | 功能 | 当前主板网络 |
|---|---|---|
| 1、12 | GND | GND |
| 2 | CS | DISP_CS |
| 3 | RS/DC | DISP_DC |
| 4 | SCL | DISP_SCLK |
| 5 | SDA | DISP_MOSI |
| 6 | RST | DISP_RST |
| 7 | NC | 明确未连接 |
| 8 | I/O-VCC | +3V3 |
| 9 | VCC | +3V3 |
| 10 | 背光A | /display/LED_A |
| 11 | 背光K | /display/LED_K |

FPC301的13/14是连接器附加焊盘，不是显示屏多出的信号脚。供应商连接器触点方向、排线Pin1朝向及锁扣装配仍须按机械资料核对，不能只按线缆颜色或外观插入。电压/背光后续修改服从DISPLAY_POWER_CONSTRAINTS.md。

网表对比仅允许移除U301，其余器件值、封装和网络端点保持不变。检查证据位于validation/display-cleanup。主工程同时重新启用pin_to_pin=error和lib_symbol_mismatch=warning，不再依赖关闭这两类检查获得通过。其他既有禁用类别仍需后续处理。

本轮官方ERC结果：0 errors、24 warnings；其中20条为现有符号引脚电气类型相关提示、2条库符号差异、2条网络多名。旧的12条U301悬空错误已消除，未关闭对应检查。没有修改PCB，因此本轮不重跑无变化的PCB几何检查；电源/NFC整合后必须重新执行全套检查。
