# 采购数据来源快照

原始成果根目录：`C:\Users\21604\mini-companion-v1-local-20261001\LOCAL_RESULTS\20261113-ble-implementation`。

| 此目录文件 | 原始相对路径 | 用途 |
|---|---|---|
| baseline_bom_by_ref.csv | budget/bom_by_ref.csv | 旧位号、精确型号和板外物料范围；不自动批准替代料 |
| baseline_netlist.xml | project/checks/integrated_review.xml | 2026-11-13保存态网表；用于与当前ECO比对 |
| historical_purchase_two_20261113.csv | ntc_material_qualification_20261113/conditional_documented_material_purchase_two.csv | 最新旧账逐行现金支出；原表内相对证据路径相对此原始成果根目录解析 |
| historical_budget_20261113.json | ntc_material_qualification_20261113/conditional_budget.json | 同版旧条件预算及排除项 |

历史价格不是2026-11-19成交报价，原表证据引用不能解释为本目录已有对应附件。保留原始内容以便对账，哈希由 `sourcing_validation.json` 记录。当前生产候选BOM的网表路径与哈希另列于该校验文件。
