# HW-PWR-012：增加USB输入保护的电源集成评审图

最新2026-09-28：新增TPS259470L输入保护子页，原始VBUS与受保护VBUS已分开；六页71器件、ERC零违规，逐脚差分和三项故障注入通过。普通USB识别、瞬态保护、专用封装和完整成本仍未验收。[最新说明](../../../docs/mini-companion/validation/power-012/REVIEW.md)，[PDF](../../../docs/mini-companion/validation/power-012/system-review.pdf)。以下为历史记录。

最新2026-09-28：BQ24072T核心已通过跨页网络接入TPS63802系统输入；新增VBUS供电的TS5A23166双通道串联许可控制，监控器供电改VBUS。当前61器件、五页、ERC零违规，逐脚合约和三项故障注入通过。Default USB/BC1.2、快速掉压及前端保护仍未完成，尚未替换主板或布板。[最新说明](../../../docs/mini-companion/validation/power-011/REVIEW.md)，[PDF](../../../docs/mini-companion/validation/power-011/system-review.pdf)。下面均为历史记录，以本段和power-011报告为准。

最新2026-09-27：新增TPS3808监控与SN74LVC1G97条件组合，R9改10k；当前40器件、四页、ERC零违规。输出尚未接充电EN，低压钳位和Default/BC1.2仍待完成。[最新说明](../../../docs/mini-companion/validation/power-010/REVIEW.md)，[PDF](../../../docs/mini-companion/validation/power-010/system-review.pdf)。以下为历史记录。

最新：USB侧TPS70933独立稳压及TUSB320LAI检测子页已绘制；尚未连接充电授权逻辑。三页PDF：`../../../docs/mini-companion/validation/power-009/system-review.pdf`；限制与验证：`../../../docs/mini-companion/validation/power-009/REVIEW.md`。32个器件，ERC零违规，原22器件连接不变。以下为历史阶段记录。

2026-09-24新增：背光子页已通过层次引脚接入切换后电源。最新两页PDF：`../../../docs/mini-companion/validation/power-008/system-review.pdf`；说明及验证：`../../../docs/mini-companion/validation/power-008/REVIEW.md`。当前22个器件，ERC 0错误/0警告，旧电源逐脚连接不变。背光名义58.06mA，电流全范围、元件定型及实测未完成。以下保留HW-PWR-007历史说明，其中“背光待设计”已由本次候选子页推进，仍未合入生产主板。

更新2026-09-23。已实际绘制独立 KiCad 原理图；不是生产主板。打开同目录 `system_power_review.kicad_pro`。最新PDF：`../../../docs/mini-companion/validation/power-007/system-review.pdf`。HW-PWR-006证据保留作历史基线。

TASK ID：HW-PWR-006；MODEL：Astra实施、独立子代理只读二审、Astra复核；OBJECTIVE：后级升降压和机械POWER接线；INPUTS：已提交BQ24072T核心、TI数据表、既定屏幕上限；MUST KEEP：充电和电芯保护连续；ALLOWED TO MODIFY：独立候选及验证资料；DO NOT MODIFY：主板、软件和外壳；TOOLS：KiCad MCP放置与连接、官方CLI、Python网表检查；VALIDATION：逐脚合约、开关错接故障注入、容差计算、ERC、PDF；OUTPUT：本目录及power-006证据；RISK：尚未完成整合、器件定型和动态验证。

## 已落到图中的连接

- J1.1 `SYS_RAW` 对接充电器 OUT；J1.2 接系统公共地。J1/J2仅是评审边界，不增加实物接口。
- TPS63802DLAR：VIN接SYS_RAW，0.47µH电感连接L1/L2，输入10µF、输出两个22µF；MODE接地允许省电模式。AGND/功率地布局需按TI要求汇接。
- 反馈53.6k/10k，均±0.1%，目标3.18V。PG经100k上拉到切换后的逻辑电源。
- SW1选PCM12SMTBR，公共端2接EN，端1接SYS_RAW，端3明确NC；EN另有100k、1%下拉。此接法无需依赖BBM，切换时没有直接短接电源与地的路径。按EN最大漏电0.2µA计算关机电平最高20.2mV，低于0.4V输入低电平界限。
- POWER不接入PACK−、BAT或NTC，不影响充电核心。关机由转换器的负载断开功能实现；USB、ADC及背光等旁路尚待整合审查。
- 输出100k泄放，避免仅靠未知负载放电；这不代表瞬间清零。44µF名义容量与100k并联63.6k估算时间常数约1.71秒，实际值随容量、负载和外部反灌变化。

## 验证与适用边界

KiCad 10.0.6官方CLI ERC：0错误、0警告。独立网表检查覆盖13个器件、36个引脚、8条网络，确认整理图形前后连接一致，并能识别SW1公共端错接。PWR_FLAG和电源图形不计入器件数。

按PWM基准±1%、电阻±0.1%、保守双向100nA反馈偏置计算，静态范围3.137544–3.222584V，距屏幕3.3V上限约77mV。**此范围不覆盖PFM纹波、启动或负载瞬变**；MODE接地时不能据此保证屏幕电压始终合格。候选参数保留，整合后需检查实际动态裕量。

转换器本身的低压锁定不足以保护单节锂电池。真实电池包必须有过放/过流/短路保护；正常系统低电管理和故障保护分工仍需落实。不能把转换器的2A能力当成整机持续负载能力，也不能以其单芯片关机电流代表整机待机电流。

## 实物与布局待办

1. 已建立并指派U1专用DLA0010A封装，10个铜焊盘，8脚两片独立锡膏开窗；数值校验和官方CLI预览通过。SW1已指派标准PCM12封装。仍需与实际装配工艺和外壳位置核对。
2. L1选DFE201612E-R47M=P2，项目E系列封装匹配推荐焊盘，去掉错误的1.0mm高P系列3D模型；E系列高度上限1.2mm。电容仍需真实料号与偏压曲线，输入有效容量至少4µF、输出至少7µF。电感在峰值及温升下的实际表现仍待负载预算和布局验证。
3. 背光不能直接由3.18V轨假定获得全部所需电压；其恒流方案仍独立设计。NFC尚未选定，完整峰值/持续电流和两天续航尚未验收。
4. USB前端、系统掉电、ADC隔离、尺寸和完整BOM成本未完成。空白PCB仅是工具初始化文件，没有布板成果。

## 操作与资料

KiCad MCP创建、生成10脚符号、放置和连线。自动排版仍重叠，备份后仅整理字段、字体及移动完整输出接口图形；官方导出网表确认无电气变化。端子移动曾产生离栅格警告，改为101.6mm整栅格平移后已消除。未改主板工程。

[TI TPS63802 Rev.D](https://www.ti.com/lit/ds/symlink/tps63802.pdf)：表7-1、8.3、8.5和第10/12节。独立二审复算与`verify_system.py`结果一致，允许保留候选草图，未作制造放行。

最新验证命令（工作目录为仓库根；power-006脚本只用于旧版本）：

```powershell
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o docs/mini-companion/validation/power-007/system-final.xml hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all -o docs/mini-companion/validation/power-007/erc.json hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/ProgramData/miniconda3/python.exe' docs/mini-companion/validation/power-007/verify_revision.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' docs/mini-companion/validation/power-007/verify_dla.py
```
