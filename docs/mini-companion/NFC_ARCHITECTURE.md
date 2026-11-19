# Mini Companion V1：离线双机 NFC 相遇架构研究（HW-NFC-001）

> 2026-09-29状态更正：本文早期“reader + dynamic tag首选”及“否则仅能PN7160 P2P”的结论已由后续单控制器读写/卡模拟研究替代。当前依据为[NFC_MODULE_SELECTION](NFC_MODULE_SELECTION.md)和[HW-NFC-014](validation/nfc-014/REVIEW.md)。Type-4/APDU不是用户强制要求，Type-2模拟页式交换也可评估；没有冻结生产模块。以下保留历史研究供追溯，不作为当前采购或固件要求。

> 历史状态：研究结论，**不冻结器件或电路**。本文不涉及校园卡、门禁卡或任何卡片克隆。目标仅是两台同款 Mini Companion 贴近时，不经 Wi-Fi/BLE，让双方知道对方的应用设备 ID 并各自留下相遇记录。

## 0. 已知边界与先决条件

- 已定平台为 ESP32-S3-MINI-1-N4R2（3.0–3.6 V）、SPI HS20HS072RX 显示；现有主板约 45 x 50 mm，壳体约 60 x 60 x 15.1 mm，锂电供电。
- 不能自研或自行调谐 13.56 MHz 天线；候选必须是带已调天线的成熟模块/参考小板，或在采购前能取得其天线匹配、尺寸和装配资料的成品。
- NFC 的有效距离、吞吐和稳定性由两边的天线面积、间距、平行度、塑料厚度、电池/屏/地铜和手握方式共同决定；这里不承诺“碰一碰”的具体厘米数。
- “设备 ID”应是本产品生成的随机 128-bit ID（或其公开别名），不是 NFC 芯片 UID，亦不是任何第三方卡号。芯片 UID 只可作链路诊断字段。

## 1. 先排除的误解

