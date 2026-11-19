# PCB 只读复核入口

`inspect_usb_routes.py` 用 KiCad 10 自带 Python 的 `pcbnew` 读取当前保存板，生成 `verification/usb_route_metrics.json`。只依赖 Python 标准库与 `pcbnew`，不改 PCB、工程规则或原理图；它不是 ERC/DRC 或实物功能验收的替代品。

完整保存态检查和报价导出入口见 `verification/README.md`。不要对已冻结并用于报价的板重新保存、填铜或改元件后继续复用旧 manifest。

一次性 ECO 同步、局部路由和中途诊断脚本在本机 `LOCAL_RESULTS/20261119-ble-usb-pcb-development` 留档。这些脚本依赖不同的中间保存态，不能当作最终板的重建流水线，也不能在当前工程上依次重跑。
