# PCB 常用入口

在仓库根目录，用 KiCad 10 自带 Python 执行：

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' .\hardware\ble-economy\tools\verify_pcb.py
& 'C:\Program Files\KiCad\10.0\bin\python.exe' .\hardware\ble-economy\tools\export_manufacturing.py
```

第一条读取已保存 CAD，运行全部规则与全部严重度 DRC/原理图一致性，核全部元件面别、实际网络、固定机械锚点、孔径/环宽、过孔孔口与贴片焊盘间距、地铜和文件 SHA。它会刷新验证报告，不保存 CAD。第二条要求当前板 SHA 与通过报告一致，导出制造文件和 JLC 坐标。二者不联网，不调用布线器。

辅助布线曾使用 [Freerouting v2.5.0](https://github.com/freerouting/freerouting/releases/tag/v2.5.0) 的 Java 包与官方 Temurin JRE 25.0.5+8，存放于本机用户工具目录；未改变系统 Java/PATH。固定 JAR SHA256 为 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`。执行关闭 GUI/API/MCP 服务和使用统计，只读写本机 DSN/SES。该版原生 CLI 的最小板出现序列化异常，Java 管线完成小板验证后才用于 A2。最终板仍经过人工修正和 KiCad 验证，自动布线完成提示不能替代它们。

生成布局和中间路由脚本均留在工作树外的本机开发留档；它们包含阶段性布局假设，不能拿来覆盖最终板。源码、封装与这两个复核/导出入口是交付的常用入口。
