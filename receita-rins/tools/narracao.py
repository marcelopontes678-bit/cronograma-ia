"""Narração pt-BR com Kokoro (voz pm_alex): uma faixa por cena + narracao.wav completa + tempos.json.
Rodar: /home/user/openmontage-work/OpenMontage/.venv/bin/python -I tools/narracao.py (da pasta receita-rins)
"""
import json
import os

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = "/home/user/openmontage-work/models"
VOICE, SPEED, GAP = "pm_alex", 1.08, 0.35

# (id, texto falado) — números por extenso para a voz; o texto das legendas fica no ROTEIRO.md
CENAS = [
    ("1-gancho", "Existe uma receita natural para os rins que os urologistas levam a sério. E ela cabe numa garrafa de água."),
    ("2-alerta", "Mas atenção: ela não trata uma crise. Dor forte nas costas com febre, sangue na urina ou vômito é motivo para procurar atendimento hoje."),
    ("3-receita", "A receita é água com limão. Esprema dois limões, mais ou menos meia xícara de suco, em dois litros de água. Sem açúcar."),
    ("4-como", "Beba aos poucos ao longo do dia, junto com a sua água de sempre. O objetivo, segundo os especialistas, é urinar pelo menos dois litros por dia."),
    ("5-porque", "Beber mais água deixa a urina mais diluída, e é a medida com mais evidência para prevenir pedras nos rins. O limão traz uma substância chamada citrato, que pode ajudar. Mas os estudos ainda são mistos."),
    ("6-cuidados", "Se você tem doença nos rins, problema no coração ou restrição de líquidos, fale com o seu médico antes. E use canudo, para proteger os dentes do ácido."),
    ("7-cta", "Salve este vídeo e mande para quem vive esquecendo de beber água."),
]

k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
parts, tempos, t, sr0 = [], [], 0.0, None
for cid, txt in CENAS:
    a, sr = k.create(txt, voice=VOICE, speed=SPEED, lang="pt-br")
    sr0 = sr
    # corta silêncio das pontas
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - int(.03 * sr), 0): idx[-1] + int(.08 * sr)]
    sf.write(os.path.join(HERE, "audio", cid + ".wav"), a, sr)
    tempos.append({"id": cid, "inicio": round(t, 3), "fim": round(t + len(a) / sr, 3), "texto": txt})
    parts += [a, np.zeros(int(GAP * sr), np.float32)]
    t += len(a) / sr + GAP
full = np.concatenate(parts)
full = full / max(np.abs(full).max(), 1e-6) * 0.89
sf.write(os.path.join(HERE, "audio", "narracao.wav"), full, sr0)
json.dump(tempos, open(os.path.join(HERE, "audio", "tempos.json"), "w"), ensure_ascii=False, indent=1)
print("duração total %.2f s" % (len(full) / sr0))
for x in tempos:
    print(x["id"], x["inicio"], x["fim"])
