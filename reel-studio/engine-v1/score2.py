"""An original score and sound effects for the reel, synthesised from scratch (no samples, no licences).
Usage: python3 score.py <full|guest> <out.wav>. Beat lengths mirror reel.html's FULL list."""
import sys, wave
import numpy as np

SR = 48000
BEATS = [("hook", 4.2), ("scan", 5.2), ("lang", 3.8), ("cart", 6.0), ("hani", 4.2), ("pay", 5.2), ("wok", 4.8),
         ("ready", 5.0), ("call", 4.6), ("phone", 5.0), ("owner", 5.4), ("end", 4.6)]
import json, soundfile as sf
story, R, outp = sys.argv[1], sys.argv[2], sys.argv[3]
PADS = {"dinein": [("hook",1.3),("turn",.9),("ask",1.5),("eta",1.2),("more",1.3),("call",1.3),("end",1.6)],
        "pickup": [("hook",1.0),("turn",.9),("list",1.3),("tap",1.5),("team",1.5),("end",1.5)]}[story]
VOD = dict(json.load(open(R + "/vo_dur.json"))[story])
T0, VO, acc = {}, {}, 0.0
for k, pad in PADS:
    T0[k] = acc; VO[k] = acc + .25; acc += VOD[k] + pad + .25
DUR = acc + 0.3
N = int(DUR * SR); t = np.arange(N) / SR; mix = np.zeros(N); rng = np.random.default_rng(7)
def place(sig, at, gain=1.0):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(sig)); mix[i:j] += sig[: max(0, j - i)] * gain


def env(n, a=0.005, r=0.3, sus=None):
    x = np.arange(n) / SR
    e = np.minimum(1, x / max(a, 1e-4)) * np.exp(-x / r)
    return e


def note(f, dur, kind="sine", a=0.01, r=0.4, det=0.0):
    n = int(dur * SR); x = np.arange(n) / SR
    if kind == "saw":
        s = sum(((x * f * (1 + d)) % 1 * 2 - 1) for d in (-det, 0, det)) / 3
    elif kind == "pluck":
        s = np.sin(2*np.pi*f*x) * 0.7 + 0.3*np.sin(2*np.pi*2*f*x) * np.exp(-x*8)
    else:
        s = np.sin(2*np.pi*f*x)
    return s * env(n, a, r)


def lowpass(s, cut):
    a = np.exp(-2*np.pi*cut/SR); y = np.zeros_like(s); acc_ = 0.0
    for i in range(len(s)):
        acc_ = (1-a)*s[i] + a*acc_; y[i] = acc_
    return y


def noise(dur):
    return rng.standard_normal(int(dur*SR))


def mtof(m): return 440 * 2 ** ((m - 69) / 12)



# ---- voice: Kokoro af_heart, one file per beat ----
voice = np.zeros(N)
for k, _ in PADS:
    a, sr = sf.read(f"{R}/vo/{story}_{k}.wav"); a = np.interp(np.arange(int(len(a)*SR/sr))*sr/SR, np.arange(len(a)), a)
    i = int(VO[k]*SR); j = min(N, i+len(a)); voice[i:j] += a[:max(0, j-i)]
# ---- music: 104 bpm, the same warm D major loop, ducked under the voice ----
BPM = 104; beat = 60 / BPM; bar = 4 * beat
CHORDS = [[50, 54, 57, 61], [47, 50, 54, 57], [43, 47, 50, 54], [45, 49, 52, 59]]
music = np.zeros(N); pad_src = np.zeros(N)
for b in range(int(DUR / bar) + 1):
    ch = CHORDS[b % 4]; at = b * bar
    for m in ch:
        s_ = note(mtof(m + 12), bar + 0.4, "saw", a=0.3, r=2.0, det=0.004) * 0.05
        i = int(at*SR); j = min(N, i+len(s_)); pad_src[i:j] += s_[:max(0, j-i)]
    bs = note(mtof(ch[0] - 12), bar * .9, "sine", a=0.01, r=0.9) * 0.22
    i = int(at*SR); j = min(N, i+len(bs)); music[i:j] += bs[:max(0, j-i)]
    for kk, m in enumerate([ch[0]+24, ch[1]+24, ch[2]+24, ch[3]+24, ch[2]+24, ch[1]+24, ch[3]+24, ch[2]+24]):
        s_ = note(mtof(m), 0.45, "pluck", a=0.002, r=0.22) * 0.06
        i = int((at + kk*beat/2)*SR); j = min(N, i+len(s_)); music[i:j] += s_[:max(0, j-i)]
    for kk in range(4):
        if kk % 2 == 0:
            n = int(0.25*SR); x = np.arange(n)/SR; kick = np.sin(2*np.pi*(55 + 70*np.exp(-x*30))*x) * np.exp(-x*14) * 0.35
            i = int((at + kk*beat)*SR); j = min(N, i+n); music[i:j] += kick[:max(0, j-i)]
        sh = noise(0.06) * env(int(0.06*SR), 0.001, 0.02) * 0.03
        i = int((at + kk*beat + beat/2)*SR); j = min(N, i+len(sh)); music[i:j] += sh[:max(0, j-i)]
