# HW-PWR-005-USB：Astra 二审补充

2026-09-22。状态：供下一张独立前端评审图使用；控制电路尚未实施，不能据此下单。

TASK ID：HW-PWR-005-USB；MODEL：Astra；OBJECTIVE：解除错误的 USB 挂起阻塞并核对供电边界；INPUTS：核心评审图、TI 和 USB-IF 原始资料；MUST KEEP：USB-C 5V、原生 USB 数据、关机充电；ALLOWED TO MODIFY：候选评审资料；DO NOT MODIFY：软件、主板及机械；TOOLS：官方资料、KiCad CLI、独立网表校验；VALIDATION：逐表查证、核心 ERC/网表复核；OUTPUT：本文和核心检查点；RISK：前端尚未完成，不能声称整机 USB 合规。

## 已解决的规范问题

[USB-IF Type-C Functional Test Specification Rev.0.91，2024-03-03](https://www.usb.org/sites/default/files/USB%20Type%20C%20Functional%20Test%20Specification%202024%2003%2003.pdf)，TD4.10.3，PDF第108–109页：步骤8允许宣告1.5A的源在USB2挂起时仍提供至1.5A；步骤12对3A相同。因此，非PD路径中持续有效的CC 1.5A/3A宣告可支持本机挂起时继续以小于500mA取电。不能把普通Default USB的挂起限制套用到此情况。该证据解除此前评审的这一疑点，不等于完成全部USB认证。

失去较高电流宣告后必须重新限流；不能锁存首次插入的结果。Default、未识别来源和BC1.2判定仍分别处理。

## TUSB320LAI：修正供电假设

[TI Rev.D](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf) 表6.3的VDD推荐范围是2.7–5.0V，绝对最大值6V不能作为推荐设计值。直接以可能高于5V的VBUS供电不成立。后续图采用VBUS侧独立稳压供电的方向；型号、容差、启动时间和掉电反灌尚待落实。

表3的OUT1/OUT2编码依次为HH未连接、HL已连接Default、LH为1.5A、LL为3A。因此在供电及有效状态成立时，A_CC可由NOT OUT1得到。两个输出为开漏，必须上拉到同一控制器电源域；不能上拉到裸VBUS。PORT接地、ADDR悬空、内部Rd替代外部两个5.1k，不并联。VBUS_DET按数据表经指定高阻连接。未上电和初始化期间不得把输出不确定态当作许可。

## 不沿用旧控制真值表作为接线指令

旧表的逻辑演算正确，但只描述抽象许可A，不证明A的产生方式正确。500mA是USB口总预算；核心之外的NTC分压、检测器、稳压器和逻辑也耗电。BQ24072T的500mA档上限已达500mA，不能宣称整机仍严格不超过500mA。

后续优先利用已有3.48k、1% ILIM设定，许可足够时选择EN2/EN1=10，其计算最大493.44mA，留下约6.56mA给旁路负载；是否足够必须以各支路最大值相加验证。普通未枚举100mA状态同样存在旁路余量问题，不能仅因充电器带USB100档就宣布解决。前端图完成前，旧E1/E2方程不再作为最终接线依据。

## GOOD_BAT和关机边界

[TI BQ24392 Rev.G](https://www.ti.com/lit/ds/symlink/bq24392.pdf) 的CDP且GOOD_BAT低状态只允许100mA；CHG_DET高不能单独视为500mA许可。GOOD_BAT长时间低还会触发32–45分钟DBP超时。不能以周期翻转GOOD_BAT绕过计时器。必须定义真实的电池/系统可启动判据，再决定数据开关和充电授权。

适配器关机充电是保留要求；普通电脑端口在设备关机、无电、挂起时的充电能力尚未冻结，不能说所有USB来源均已支持。POWER必须只控制系统支路，不能切断充电芯片、电芯NTC或电池保护回路。

## 下一实施项

完成独立前端图的稳压/默认态、来源识别和总输入预算，再接入后级稳压与POWER。预算需同时计入检测器和逻辑；尚未证明这些器件能满足整机50–100元。核心评审图可保留作为已验证检查点，不因前端未完成而反复重画，也不能提前替换主板电源页。
