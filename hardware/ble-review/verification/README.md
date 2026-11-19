# 验证记录

迁移来源为 2026-11-13 BLE-A0，PCB 的 SHA-256 为 `9a5667eb991860b95062c8a7ceff00264be82c1c68d4a0834d06fc491ed38ac4`。原始保存态的 [收据](BLE-A0-receipt.json) 对应当时的源文件，ERC、严格 DRC、未接线和原理图一致性问题各为零。后续修改需根据新的保存态出证。

2026-11-19 在独立临时副本实测 KiCad MCP Pro 4.19.0。MCP 磁盘读取返回 92 个封装，原理图写入测试通过修改根图标题完成；检查磁盘标题并运行 KiCad 10.0.6 官方 CLI，全部严重度 ERC 零违规。从原文件恢复标题后，根图 SHA-256 恢复为 `fd165983a2b578b0c119fdd03db69f66f18b718b5f9a58c509124d2fc14c2271`。恢复操作使用文件副本。IPC 实时 PCB 写入本轮未验证。

维护情况截至 2026-11-19。KiCad MCP Pro 在 11 月 17、18 日连续发布 4.19.0 和 4.20.0，后者修正了已打开 PCB 时的文件写入保护。本次保留已实测的 4.19.0，并在独立副本核验其文件写入能力。KiCad 10 官方 IPC 可用于连接运行中的 PCB 编辑器；原理图文件编辑需另走文件接口。随 KiCad 提供的 pcbnew Python 绑定适用于此次固定版本的板级操作，官方已列为弃用接口。正式交付使用官方 CLI 从保存后的文件输出 ERC、DRC、Gerber、钻孔和贴片坐标。[MCP 发布记录](https://github.com/oaslananka/kicad-mcp-pro/releases) · [KiCad 10 IPC 范围](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html) · [pcbnew 绑定说明](https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/index.html) · [官方 CLI](https://docs.kicad.org/10.0/en/cli/cli.html)。


## BLE-A1 最终保存态

当前 PCB 的 SHA-256 为 `35675f68e93142e07def0e88f09073ee1605d7398833b505377b71d052818954`。由此保存态独立运行全严重度 ERC、全走线/原理图一致性 DRC，报告中无忽略项；违规、未连接及不一致均为零。[最终 ERC](../quote/ERC.json) · [最终 DRC](../quote/DRC.json) · [文件与装配位号哈希](../quote/manifest.json)。

对比 BLE-A0，电池 PACK_POS 和背光 LED_A/LED_K 的线宽、长度及过孔统计一致；USB 输入与逻辑电源的支路和局部绕线有变化。新增监督器不向逻辑主轨提供工作电源。需实测启动、热插拔、发射和满亮时的主轨极值。[供电铜线宽度与长度统计](power-copper-comparison.json)。新增与移动器件的最终名义位置，已按工程高度包络和壳体模型核对。[机械筛查结果](../mechanical/ECO-clearances.json)。

复核报价包时，在最终保存和覆铜后用 `python sourcing/build_sourcing.py` 从当前网表刷新采购数据，再用 `python verification/export_quote_pack.py <新的输出目录>` 导出。独立于供应商的贴片方向预览、物理装配和功能试验。
