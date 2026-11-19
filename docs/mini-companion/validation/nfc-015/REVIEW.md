# HW-NFC-015：NFC 独立升压候选

日期：2026-09-29。仅完成独立原理图及静态审查，未冻结NFC模块、主板接口或生产BOM。

TASK ID：HW-NFC-015；MODEL：Astra实施/自审，独立二审未完成；OBJECTIVE：验证原样5V NFC模块的供电实现及两级损耗；INPUTS：nfc-014、power-013、TPS61023正式手册；MUST KEEP：Power Path、电芯NTC、系统POWER不切充电路径；ALLOWED TO MODIFY：独立NFC电源候选与验证资料；DO NOT MODIFY：主板、软件、未知已有修改；TOOLS：KiCad MCP、官方CLI、Python、厂商资料；VALIDATION：逐脚合约、容差计算、ERC、PDF检查、3项错误注入；OUTPUT：独立KiCad工程、PDF、验证脚本；RISK：使能策略、模块电源容差、反灌、动态/热与采购仍待验证。

## 连接及器件依据

输入接切换后VLOGIC_SWITCHED，后接TPS61023；因此正常POWER关机可切断这一路的上游能源，不从电池裸端或常通SYS_RAW另拉旁路。另有NFC_ENABLE及100k下拉，允许控制NFC电源。使能GPIO及触发方式未定；关闭升压器也不能代替I²C掉电隔离。

按[TI TPS61023 Rev.B](https://www.ti.com/lit/ds/symlink/tps61023.pdf)第5、6、7、8节核对：1 FB、2 EN、3 VIN、4 GND、5 SW、6 VOUT；该器件支持关断输入输出断开。1µH为候选电感值，C1=10µF、C2=22µF为标称占位，实际电感饱和/温升和电容偏压有效值需定型。不能把开关限流值当作持续输出电流。R1=75k、R2=10.2k，均0.1%；R4=100k为输出泄放。

用手册PWM参考电压及电阻公差计算：名义4.970V，静态4.8362–5.1043V，不包含PFM、负载调节、布局和瞬态；25℃的20nA反馈漏电另对应约1.50mV幅值，不能当作全温保证。没有宣称满足U216全部输入容差。必须测量上电浪涌、最低输入、负载跳变和输出过冲后再判断。

当前11器件包含3个评审接口，实际候选8个器件位置（IC、电感、两电容、四电阻）。封装/料号未齐全，不能发布制造BOM。

## 验证结果

- KiCad MCP建立独立工程及六引脚符号并放置连接；仅修改本候选。
- 官方CLI ERC零违规；26个引脚与独立手册合约一致，字段整理前后网络完全相同。
- 注入VIN误接常通SYS_RAW、反馈下端误接输出、使能下拉误接电源三种错误均被脚本检出。这是网表检查，不是电路故障仿真。
- 最终PDF目视检查完成。无PCB、示波器、热或实物结果，未独立代理复审。

复现命令（仓库根目录；先重新导出以检查当前图）：

```powershell
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o docs/mini-companion/validation/nfc-015/final.xml hardware/candidates/nfc_supply_review/nfc_supply_review.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all -o docs/mini-companion/validation/nfc-015/erc.json hardware/candidates/nfc_supply_review/nfc_supply_review.kicad_sch
& 'C:/ProgramData/miniconda3/python.exe' docs/mini-companion/validation/nfc-015/verify.py
```

## 对系统负载和续航的影响

以下仅是效率85%的情景，不是模块最大额定功耗：以5V负载67.65/150/300mA计算，最低静态3.137544V系统轨需要约127/281/562mA额外电流。还要叠加MCU、显示及背光，故不能仅凭主转换器“2A”名称宣布全负载通过。67.65mA来自nfc-014已核对的模块读卡示例；150和300mA用于敏感性比较，不是测量。

此接法NFC经历TPS63802和TPS61023两级转换。沿用nfc-014其余假设、两级各85%，两天40分钟活动约消耗219.17mAh；500mAh、80%可用容量时剩余待机平均电流上限约3.82mA；800mAh约8.89mA。**该接法应使用本次数字，不能继续套用nfc-014单级模型的4.09/9.16mA。** 待机预算必须包含MCU定时醒来及总线轮询，电池容量、效率和使用占空比还未实测。

NFC使能拉低后，信号线或模块侧残余电荷仍可能反灌。整合前需完成SDA/SCL掉电电平、上拉域、泄放时间及控制次序审查；本图故意没有把未审查的I²C线接上主板。

## 采购进展和下一步

2026-09-29查得[TPS61023DRLR / C919459](https://www.lcsc.com/product-detail/C919459.html)最少5件、5件倍数，5件档单价0.2487美元，10件同档；网页库存46005。仅是国际网页快照，税费/运费不明，未锁货。此价格只含IC，不含整套升压电路。加到nfc-014的10件方案，按假设7元/美元，部分已报价物料约130.27元；仍不是整机成本。

国内U216的5/10件人民币到手价仍未取得可核验报价；国内分销页面读取失败，搜索未得到明确数量阶梯。没有把日元价、美元换算价或大批起价冒充国内小批实价，也未联系商家或下单。

已向用户提出触发体验选择：先按键唤醒两台再碰触，或熄屏待机直接碰触识别；尚未收到明确选择，“继续”没有被当作选项答复。共同供电评审已推进，等待选择期间不冻结使能策略。随后核对所选策略的待机电流和总成本，再决定是否将本图接入系统候选。
