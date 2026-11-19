"""TI DLA0010A land/stencil pattern, drawing 4223750/D, 03/2019.

Use KiCad's official pcbnew Python, not the generic IPC DFN generator:
this package has asymmetric copper and a split paste aperture on pin 8.
"""
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[4]
LIB = ROOT/'hardware/candidates/system_power_review/MiniCompanionPower.pretty'
NAME = 'TI_DLA0010A_VSON-HR-10_2x3mm_P0.5mm'
LIB.mkdir(exist_ok=True)
fp = p.FOOTPRINT(None)
fp.SetFPID(p.LIB_ID('MiniCompanionPower', NAME))
fp.SetAttributes(p.FP_SMD)
fp.SetLibDescription('TI DLA0010A, drawing 4223750/D 03/2019; asymmetric pads; pin 8 split paste; https://www.ti.com/lit/ds/symlink/tps63802.pdf')
fp.SetKeywords('TPS63802 DLA0010A VSON-HR HotRod')

def vec(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))

def pad(number, x, y, w, layers):
    item = p.PAD(fp)
    item.SetNumber(str(number))
    item.SetAttribute(p.PAD_ATTRIB_SMD)
    item.SetShape(p.PAD_SHAPE_ROUNDRECT)
    item.SetPosition(vec(x, y))
    item.SetSize(vec(w, .25))
    item.SetRoundRectRadiusRatio(.2)  # R0.05 on 0.25 mm height
    layer_set = p.LSET()
    for layer in layers:
        layer_set.AddLayer(layer)
    item.SetLayerSet(layer_set)
    item.SetLocalSolderMaskMargin(p.FromMM(.05))
    fp.Add(item)

for number in range(1, 6):
    pad(number, -.9, (number-3)*.5, .6, [p.F_Cu, p.F_Paste, p.F_Mask])
for number in (6, 7, 9, 10):
    pad(number, .75, (8-number)*.5, .9, [p.F_Cu, p.F_Paste, p.F_Mask])
pad(8, .55, 0, 1.3, [p.F_Cu, p.F_Mask])
for center in (.175, .925):
    pad('', center, 0, .55, [p.F_Paste])

def line(a, b, layer, width):
    item = p.PCB_SHAPE(fp)
    item.SetShape(p.SHAPE_T_SEGMENT)
    item.SetStart(vec(*a)); item.SetEnd(vec(*b))
    item.SetLayer(layer); item.SetWidth(p.FromMM(width)); fp.Add(item)

# Nominal 2 x 3 body with pin-1 chamfer. Courtyard covers max body +0.25.
outline = [(-1,-1.1),(-.6,-1.5),(1,-1.5),(1,1.5),(-1,1.5),(-1,-1.1)]
for a,b in zip(outline, outline[1:]): line(a,b,p.F_Fab,.1)
outline = [(-1.45,-1.8),(1.45,-1.8),(1.45,1.8),(-1.45,1.8),(-1.45,-1.8)]
for a,b in zip(outline, outline[1:]): line(a,b,p.F_CrtYd,.05)
line((-.8,-1.65),(.8,-1.65),p.F_SilkS,.12)
line((-.8,1.65),(.8,1.65),p.F_SilkS,.12)
line((-1.2,-1.65),(-.95,-1.65),p.F_SilkS,.12)
for field, value, y, layer in [(fp.Reference(),'REF**',-2.2,p.F_SilkS),
                               (fp.Value(),NAME,2.2,p.F_Fab)]:
    field.SetText(value); field.SetPosition(vec(0,y)); field.SetLayer(layer)
    field.SetTextSize(vec(.6,.6)); field.SetTextThickness(p.FromMM(.1))
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LIB), fp)
print(LIB/(NAME+'.kicad_mod'))