| 说法 | 结论 | 原因 |
| --- | --- | --- |
| 两个 reader 靠近即可自动互读 | 错误 | reader 发场、tag/target 负载调制回应；两个 reader 同时发场会冲突，且不会自动把各自 MCU 数据交换出去。 |
| 两个 tag 靠近可以互读 | 错误 | 被动 tag 不产生 reader 场，两个 tag 没有发起方。 |
| IC 数据表有 P2P，就等于 ESP-IDF 有可靠双机库 | 错误 | 还需要 NCI/驱动、发现与发起/目标角色切换、LLCP/NDEF 或自定义会话、冲突恢复及版本锁定；必须用两台实机验证。 |
| dynamic tag 是两机对等通信器 | 错误 | 它是 MCU 的 I²C 存储/邮箱与**外部 reader**之间的桥；它本身不能读另一台 tag。ST 对 M24SR64-Y 的定义就是 I²C 从机或由 13.56 MHz reader/手机访问。[ST 产品页](https://www.st.com/en/nfc/m24sr64-y.html) |

## 2. 方案比较

| 方案 | 每台器件与角色 | 两机交换是否可做 | 成熟模块/软件现实性 | 体积、电源与主要风险 | 结论 |
| --- | --- | --- | --- | --- | --- |
| A. PN532 直接 P2P | 一块 PN532 模块；任一方 initiator，另一方 target | 芯片层面可尝试 | 现成 Arduino/CircuitPython 模块和读写 tag 示例多，但常见库以读写卡为主；例如 Adafruit 明说其 Arduino 库只支持读写 tag，未支持 phone-to-shield、tag emulation 等高级功能。[Adafruit](https://learn.adafruit.com/adafruit-shield-compatibility/rfid) | 很多 PN532 成品板的天线面积接近主板；连续发场时 PN532 数据表总电流上限 150 mA、推荐天线调谐下小于 100 mA，不能直接并入既有 3.3 V 预算。[PN532 数据表](https://www.nxp.com/docs/en/nxp/data-sheets/PN532_C1.pdf) | 仅可作为低成本**概念验证**，不作为量产基线。 |
| B. PN7160/PN7161 直接 P2P | 一块有现成天线的 PN7160 模块；NCI poll/listen，initiator/target | 芯片/NCI 宣称可做 | PN7160 为 Active，I²C/SPI、3.3 V host、P2P initiator/target 都有一手资料。[NXP 产品页](https://www.nxp.com/products/PN7160) | RF driver 2.7–5.25 V、最大 250 mA；现阶段未找到同时满足 `<=45x50 mm`、已调天线、可稳定采购、并有 ESP-IDF 双机 P2P 示例的成品模块。更关键：NXP 写明 P2P 从 2024 起停止维护；数据表还限定 P2P 只到 firmware 12.50.0A。[数据表](https://www.nxp.com/docs/en/data-sheet/PN7160_PN7161.pdf) | 技术上最接近“单模块对等”，但软件生命周期风险高，先不推荐。 |
| C. ST25R3916 front-end 直接 P2P | 一颗 front-end + 外部天线；软件控制 initiator/target | 芯片能力足够 | ST 标为 Active，支持 active/passive P2P、initiator/target，至 424 kbit/s。[ST 产品页](https://www.st.com/en/nfc/st25r3916.html) | 封装虽小（5 x 5 mm），但它要天线、匹配与 RF 布局；这直接违背“不自研天线”，也未发现适合本尺寸的成熟 P2P 模块。 | 排除，除非以后解除天线约束并投入 RF 设计与验证。 |
| D. reader + dynamic tag（建议先验证） | 每台 = 一个成熟 NFC reader 模块 + 一个带天线的 Type-4 dynamic-tag 小板；单次一方 reader，另一方 tag | 可以，且不需要 NFC P2P | M24SR64-Y 是在产的 I²C + ISO14443-A Type-4 dynamic tag，有 GPO 可报告 RF 操作；ST 有带 14 x 14 mm 双层天线的 ANT7-T-M24SR64 参考小板和 Gerber。[Tag](https://www.st.com/en/nfc/m24sr64-y.html) [天线参考板](https://www.st.com/en/evaluation-tools/ant7-t-m24sr64.html) | 多一套器件与天线，会挤占 45 x 50 mm 板；tag 待机量级低（数据表 3.3 V、RF off 最大 5 µA，RF on 最大 30 µA），reader 的发场脉冲才是电池主风险。[M24SR 数据表](https://www.st.com/resource/en/datasheet/m24sr64-y.pdf) | **首选验证架构**：协议角色清晰、避开 P2P 软件弃维护风险；但 reader 成品 SKU、总装尺寸和量产供应尚未确认。 |
| E. 只有 dynamic tag | 每台一块 tag | 不可以 | NFC 手机/reader 可以读它；两台 tag 不会形成会话。 | 省电省空间，但不符合离线双机相遇。 | 排除。 |

### PN532 生命周期结论

PN5321A3HN 已被 NXP 标为 **Not Recommended for New Designs**，且 NXP 明确建议新设计改用 PN7160。[NXP 生命周期页](https://www.nxp.com/products/rfid-nfc/nfc-hf/nfc-readers/nfc-integrated-solution:PN5321A3HN) 因此即便淘宝/开发板市场上的 PN532 模块仍很多，也只能采购两块作早期链路实验，不能将“模块还买得到”写成长期供货保证。

## 3. 建议的可验证架构：reader + Type-4 dynamic tag

这不是“两个 tag 互读”，也不是“两个 reader 自动互读”。每台同时拥有两种功能，但每一次相遇会话只有一个 reader 和一个 tag：

```text
设备 A                                        设备 B
ESP32 ─I²C/SPI─ reader 模块 ))) 13.56 MHz ((( dynamic-tag 小板 ─I²C/GPO─ ESP32
  生成 request / 读取 response                         写入 request / 生成 response
  本地落库 A<->B                                     本地落库 B<->A
```

建议协议（上层为产品私有 TLV/二进制记录，不要求把应用载荷伪装成校园卡）：

1. 每台开机持久化 `device_id`、单调计数器与随机 `nonce` 来源。tag 中预置只读的协议版本与公开 `device_id`，并暴露一个短请求槽和响应槽；GPO 接到 ESP32 可中断 GPIO。
2. 靠近时，两台都先在**被动 tag**状态短暂监听。随后各自随机退避进入短 reader poll 窗口；检测失败/场冲突/超时立即回退到监听，并采用指数退避。禁止双方持续发场。
3. 首个成功 reader（A）读取 B 的公开 ID，写入 `{version, session_nonce, A_id, A_counter, request_crc}`。B 的 GPO/RF 事件唤醒 MCU，B 校验长度、版本、CRC、重放窗口后先持久化“收到 A”的暂存记录。
4. B 写回 `{session_nonce, B_id, B_counter, status=accepted, response_crc}`；A 轮询读取、比对 nonce/B_id 并持久化“收到 B”的记录。A 必须再写 `commit`（本项目的双方确认要求）；B 在读到 `commit` 后把暂存记录改为已确认。
5. 若在超时前没有对应 nonce 的响应/commit，双方记录为 `incomplete`，下次碰触以同一 nonce 去重/补偿，而不是把一次物理贴近误标成双方确认。

这使双方确认的语义可审计：B 仅在收到 A 的请求后记录 A；A 仅在读到 B 对同一 nonce 的确认后记录 B；B 收到 commit 后还知道 A 已收到确认。两端均写入 `session_nonce`、双方 ID、时间（单机本地时间只作显示）、协议版本和结果，避免仅靠 RF UID 或时间相近合并记录。

### 身份与安全边界（需要产品决策）

- 未配置密钥时，这只是**近距离发现**：恶意设备可伪造 `device_id` 或重放可读 tag 内容；不要将它用于支付、门禁、解锁或身份认证。
- 若“识别”须抵抗伪造，需要在首次受控配对时建立每设备密钥/公钥，并对 `{双方 ID, nonce, counter, protocol_version}` 做 MAC/签名；密钥存储与丢机撤销将成为额外产品需求。
- dynamic tag 内的公开 ID/状态可能被任何兼容 reader 读取。若需要隐私，tag 只公开滚动匿名提示，真正 ID 在已认证挑战响应后返回；这会提高 reader 与软件实现难度。

## 4. 机械、电源、采购：已知与未知

| 项目 | 已有证据 | 必须在下单前拿到的证据 |
| --- | --- | --- |
| tag 天线 | ST ANT7 参考板为 14 x 14 mm 双层已调天线，含 I²C 测试点、GPO 和 M24SR64-Y。[ST](https://www.st.com/en/evaluation-tools/ant7-t-m24sr64.html) | 采购的是完整可装的小板还是仅参考资料；小板总体长宽厚、连接器/焊线方式、人民币含税交期。不能把 Gerber 当成已采购模块。 |
| reader 模块 | PN532 市场模块通常提供 SPI/I²C/UART；例如 Waveshare 列明 3.3/5 V 与三接口，但其页面未给本报告可复核的全尺寸/电流资料。[Waveshare](https://www.waveshare.com/product/iot-communication/short-range-wireless/nfc-rf/pn532-nfc-hat.htm) | 指定品牌+料号，带天线后的 L/W/H、3.3 V 逻辑兼容性、峰值/平均电流、休眠控制脚、固件版本、库存与可追溯采购链接；实物 3D 与壳体干涉检查。 |
| 电源 | PN532 芯片资料中的电流值仅用于预算预警，不能替代成品模块实测；PN7160 RF driver 最大 250 mA。 | 在现有 ME6211、电池内阻和显示背光同时工作的实测电压跌落、峰值电流、复位次数、充电边用边充行为。不要按 tag 的微安级待机推断 reader 发场功耗。 |
| 60 mm 级外壳 | 45 x 50 mm 主板与 60 x 60 x 15.1 mm 外壳没有很多高度余量。 | 堆叠高度（排针通常会失败）、固定柱、FPC、USB-C、电池和屏背之间的净空；优先贴装/柔性引线，不以双排针叠板作为量产布局。 |
| RF/屏蔽 | 13.56 MHz 磁场会受电池金属箔、显示 FPC/背板、地铜和手握影响；ST25R3916 资料也专门强调 noisy LCD 周围的天线设计挑战。[ST](https://www.st.com/en/nfc/st25r3916.html) | NFC 天线放在塑料壳一面、远离电池和显示背板；金属件不能夹在天线与对端设备之间。若需要磁性屏蔽/铁氧体片，必须随选定模块做距离和温升实测，不能只凭宣传页选厚度。 |

## 5. 两台同款设备的验证门槛（选型冻结前）

下面是可重复的验收门槛，而不是“手机能读 tag”这种替代测试。测试固件可最小化，但必须运行在两台 ESP32-S3 上，不依赖 Wi-Fi/BLE，也不读取或写入任何第三方卡。

1. **物理与接口**：两套候选模块都能由 3.3 V/指定供电稳定启动；ESP32 用所选 SPI/I²C 和 IRQ/GPO 完成 1,000 次单机 read/write，不出现复位、总线锁死或数据错包。
2. **双机角色**：A/B 交换摆放、同时唤醒、相向贴近 500 次；每次日志必须显示一方 reader、另一方 tag，禁止把“检测到场”算成功。
3. **数据闭环**：每次成功都要求 A、B 各自保存对方应用 ID 和相同 nonce；B 的 `accepted` 与 A 的 response 必须匹配。断开在 request、response、commit 三个阶段各 100 次，不能产生“双方确认”假记录。
4. **碰撞恢复**：两台都在 poll 的最坏启动条件下连续 200 次；应在定义的超时内通过退避形成唯一 reader，失败只能写 `incomplete` 并可下一次恢复。还要加入第三台设备在场的 100 次测试，确认不会把第三方 ID 误写入会话。
5. **壳体与功耗**：在最终屏、电池、显示背光、NFC发场/休眠、USB 充电、手握和不同贴合方向下，各做不少于 100 次；报告成功率、95% 时延、峰值电流、最低 3.3 V、电池电量差和失败日志。通过标准应由产品方决定，建议先把“同壳体条件下双向已确认成功率 >=99% 且无 MCU 复位”作为冻结前最低线。
6. **版本可复现**：锁定模块品牌料号、板版本、PN7160 固件（若用）、ESP-IDF 版本、协议版本、测试工装和原始日志；任何模块替换后重跑上述测试。

## 6. 当前建议与待决策事项

**建议**：先采购/借测两套“现成 reader 模块 + 现成 M24SR64-Y（或等价在产 Type-4 dynamic-tag）带天线小板”，按第 5 节做双机闭环 PoC。它使用明确的 reader/tag 非对称会话，能让两台同款设备都记录相遇，同时不把已停止维护的 P2P 软件当作基础能力。验证通过后才评估能否放进 60 mm 级壳体；本结论不要求更换 MCU、显示，也不修改现有 PCB。

**不建议现在冻结 PN532**：它可作为便宜的 reader 试验样品，但 NXP 已将芯片列为 NRND；若只配一块 PN532 reader，它只能让读方知道对端 tag，不能使两台同款设备天然双向确认，必须配合上述 tag、GPO 和确认协议。

需要产品/硬件负责人决定的边界：

1. 相遇记录是否只需“近距离可见声明”，还是必须抗伪造/重放；后者需要密钥生命周期设计。
2. 是否接受每台两块 NFC 小板及其面积、高度、BOM 与采购风险；若不接受，则转为 PN7160 P2P 原型，但必须接受其 P2P 维护停止及固件上限风险。
3. 成功距离/时延/电池消耗的可量化目标，及是否允许用户按提示保持贴合至 `commit` 完成。
4. 首批可接受的明确 reader 与 dynamic-tag 模块料号、供货渠道、成本和 3D 尺寸。未取得这些资料前，不可声称该方案已装得下 45 x 50 mm PCB 或可量产。

## 来源（均为一手厂商或模块厂商页面）

- NXP：[PN532 生命周期与替代建议](https://www.nxp.com/products/rfid-nfc/nfc-hf/nfc-readers/nfc-integrated-solution:PN5321A3HN)、[PN532 数据表](https://www.nxp.com/docs/en/nxp/data-sheets/PN532_C1.pdf)、[PN7160 产品页](https://www.nxp.com/products/PN7160)、[PN7160/PN7161 数据表](https://www.nxp.com/docs/en/data-sheet/PN7160_PN7161.pdf)、[PN7160 用户手册](https://www.nxp.com/docs/en/user-manual/UM11495.pdf)。
- ST：[ST25R3916](https://www.st.com/en/nfc/st25r3916.html)、[M24SR64-Y](https://www.st.com/en/nfc/m24sr64-y.html)、[M24SR64-Y 数据表](https://www.st.com/resource/en/datasheet/m24sr64-y.pdf)、[ANT7-T-M24SR64](https://www.st.com/en/evaluation-tools/ant7-t-m24sr64.html)。
- 模块软件/采购现实性参考：[Adafruit PN532 库能力说明](https://learn.adafruit.com/adafruit-shield-compatibility/rfid)、[Waveshare PN532 模块页](https://www.waveshare.com/product/iot-communication/short-range-wireless/nfc-rf/pn532-nfc-hat.htm)。模块商网页的库存、价格和规格均会变化，须在下单当日复核。

## Astra 二审：尚未闭环，禁止按本研究直接落板

- reader+tag是研究候选，不是已经证明优于单模块的最终选择。还须比较同一控制器在reader与Type-4 card-emulation之间切换的方案；card-emulation不同于LLCP P2P，不能因P2P停止维护而直接排除。
- 同机reader会读到自己的tag，两个近邻天线会互相耦合。必须验证本机tag的RF禁用/仲裁、对端选择、两套天线失谐以及第三台干扰；仅忽略自身ID不足以证明RF可靠。
- M24SR的RF/I²C访问所有权与会话释放必须按数据表实现并验证。不能假设RF仍占有会话时MCU可随时写response；GPO是事件提示，不保证两接口可并发访问。
- Request/response/commit只是协议草图。断链时不可能凭空保证两端同时获知最终提交；采用持久化pending、幂等session ID、可重试确认与重连补偿。没有收齐证据的一端显示待确认，不谎报双方已成功。
- 原理图集成仍待准确模块SKU、实测峰值、尺寸及固件接口证明；库存/人民币成本尚未核实。本轮未授权或执行采购。
