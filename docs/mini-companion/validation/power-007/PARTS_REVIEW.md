# HW-PWR-007：器件与封装检查点

2026-09-23。TASK ID：HW-PWR-007；MODEL：Astra实施与复核、独立子代理核对电感/开关；OBJECTIVE：消除U1/L1/SW1占位与BBM依赖；INPUTS：HW-PWR-006、厂家机械图；MUST KEEP：原充电路径与其余系统网络；ALLOWED TO MODIFY：独立候选及验证资料；DO NOT MODIFY：主板/软件/外壳；TOOLS：KiCad MCP、官方pcbnew/CLI、厂家PDF；VALIDATION：逐焊盘尺寸、网表差分、ERC和可视化；OUTPUT：封装、候选图及本报告；RISK：整板、实际装配和热性能未验证。

| 对象 | 本轮决定 | 尚待验证 |
|---|---|---|
| U1 | TPS63802DLAR；项目专用DLA0010A封装 | 工厂钢网/贴装工艺，最终布局热性能 |
| L1 | DFE201612E-R47M=P2；0.47µH，专用E系列封装 | 高温、负载峰值与异常限流下的有效电感和温升 |
| SW1 | PCM12SMTBR；金触点；标准SW_SPDT_PCM12 | 外壳开孔/操纵方向、低电流寿命及采购报价 |

## U1 封装复核

依据 [TI TPS63802数据表](https://www.ti.com/lit/ds/symlink/tps63802.pdf) 附图DLA0010A、4223750/D、03/2019，PDF第35–37页。铜层顶视图左侧1→5自上而下，右侧10→6自上而下；没有额外的11号EP。左焊盘0.6×0.25mm、中心x=-0.9；右侧普通焊盘0.9×0.25mm、中心x=0.75；8脚1.3×0.25mm、中心x=0.55。纵向节距0.5mm。

8脚不整片开锡膏，两个0.55×0.25mm圆角开窗，中心x=0.175/0.925；按真实圆角面积计算覆盖约83.85%。采用0.05mm局部阻焊扩展；仍需厂家确认加工能力。庭院按最大封装外形加0.25mm余量。没有虚构3D模型或热过孔。

MCP结构检查仅确认文档图层完整，未识别封装名中的脚数，不能作为尺寸认证。`verify_dla.py`另行核对10个铜焊盘、编号、位置、尺寸和锡膏层；官方CLI导出PDF后已查看。`footprint-preview.kicad_pcb`只是单封装绘图载体，不是整板布局。

## L1 与 SW1

电感依据 [TOKO/Murata原始DFE201612E资料（分销商CODICO托管）](https://downloads.codico.com/misc/Newsletter_Passive/2016/Inductors/Murata_DFE_Serie/dfe201612e.pdf)，同时是TI列出的推荐系列。DCR上限26mΩ；5.5A是规定条件下电感下降30%的指标，4.5A是温升40°C条件下的指标，不能解释为整机电流承诺。高度上限1.2mm。推荐焊盘为两片0.55×1.6mm，中心距1.45mm。

电感封装派生自本地KiCad `Inductor_SMD:L_Murata_DFE201610P`：保留已匹配的平面焊盘，改为E系列标识并移除P系列错误高度的3D引用。遵循 [KiCad库许可CC-BY-SA 4.0及库使用例外](https://www.kicad.org/libraries/license/)，保留该来源说明；修改者为本项目。

开关依据 [Littelfuse/C&K PCM官方2025版资料](https://www.littelfuse.com/assetdocs/littelfuse-ck-slide-pcm-series-datasheet?assetguid=d2f6a96c-7a9a-4c4e-a5aa-4fe3075dffe5)，B选项为金触点，端2是公共端。不以资料未明示的BBM为前提：端1接SYS_RAW，端2接EN，端3明确NC。100k、1%下拉配合EN最大0.2µA漏电，关机电压计算20.2mV，低于0.4V。此处未把标称寿命等同于本机使用条件下已实测寿命。

开关标准封装已读取：电气焊盘1/2/3分别为(-2.25,-1.43)、(0.75,-1.43)、(2.25,-1.43)mm，尺寸0.7×1.5mm；定位孔中心±1.5/0.33mm、孔径0.9mm。官网资料文字可读，但原始PDF下载被服务器拒绝，未完成主代理对固定脚和定位孔的逐尺寸图像复核；封装指派属于候选，不等于该机械项目已放行。

## 变更验收和后续

`verify_revision.py`要求与HW-PWR-006相比只有SW1.3由GND变为明确NC；其他所有引脚网络一致，并核对三个器件的料号/封装。ERC零违规。原先power-006报告保持历史快照，不覆盖其旧状态。当前检查点仍缺真实电容型号、背光恒流、USB来源控制、ADC隔离、NFC、电池定型及整板布局；未生成生产Gerber、未采购。

操作恢复记录：跨轮次后MCP活动工程回到主工程，曾误加一个独立NC标记；发现返回目标路径后立即只撤销该UUID，Git确认主原理图无差异，再显式选择候选工程完成修改。既有`devotchi.kicad_pro`未提交修改保持原状。
