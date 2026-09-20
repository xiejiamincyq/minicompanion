# 补充ERC检查（2026-09-20）

在临时副本中启用`erc.rule_severities.pin_to_pin=error`和`lib_symbol_mismatch=warning`，不修改主工程规则。输入为本轮KiCad10格式基线与已补齐的本地库表，仍含feedback。

执行官方KiCad10.0.6 CLI `sch erc --format json --severity-all --exit-code-violations`，输出`erc-pin-conflicts.json`。

结果43项：12 errors、31 warnings。12错误仍为DNP外接屏表示U301的12个悬空引脚；未新增其他错误。新增告警主要来自EasyEDA符号的引脚类型为Unspecified，以及J201/J202与当前库副本不同。引脚冲突矩阵可决定具体告警严重性，所以启用规则后仍会产生warning。

此结果不能证明符号引脚类型正确或实物电路正确。不得为消警告盲换USB/电池座库符号；应按器件真实功能完善符号电气类型，并审阅库差异。主工程仍须恢复关键规则并在最终设计上重跑。

环境副本路径保存在报告source中；正式证据不依赖临时副本继续存在。没有覆盖或删除用户设计。
