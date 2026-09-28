# NFC 独立升压评审图

2026-09-29，HW-NFC-015。用KiCad打开本目录nfc_supply_review.kicad_pro，或查看[PDF](../../../docs/mini-companion/validation/nfc-015/review.pdf)。本图尚未接入主板，工具生成的PCB为空白，不是布局成果。

TPS61023DRLR从VLOGIC_SWITCHED升至约4.97V；NFC_ENABLE由外部待定控制，100k下拉。三个J接口均是评审边界，不是生产连接器。NFC模块、I²C隔离、实际电感/电容料号及封装未完成；不得直接下单。

11个器件含3个评审接口，26个引脚网表合约通过；ERC零违规，3项错接注入被检出。KiCad MCP生成符号、放置和连线；字段整理后再次导出网表核对无电气变化。详细计算与适用限制见[审查记录](../../../docs/mini-companion/validation/nfc-015/REVIEW.md)。
