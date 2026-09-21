# HW-FB-001：反馈支路移除与二审

2026-09-21，Astra完成集成与复核。此阶段只完成移除状态LED和振动电机；电源、NFC以及制造放行尚未完成。

## 已实施

- 从活动原理图和PCB移除D401、D402、J401、Q401、R401、R402及TP104；移除顶层feedback页实例。保留磁盘上的子页文件，不作为活动电路。
- 删除MOTOR_PWM、LED_PWM及专属连接；U101引脚33/34，即GPIO37/38，置明确NC。保留GPIO41/42原有NC，清除重复标记、错误位置标记及孤立LED连接点。
- 保留显示背光Q301/R301/R302、MCU、电源、显示、USB、三键和板框。原理图网表逐项比较确认其余器件值、封装、DNP属性及网络端点不变。
- PCB移除7个封装、48段走线、9个过孔，以及相关自动泪滴。共享GND连通路径保留；+BATT死支路清理到134.75/87.75mm的共享节点，未继续删除有用供电路径。

## 工具与恢复点

主要原理图修改使用KiCad MCP。当前MCP工具列表没有PCB删除接口，因此按用户授权降级使用KiCad 10官方`pcbnew` Python API，先生成候选副本、审核后替换主板。原板修改前状态已独立提交`364a198`，SHA256为`e6f828b748f541a01b1beb16d207282692a6cdf9e0e12027d130810b69cef53c`。

该恢复点包含此前已有的KiCad 9→10转换、6处模型路径变化及铜区变化；没有把这些先前变化冒充本次反馈删除，也未宣称它们全部只是格式差异。用户历史和恢复目录均保留。

末尾清理采用一次最小文本补丁删除已核对UUID的孤立junction；当前MCP无junction删除工具，官方CLI也无对应编辑命令。清理前已保存文件副本。MCP产生的纯空白行另经解析树完全相等验证后规范化。随后重新运行官方ERC及网表导出。

`remove_feedback_pcb.py`产生候选及逐对象删除记录；`verify_feedback_pcb.py`核对其余封装、走线、图形、配置及手工铜区定义。官方CLI重填铜会重新生成泪滴，因此自动泪滴与填充铜不作逐字相等承诺；最终DRC审核保存后的铜。

## 验证结果

| 检查 | 结果 | 证据 |
|---|---|---|
| 网表差异 | PASS；其余器件/网络不变，GPIO37/38独立 | `validation/feedback/netlist.xml`，`compare_feedback_netlists.py` |
| PCB结构差异 | PASS；剩余非铜区对象及手工铜区定义不变，仅U101两焊盘网络改为NC | `validation/feedback/pcb-comparison.json` |
| 官方KiCad ERC | 12 errors、2 warnings；均为既有U301外部显示占位符未接引脚及电源网络多名 | `validation/feedback/erc-final.json` |
| 官方KiCad DRC，重填并保存 | 0 errors、0未连接、1 warning（既有J201库封装差异） | `validation/feedback/drc-final.json` |
| 原理图/PCB一致性 | 48 warnings，全部为Datasheet空串与`~`字段差异；无连接或器件数量差异 | 同上报告的`schematic_parity` |
| 图面检查 | 官方导出PDF，检查MCU引脚、保留模块和孤立连接点 | `validation/feedback/schematic-review.pdf`（本地生成） |
| 空白检查 | `git diff --check -- hardware`通过 | 本轮命令记录 |

项目仍有继承的禁用ERC/DRC类别，详见`validation/full-rules/README.md`。以上结果不是全产品安全或制造验收；U301表示、USB封装、Datasheet字段及禁用规则仍在后续原理图整合阶段处理。

对比脚本可用`364a198:hardware/devotchi.kicad_pcb`作为PCB前态重放；运行PCB编辑脚本须使用KiCad附带Python，不是普通系统Python。脚本禁止覆盖输入和已存在候选。API进程退出时有SWIG所有权清理警告，记录在本地日志；输出已由官方CLI重新加载、覆铜并验证，未把进程清理警告当作电路通过证据。
