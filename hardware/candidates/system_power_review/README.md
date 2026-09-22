# HW-PWR-006：系统稳压与 POWER 评审图

2026-09-22。已实际绘制独立 KiCad 原理图；不是生产主板。打开同目录 `system_power_review.kicad_pro`。PDF：`../../../docs/mini-companion/validation/power-006/system-review.pdf`。

TASK ID：HW-PWR-006；MODEL：Astra实施、独立子代理只读二审、Astra复核；OBJECTIVE：后级升降压和机械POWER接线；INPUTS：已提交BQ24072T核心、TI数据表、既定屏幕上限；MUST KEEP：充电和电芯保护连续；ALLOWED TO MODIFY：独立候选及验证资料；DO NOT MODIFY：主板、软件和外壳；TOOLS：KiCad MCP放置与连接、官方CLI、Python网表检查；VALIDATION：逐脚合约、开关错接故障注入、容差计算、ERC、PDF；OUTPUT：本目录及power-006证据；RISK：尚未完成整合、器件定型和动态验证。

## 已落到图中的连接

- J1.1 `SYS_RAW` 对接充电器 OUT；J1.2 接系统公共地。J1/J2仅是评审边界，不增加实物接口。
- TPS63802DLAR：VIN接SYS_RAW，0.47µH电感连接L1/L2，输入10µF、输出两个22µF；MODE接地允许省电模式。AGND/功率地布局需按TI要求汇接。
- 反馈53.6k/10k，均±0.1%，目标3.18V。PG经100k上拉到切换后的逻辑电源。
- SW1为保持位置的机械SPDT，公共端2接EN，端1接SYS_RAW，端3接地；EN另有100k下拉。最终料号必须是先断后合BBM，不能在切换时短接电源和地。
- POWER不接入PACK−、BAT或NTC，不影响充电核心。关机由转换器的负载断开功能实现；USB、ADC及背光等旁路尚待整合审查。
- 输出100k泄放，避免仅靠未知负载放电；这不代表瞬间清零。44µF名义容量与100k并联63.6k估算时间常数约1.71秒，实际值随容量、负载和外部反灌变化。

## 验证与适用边界

KiCad 10.0.6官方CLI ERC：0错误、0警告。独立网表检查覆盖13个器件、36个引脚、8条网络，确认整理图形前后连接一致，并能识别SW1公共端错接。PWR_FLAG和电源图形不计入器件数。

按PWM基准±1%、电阻±0.1%、保守双向100nA反馈偏置计算，静态范围3.137544–3.222584V，距屏幕3.3V上限约77mV。**此范围不覆盖PFM纹波、启动或负载瞬变**；MODE接地时不能据此保证屏幕电压始终合格。候选参数保留，整合后需检查实际动态裕量。

转换器本身的低压锁定不足以保护单节锂电池。真实电池包必须有过放/过流/短路保护；正常系统低电管理和故障保护分工仍需落实。不能把转换器的2A能力当成整机持续负载能力，也不能以其单芯片关机电流代表整机待机电流。

## 实物与布局待办

1. DLA是非对称HotRod焊盘，未找到已核对的本地标准封装；本图故意不指派普通DFN代替。U1、L1、SW1尚无生产封装。
2. 电感和电容需确定真实料号，核对电流/温升及直流偏压。推荐条件要求输入有效电容至少4µF、当前输出档至少7µF；标称容量不能代替此检查。
3. 背光不能直接由3.18V轨假定获得全部所需电压；其恒流方案仍独立设计。NFC尚未选定，完整峰值/持续电流和两天续航尚未验收。
4. USB前端、系统掉电、ADC隔离、尺寸和完整BOM成本未完成。空白PCB仅是工具初始化文件，没有布板成果。

## 操作与资料

KiCad MCP创建、生成10脚符号、放置和连线。自动排版仍重叠，备份后仅整理字段、字体及移动完整输出接口图形；官方导出网表确认无电气变化。端子移动曾产生离栅格警告，改为101.6mm整栅格平移后已消除。未改主板工程。

[TI TPS63802 Rev.D](https://www.ti.com/lit/ds/symlink/tps63802.pdf)：表7-1、8.3、8.5和第10/12节。独立二审复算与`verify_system.py`结果一致，允许保留候选草图，未作制造放行。

验证命令（工作目录为仓库根）：

```powershell
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o docs/mini-companion/validation/power-006/system-final.xml hardware/candidates/system_power_review/system_power_review.kicad_sch
& 'C:/ProgramData/miniconda3/python.exe' docs/mini-companion/validation/power-006/verify_system.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all -o docs/mini-companion/validation/power-006/erc.json hardware/candidates/system_power_review/system_power_review.kicad_sch
```