music += lowpass(pad_src, 1800)
vabs = np.convolve(np.abs(voice), np.ones(int(.25*SR))/int(.25*SR), mode="same")
duck = 1 - 0.62 * np.clip(vabs / (np.max(vabs) * .25 + 1e-9), 0, 1)
duck = np.convolve(duck, np.ones(int(.15*SR))/int(.15*SR), mode="same")
mus_env = np.clip(t / .6, 0, 1) * np.where(t > DUR - 1.2, np.clip((DUR - t) / 1.2, 0, 1), 1)
mix += music * mus_env * duck * 0.85
# ---- effects ----
def pop(at, g=0.5):
    n = int(0.09*SR); x = np.arange(n)/SR; place(np.sin(2*np.pi*(900 - 500*x/0.09)*x) * np.exp(-x*45), at, g)
def chime(at, notes=(86, 90, 93, 98), g=0.22, gap=0.06):
    for k, m in enumerate(notes): place(note(mtof(m), 1.0, "sine", a=0.002, r=0.35) + 0.3*note(mtof(m+12), 1.0, "sine", a=0.002, r=0.2), at + k*gap, g)
def whoosh(at, g=0.18, dur=0.5):
    s = noise(dur); x = np.arange(len(s))/SR; e = np.sin(np.pi * x / dur) ** 2
    place(lowpass(s, 2500) * e, at - 0.1, g)
def sizzle(a, b, g=0.10):
    s = lowpass(noise(b - a), 6000) - lowpass(noise(b - a), 900); x = np.arange(len(s))/SR
    e = np.clip(x/0.3, 0, 1) * np.clip((b - a - x)/0.6, 0, 1) * (0.8 + 0.2*np.sin(2*np.pi*3*x)); place(s * e, a, g)
def ring(at, times=2, g=0.18):
    for k in range(times):
        n = int(0.8*SR); x = np.arange(n)/SR; tr = (np.sin(2*np.pi*20*x) > 0)
        s = (np.sin(2*np.pi*660*x) + np.sin(2*np.pi*880*x)) * 0.5 * tr * np.clip((0.8-x)/0.05, 0, 1)
        place(s, at + k*1.0, g)
def printer(at, dur=1.1, g=0.08):
    n = int(dur*SR); x = np.arange(n)/SR; s = np.sign(np.sin(2*np.pi*95*x)) * (0.5 + 0.5*np.sin(2*np.pi*12*x)) ; place(lowpass(s, 1200) * np.clip((dur-x)/0.1, 0, 1), at, g)
def bell(at, g=0.2):
    for k in range(3): place(note(1320, 0.5, "sine", a=0.001, r=0.25) + 0.5*note(1980, 0.5, "sine", a=0.001, r=0.15), at + k*0.18, g)


def ticks(a, b, g=0.10):
    k = a
    while k < b: place(note(2200, .04, "sine", a=0.0005, r=0.01), k, g); k += 0.5
def steps(a, b, g=0.10):
    k = a
    while k < b: place(lowpass(noise(.07), 700) * env(int(.07*SR), .001, .03), k, g); k += 0.32
if story == "dinein":
    hk, tu, as_, et, mo, cl, en = (T0[k] for k in ("hook","turn","ask","eta","more","call","end"))
    ticks(hk + .4, tu); [pop(hk + x, .35) for x in (.2, .9, 1.6, 2.3)]
    whoosh(tu, .25, .5); chime(tu + .05, (86, 93), .2, .06); whoosh(tu + .5, .2, .6)
    pop(as_ + .2); pop(VO["ask"] + .2, .3); chime(VO["ask"] + 1.3, (90, 95), .14)
    whoosh(et + .1, .18); pop(VO["more"] + .9); chime(VO["more"] + 1.5, (93, 98, 102), .18, .06)
    whoosh(cl + .1, .16); pop(VO["call"] + .3); bell(VO["call"] + .5, .12); steps(VO["call"] + .9, VO["call"] + 2.2)
    chime(VO["call"] + 2.0, (88, 93), .16); chime(cl + VOD["call"] + 1.3 + .25 - .6, (86, 90, 93, 98), .2, .07)
    chime(en + .4, (74, 78, 81, 86, 90), .2, .09)
else:
    hk, tu, li, tp, te, en = (T0[k] for k in ("hook","turn","list","tap","team","end"))
    bell(hk + .05, .10); steps(hk + .1, hk + 1.6); ticks(hk + 2.4, tu); pop(hk + 1.8, .35)
    whoosh(tu, .25, .5); chime(tu + .05, (86, 93), .2, .06); whoosh(li - .5, .2, .6)
    pop(li + 1.0); whoosh(li + VOD["list"] + 1.3 + .25 - .5, .14, .4); pop(tp + .7); chime(tp + 1.2, (86, 90, 93, 98), .22, .07)
    bell(te + .15, .16); bell(te + .9, .1); steps(VO["team"] + .4, VO["team"] + 2.4); chime(VO["team"] + 2.4, (90, 95, 98), .18, .07)
    chime(en + .4, (74, 78, 81, 86, 90), .2, .09)
mix = mix + voice * 1.0
mix = np.tanh(mix * 1.3) / np.tanh(1.3); mix *= 0.89 / max(1e-6, np.max(np.abs(mix)))
st = np.stack([mix, mix], 1)
with wave.open(outp, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype("<i2").tobytes())
print(outp, round(DUR, 2), {k: round(v, 2) for k, v in T0.items()})
