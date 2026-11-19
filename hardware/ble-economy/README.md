# Mini Companion BLE-A2 · 两台样机

两块微雪 ESP32-S3-LCD-2 V2 各配一块定制三键电源板、一只带保护电池和一套树脂外壳。本版按两台样机设计。电气和装配资料供询价，实物制作、温度保护测试和总装验收待进行。

| 想看什么 | 文件 |
|---|---|
| 打开 KiCad 10 完整工程 | [工程文件](project/mini_companion_a2.kicad_pro) · [原理图](project/mini_companion_a2.kicad_sch) · [双层 PCB](project/mini_companion_a2.kicad_pcb) |
| 免安装看图 | [电路 PDF](verification/a2_schematic.pdf) · [顶面装配 PDF](verification/a2_top_assembly.pdf) · [壳体及安装](mechanical/装配.md) |
| 两台花多少钱 | [含线束、装配、运费的预算](两台费用.md) · [采购核验](sourcing/采购核验记录_20261119.md) |
| 让工厂单面贴片 | [嘉立创格式 BOM](sourcing/BOM_JLC_顶面.csv) · [顶面坐标](manufacturing/top-position-jlc.csv) · [光绘和钻孔](manufacturing/a2-gerber-drill.zip) · [贴装说明](manufacturing/README.md) |
| 让代装方免焊交付 | [询价范围及逐针接线](sourcing/外部询价与免焊线束要求.md) · [四款打印文件](mechanical/stl/) · [逐台验收表](整机验收.md) |
| 了解电路和软件接口 | [供电、互锁与温度计算](design/电气设计与验收.md) · [开关、按键、BLE 和 USB 烧录](使用与软件接口.md) |
| 复核设计文件 | [电路校核](verification/a2_electrical_checks.json) · [布线校核](verification/a2_pcb_receipt.json) · [机械校核](mechanical/geometry-check.json) |

USB-C 由运行短线和电脑数据线轮流使用。日常充电走单独的 5 V 圆口，圆口插入即关断电池给主机的供电。温感探头贴在电芯大面，由小板硬件禁充；代装方要为两台分别交付温度动作记录。[微雪核心](https://www.waveshare.net/shop/ESP32-S3-LCD-2.htm) · [芯片充电规格](https://www.ti.com/product/BQ25170)

用过的 KiCad 工具版本、用途和复查方式见[工具说明](tools/PCB工具说明.md)。本版可下载的硬件包及费用汇总从[项目总入口](../../00-项目入口/先读我.md)进入。
