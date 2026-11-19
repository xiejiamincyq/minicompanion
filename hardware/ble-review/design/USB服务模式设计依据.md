# BLE-A1 USB 服务模式与电源开关

这是基于 BLE-A0 的硬件候选，不是生产放行。原理图新增 18 个板载元件，共 113 个采购对象，其中 3 个板外对象；PCB 应有 110 个器件。原有 338 个引脚网络中，322 个保持不变，16 个有意改变：USB 接口/隔离/绑带共 15 个，板外 POWER 开关的 OFF 掷端 1 个。验证脚本检查所有旧引脚和旧器件值/封装/采购字段，防止局部修改误改原供电、背光和显示链路。

原 BLE-A0 保存在 `C:\Users\21604\mini-companion-v1-local-20261001\LOCAL_RESULTS\20261113-ble-implementation\project`；这里没有改动它。新版以 `project/mini_companion_integrated.kicad_sch` 为入口。

## 操作合同

| 状态 | 设计行为 |
|---|---|
| NORMAL，USB 插入 | 原 VBUS 禁止运行链路有效；主系统关闭，原 NTC 条件控制充电。 |
| SERVICE，USB 插入，POWER ON | SERVICE 同时使 TS 禁用充电、解除 VBUS 对运行的禁止；主系统全部由有电的保护电池供电。USB 数据由两路电压监督器决定是否接通。 |
| SERVICE，POWER OFF | 主系统关闭；仍不充电。不能把 SERVICE 当普通充电状态。 |
| USB 未接 | VBUS 监督器和 DATA_EN 下拉使 USB 数据断开，电池不能使设备向外部未供电总线持续发送。 |
| 电池缺失或耗尽 | 不提供 USB 单独供电烧录。先返回 NORMAL 充电，再进入 SERVICE。 |

设计期免开壳恢复流程：**拔 USB → POWER OFF，等待主轨放电 → 拨 SERVICE → 按住 BOOT → POWER ON → 接普通 USB 数据线 → ROM 枚举后松开 BOOT**。首板测出实际可靠放电等待时间；暂按至少 5 秒并在台架确认主轨/MCU_EN 已降至低电平，不能把经验等待时间当成测量证据。结束时先拔 USB，再返回 NORMAL。开壳时可用内部 RESET 配合 BOOT 作为备选。这些流程尚未用实板验证。

