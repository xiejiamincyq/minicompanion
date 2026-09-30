"""Candidate selection calculations, not a netlist or hardware acceptance test."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
hlo,hhi=3.137544,3.222584
module_lo,module_hi=3.18945,3.41055 # conditional 25C envelope from 018
# TCA9517A both supplies fed from switched host rail; B connected to host.
# EN internal pullup cannot be ignored. Leakage below is a test-bias envelope.
r8hi,r5lo=2200*1.01,22000*.99
en_hi=(.8*hlo/r8hi-1.5e-6)/(1/r8hi+1/r5lo)
en_float=(30e-6+.5e-6+.05e-6)*22000*1.01
sink=hhi/(2200*.99)
margins={'host_receive_low':.25*hlo-.6,
 'module_receive_low':.2*module_lo-.2,
 'module_to_A_high':module_lo-11e-6*(2200*1.01)-.7*hhi,
 'EN_high':en_hi-.7*hlo,'EN_float_low_at_2V7':.3*2.7-en_float}
assert min(margins.values())>0 and sink<.002
# Comparison scenarios, NOT qualified currents at this actual voltage/bias.
# Always-on 6mA allowance: 5mA VCCB plus 1mA VCCA from datasheet test rows.
hours=48;awake=2*20/60
buffer_battery_mA=3.18*6/(3.7*.85)
always=buffer_battery_mA*hours;gated=buffer_battery_mA*awake
assert gated<always/50
report={'status':'selection_math_only_no_CAD_change',
 'selected_for_next_CAD':'TCA9517ADGKR plus TPS22919DCKR switched supply',
 'conditional_margins_V':margins,'conditional_EN_float_V':en_float,
 'supervisor_sink_mA':sink*1000,
 '6mA_budget_battery_mAh_48h_always_on':always,
 '6mA_budget_battery_mAh_40min_on':gated,
 'assumptions':['Buffer 6mA is a planning allowance from differing datasheet conditions, not a guaranteed 3.18V maximum',
 '3.18V, 3.7V battery, 85 percent converter efficiency, 40 minutes active over 48h',
 'Power switch losses, pullup currents, leakage and NFC itself excluded from this incremental comparison',
 'EN leakage and host GPIO output specifications require operating-point confirmation',
 'Both buffer supply pins use a gated host rail; module pullups remain on its own internal rail'],
 'source_sha256':{name:hashlib.sha256((H/name).read_bytes()).hexdigest() for name in ['tca9517a.pdf','tps22919.pdf']}}
(H/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
