"""Preserve KiCad pad geometry; correct E-series identity and omit wrong P model."""
from pathlib import Path
import pcbnew as p
root=Path(__file__).resolve().parents[4]
io=p.PCB_IO_KICAD_SEXPR()
src='C:/Program Files/KiCad/10.0/share/kicad/footprints/Inductor_SMD.pretty'
fp=io.FootprintLoad(src,'L_Murata_DFE201610P')
assert fp
for pad in fp.Pads():
    pos,size=pad.GetPosition(),pad.GetSize()
    assert abs(abs(p.ToMM(pos.x))-.725)<1e-6 and pos.y==0
    assert abs(p.ToMM(size.x)-.55)<1e-6 and abs(p.ToMM(size.y)-1.6)<1e-6
name='L_Murata_DFE201612E_2x1.6mm_H1.2mm'
fp.SetFPID(p.LIB_ID('MiniCompanionPower',name))
fp.SetValue(name)
fp.SetLibDescription('DFE201612E; derived from KiCad DFE201610P matching pad pattern; body height max 1.2mm; no P-series 3D. TOKO original data: https://downloads.codico.com/misc/Newsletter_Passive/2016/Inductors/Murata_DFE_Serie/dfe201612e.pdf')
fp.Models().clear()
io.FootprintSave(str(root/'hardware/candidates/system_power_review/MiniCompanionPower.pretty'),fp)
print('E-series footprint saved; two 0.55x1.6 pads, center spacing 1.45mm, no misleading 3D model')