SW7301 是非短接型 DPDT，2/5 为公共端并接地；SERVICE 时 2→3 接 NTC_TS，5→6 接 VBUS_INHIBIT_BASE；NORMAL 的 1/4 留空。**不能假设两个机械极同时切换**，因此只在 USB 拔除后换模式。来源：[Littelfuse/C&K JS 系列](https://www.littelfuse.com/assetdocs/littelfuse-ck-slide-js-series-datasheet?assetguid=aba42b08-0d2c-423b-813d-a2faa5a3bb14)，JS202011SCQN 的 N 为 non-shorting，SC 封装图与 PCB 自建封装另有复核记录。

## USB 通路与断电边界

J201 的 A6/B6 为 D+、A7/B7 为 D−，经 D7301 双路对地 ESD、U1101 未使用的通道 3/4、R7302/3 的 22Ω 串阻，连接 ESP32-S3 GPIO20/19。串阻靠 MCU，ESD 靠连接器。没有添加 VBUS 到系统电源的通路，也没有改变 TMUX 的 ADC/背光两路。GPIO0 用 R7301 10k 上拉和 SW7302 直接拉低；GPIO46 用 R7308 10k 下拉，保证下载绑带的静态方向。引脚见 [Espressif 硬件连接](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html#hardware-connection)；GPIO0/46 的联合下载条件见 [Boot Mode Selection](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html)。

TMUX1511 的 SEL 是失效安全逻辑输入，VIH≥1.2V、VIL≤0.45V；正常供电允许信号高于 VDD（至 2×VDD，最高 5.5V）。掉电保护针对 0–3.6V 信号，VDD=0 时 I/O 漏电最大 ±2µA。其 3GHz 典型带宽、6pF 最大导通电容适用于本次 USB Full-Speed 12Mbps 的初步选型；这不等于本板眼图或阻抗已通过。特别不能把掉电保护外推为整个缓慢电源过渡过程的零灌流保证。[TI TMUX1511 Rev.B](https://www.ti.com/lit/ds/symlink/tmux1511.pdf)

D7301 采用 Nexperia PESD5V0U2BT,215：1/2 为线路、3 为公共地，最大结电容 3.5pF，不依赖电源轨。器件 ESD 指标不代表整机已通过 ESD 测试。[厂家数据表](https://assets.nexperia.com/documents/data-sheet/PESD5V0U2BT.pdf)

## 两路硬件电压资格

U7301 TPS3808G01 检测 VBUS，U7302 TPS389001 检测主轨；两个开漏输出共同接 `USB_DATA_EN`。R7306 10k 从 USB_3V3 上拉，R7307 100k 下拉，只有两者均释放时数据才连通。两个监督器均由 USB_3V3 供电，避免主轨为零时依赖未供电监督器的输出。USB_3V3 缺失时没有上拉电源；没有把 GPIO 直接接到 VBUS。

| 项目 | 名义值 | 计算边界（元件温度 0–45°C） |
|---|---:|---:|
| VBUS 下降断开 | 4.455V | 4.3505–4.5601V |
| VBUS 上升接通 | 受迟滞影响 | 最坏上限 4.6968V |
| 主轨下降断开 | 2.967V | 2.9299–3.0042V |
| 主轨上升接通 | 受迟滞影响 | 最坏上限 3.0290V |
| 主轨低端估计与上升门限余量 | 基线低端估计 3.0711V | 约 42mV，未含动态负载/噪声 |

VBUS 分压为 100k/10k，主轨分压为 15.8k/10k；四只均指定 0.1%、25ppm/°C。计算同时取电阻误差、温漂、芯片阈值/迟滞及输入偏置的最坏方向。VBUS 下降边界对 4.35V 只有约 0.5mV 的模型余量，**不包含焊接漂移和老化**，不能作为全面 USB 合规结论。两台首板实际扫阈值；需要扩大温度/寿命规范时应重选比值，而不是沿用此估算。计算代码和结果位于 `verify_usb_eco.py`、`verification/usb_static_bounds.json`。

TPS3808G01 的 SENSE 是 pin5、MR 是 pin3；CT 留空，释放延时 12–28ms。TPS389001 的 pin1=SENSE、2=GND、3=MR、4=VDD、5=CT、6=RESET，CT 留空。TPS3890 明确允许 SENSE 相对 GND 至 5.5V、独立于供电电压；这里最高约 1.25V，避免把未供电输入钳位当作设计前提。开漏低电平与 TMUX VIL 有静态余量，仍需确认 USB_3V3 的升降过程。[TPS3808 Rev.N](https://www.ti.com/lit/ds/symlink/tps3808.pdf)、[TPS3890 Rev.A](https://www.ti.com/lit/ds/symlink/tps3890.pdf)

U7302 使用已冻结的 KiCad WSON-6 1.5×1.5mm/P0.5mm 封装，无 EP；pin1 铜为 0.85×0.28mm，其余为 0.75×0.28mm。比 TI 建议长多 0.05mm、宽多 0.03mm，保留同列 0.22mm、pin1 对面最小 0.30mm 铜间距。工程上接受此小幅增量用于两台候选；它不是 TI 建议尺寸的逐项复制。钢网、阻焊和首板桥连仍须 SMT DFM/实物检查。

该主轨门限用于避免主轨未建立时过早连接 USB，不保证在整个 USB 允许输入幅度、极快电源崩落、MCU 棕断及异常主机输出条件下均没有瞬态灌流，也不保证 MCU 在 2.97V 下正常工作。样机必须捕获这些边界。已有 USB 后再 POWER ON 的反例由主轨监督器覆盖；单用 EN_RUN 提前接通不满足此条件，因此没有采用该方案。

## 拔线、电流、充电与热

R7309 是 2.7k、1206、250mW，接原始 VBUS 到地。原始 VBUS 电容 C7101/C7102/C7107 共 3.3µF，取 +10% 并加 0.1µF 局部/线缆预算后为 3.73µF。只按 R7309 放电、忽略其他有利放电路径，从 5.5V 到最低检测阈值的 RC 估算约 2.39ms。监督器响应、主机端残余供电、连接器先后接触和线缆实际电容没有被此计算覆盖；拔线后 DATA_EN 低及设备 D± 停止驱动 ≤3ms 是首板测试目标。[Espressif 自供电设备要求](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html#self-powered-device)

按电阻公差/温漂，R7309 在 20V 误压故障域约 150mW，在 5.5V 约 11.35mW，必须保留 250mW 等级和对应降额条件，不能换成 0.1W 0603。额定功率不证明外壳/电池表面温度≤45°C。采购型号为 UNI-ROYAL 1206W4F2701T5E/C17950；额定值见 [LCSC 官方目录](https://www.lcsc.com/product-detail/C17950.html)。常温封装功率有余量，壳内温升及误压受控测试仍归首板验收。

保守叠加原慢充最大 85.47mA、原辅助预算 5mA、原误差预留 2mA 和全部新增约 2.47mA，默认 USB 稳态估算约 94.94mA；SERVICE 禁充电时系统负载来自电池。此预算不能证明 USB 浪涌、挂起电流或快充识别已经通过，相关基线限制仍有效。

BQ25170 的 TS 拉至低于禁用阈值是停止充电，而不是忽略温度继续充电；SERVICE 关闭充电、允许电池运行，不提供边充边用。USB 断开后再拨回 NORMAL，让 TS 探头恢复原回路。不要以 MCU 软件代替这条硬件关系。[BQ25170 数据表](https://www.ti.com/lit/ds/symlink/bq25170.pdf)

## POWER 两线安全修正及启动时序

SW7201（SS-12D01-G040）只接 ON 和 COMMON：J7201.1→SW7201.1，J7201.2→SW7201.2。SW7201.3 留空并绝缘；J7201.3 保持板上 GND 铜焊盘但不接线。这样即使滑动触点跨接两个掷端，也没有直接短接电池正负极的回路。R7114 10k 保持 EN_RUN 默认下拉；断线/开关开路时为关闭，闭合电阻逐步升高主要导致不能可靠开启，而不是造成直接电池短路。触点焊死仍可能无法用 POWER 关机，不能宣称覆盖该故障。

供应商精确商品页 [C2876014](https://item.szlcsc.com/3084347.html) 所附同厂家 GXXX 系列图包含 G040；新件接触电阻≤50mΩ、绝缘电阻≥100MΩ（250V 测试）、额定寿命 10000 次且标 non-shorting。4.2V/100MΩ≈42nA 仅是新件绝缘估算；没有寿命后污染/绝缘劣化保证。沿用基线 18.2µA 最坏方向漏电模型，再预留 5µA 线束/板面泄漏，加开关估算，10k +1% 下 EN_RUN≈0.235V，低于项目 0.3V 门槛。总正向泄漏不得超过约 29.7µA；这个门槛要在真实装配件上测，而非用供应商寿命次数替代。[厂家系列图](https://datasheet.lcsc.com/datasheet/pdf/af2c04499242010f9bc8773a044bd472.pdf?productCode=C5446804)

原 MCU EN 网络是 **R101=10k、C103=1µF**（C102=100nF 为电源去耦），名义 RC 为 10ms。没有给 GPIO0 加电容；BOOT 提前按住且保持至枚举，覆盖 CHIP_PU 上升后至少 3ms 的绑带保持要求。RC 不是精确电源监督器，掉电再快速上电可能没有完全复位，因此 POWER OFF 后放电以及低电量启动都需要测量。没有增加外部 UART 自动 DTR/RTS 复位电路。[Espressif 绑带/复位建议](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)

## 两台首板必须记录的结果

1. 正常充电关机、SERVICE 禁充电、空电池先充再恢复；分别测电流及 NTC 热/冷/开路/短路行为。保持原安全台架顺序，不把真人电池用作首次故障测试负载。
2. USB 已接再开关 POWER、USB 热插/拔、慢斜坡、耗尽/移除保护包：同时捕获 VBUS、USB_3V3、VLOGIC_SWITCHED、DATA_EN、D±，核查持续反灌、电源回升和检测窗口。
3. 普通电脑数据线正反插，免开壳 BOOT+POWER 恢复；一次空白/无效应用恢复及重复烧录。保留 UART 测试点作为台架备用；不承诺软件自动复位已验证。
4. 真实装壳、最大背光/BLE 负载下测主轨瞬态和温升，确认没有 USB 反复掉线；测表中实际下降/上升阈值。
5. POWER 线束拔除/单线断开、OFF 和滑动途中检查 EN_RUN≤0.3V；低电量下 ON≥1.3V。完成不少于 20 次操作、轻晃线束后复测，检查焊点/绝缘和接触压降。此为两台装配筛查，不是寿命认证。

保存状态 ERC、网表合同和静态算术通过仅代表 CAD 与计算一致；PCB DRC、封装/机械、装配库存、实测与最终制造放行分别由对应证据负责。重现原理图检查：`python design/verify_usb_eco.py --refresh`。
