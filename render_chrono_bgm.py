#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""스피릿 시타델: 오버드라이브 — 자작 BGM 3곡 렌더러 (외부 음원·샘플 없음)

  audio/chrono-lobby.mp3   「성채의 새벽」  (로비 · 76 BPM · Am-F-C-G)
  audio/chrono-battle.mp3  「균열의 행진」  (일반 전투 · 128 BPM · Am-F-C-G)
  audio/chrono-boss.mp3    「심연의 왕좌」  (보스전 · 142 BPM · Dm-Bb-Gm-A)

모두 numpy 로 악기를 직접 합성하고, 리버브(오버랩-애드 컨볼루션)·마스터링을 거쳐
imageio_ffmpeg 의 ffmpeg 로 MP3(160k) 인코딩한다. 기존 audio/*.mp3 는 건드리지 않는다.

사용:  python3 render_chrono_bgm.py [lobby|battle|boss|all]
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(1128)

# ----------------------------------------------------------------------------
# 기본 DSP
# ----------------------------------------------------------------------------


def lowpass_fast(x, fc, order=2):
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n + 1)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    H = 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, N)[:n]


def bandpass_fast(x, lo, hi, order=2):
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n + 1)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    Hl = 1.0 / np.sqrt(1.0 + (lo / np.maximum(f, 1e-9)) ** (2 * order))
    Hh = 1.0 / np.sqrt(1.0 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * Hl * Hh, N)[:n]


def osc(freq, n, kind, phase0=0.0):
    t = np.arange(n) / SR
    ph = freq * t + phase0
    if kind == 'sine':
        return np.sin(2 * np.pi * ph)
    if kind == 'triangle':
        return 2 * np.abs(2 * (ph - np.floor(ph + 0.5))) - 1
    if kind == 'saw':
        return 2 * (ph - np.floor(ph + 0.5))
    return np.where((ph - np.floor(ph)) < 0.5, 1.0, -1.0)


def env_exp(n, attack, dur, vol, release=0.02):
    t = np.arange(n) / SR
    g = np.zeros(n)
    ai = min(n, max(1, int(attack * SR)))
    g[:ai] = np.linspace(0.0, vol, ai, endpoint=False)
    di = min(n, int(dur * SR))
    if di > ai:
        dt = np.maximum(t[ai:di] - attack, 0.0)
        tau = max((dur - attack) / np.log(max(vol / 0.002, 2.0)), 0.01)
        g[ai:di] = vol * np.exp(-dt / tau)
    if di < n:
        g[di:] = 0.0
    return g


def env_adsr(n, attack, decay_s, sustain, release_s, vol):
    """어택 → 디케이 → 서스테인 → 릴리즈 (릴리즈는 끝에서부터)"""
    t = np.arange(n) / SR
    g = np.full(n, vol * sustain)
    a = min(n, max(1, int(attack * SR)))
    g[:a] = np.linspace(0.0, vol, a, endpoint=False)
    d = max(1, int(decay_s * SR))
    if a < n:
        k = min(d, n - a)
        g[a:a + k] = vol * (1 - (1 - sustain) * (np.arange(k) / d))
    r = min(n, max(1, int(release_s * SR)))
    if r < n:
        g[n - r:] *= np.linspace(1.0, 0.0, r)
    return g


def place(buf, t0, sig, pan=0.0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), len(buf) - i0)
    if n <= 0:
        return
    l = np.cos((pan + 1) * np.pi / 4) * gain
    r = np.sin((pan + 1) * np.pi / 4) * gain
    buf[i0:i0 + n, 0] += sig[:n] * l
    buf[i0:i0 + n, 1] += sig[:n] * r


def note(name):
    """'A2', 'C#4', 'Bb1' → 주파수(Hz)"""
    base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    i = 1
    semi = base[name[0].upper()]
    if len(name) > 1 and name[1] in '#b':
        semi += 1 if name[1] == '#' else -1
        i = 2
    octave = int(name[i:])
    midi = 12 * (octave + 1) + semi
    return 440.0 * 2 ** ((midi - 69) / 12.0)


# ----------------------------------------------------------------------------
# 악기
# ----------------------------------------------------------------------------


def pad(freqs, dur, vol=0.10, bright=1600.0, attack=0.35):
    n = int((dur + 0.5) * SR)
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.004):
            ff = f * (1 + det)
            out += 0.5 * osc(ff, n, 'saw') + 0.5 * osc(ff, n, 'triangle')
    out /= max(1, len(freqs) * 2)
    t = np.arange(n) / SR
    lfo = 1 + 0.06 * np.sin(2 * np.pi * 0.7 * t)
    out = lowpass_fast(out * lfo, bright, 2)
    e = env_adsr(n, attack, dur * 0.35, 0.85, 0.45, vol)
    return out * e


def choir(freqs, dur, vol=0.09):
    n = int((dur + 0.4) * SR)
    out = np.zeros(n)
    for f in freqs:
        t = np.arange(n) / SR
        vib = 1 + 0.006 * np.sin(2 * np.pi * 4.2 * t + rng.uniform(0, 6))
        ph = np.cumsum(f * vib) / SR
        out += (np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph) + 0.18 * np.sin(6 * np.pi * ph))
    out /= max(1, len(freqs))
    breath = lowpass_fast(rng.uniform(-1, 1, n), 2400, 1) * 0.05
    out = lowpass_fast(out + breath, 2600, 2)
    return out * env_adsr(n, 0.6, dur * 0.4, 0.9, 0.6, vol)


def cello_bass(freq, dur=0.14, vol=0.22):
    n = int((dur + 0.06) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.002 * np.sin(2 * np.pi * 4.5 * t)
    ph = np.cumsum(freq * vib) / SR
    w = (1.00 * np.sin(2 * np.pi * ph)
         + 0.48 * np.sin(4 * np.pi * ph)
         + 0.22 * np.sin(6 * np.pi * ph)
         + 0.08 * osc(freq, n, 'saw'))
    w = lowpass_fast(w, 2000, 2)
    return w * env_exp(n, 0.010, dur, vol)


def violin_lead(freq, dur=0.13, vol=0.15):
    n = int((dur + 0.10) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    ph = np.cumsum(freq * vib) / SR
    w = (1.00 * np.sin(2 * np.pi * ph)
         + 0.42 * np.sin(4 * np.pi * ph)
         + 0.20 * np.sin(6 * np.pi * ph)
         + 0.10 * np.sin(8 * np.pi * ph)
         + 0.05 * osc(freq, n, 'saw'))
    w = lowpass_fast(w, 6000, 2)
    return w * env_adsr(n, 0.02, dur * 0.5, 0.75, 0.10, vol)


def bell(freq, dur=1.1, vol=0.10):
    n = int((dur + 0.2) * SR)
    t = np.arange(n) / SR
    w = (np.sin(2 * np.pi * freq * t) * np.exp(-t / (dur * 0.30))
         + 0.42 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t / (dur * 0.20))
         + 0.20 * np.sin(2 * np.pi * freq * 3.02 * t) * np.exp(-t / (dur * 0.13))
         + 0.09 * np.sin(2 * np.pi * freq * 4.05 * t) * np.exp(-t / (dur * 0.09)))
    return w * env_exp(n, 0.004, dur, vol)


def brass(freq, dur=0.35, vol=0.16):
    n = int((dur + 0.15) * SR)
    t = np.arange(n) / SR
    w = np.zeros(n)
    for det in (-0.006, 0.0, 0.006):
        f = freq * (1 + det)
        ph = np.cumsum(f * (1 + 0.002 * np.sin(2 * np.pi * 5 * t))) / SR
        w += 2 * (ph - np.floor(ph + 0.5))
    w /= 3
    w = lowpass_fast(w, 1800, 2)
    return w * env_adsr(n, 0.05, 0.10, 0.75, 0.18, vol)


def pluck(freq, dur=0.30, vol=0.12):
    n = int((dur + 0.05) * SR)
    t = np.arange(n) / SR
    w = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
         + 0.25 * np.sin(2 * np.pi * freq * 3 * t))
    w = lowpass_fast(w, 4200, 1)
    return w * env_exp(n, 0.004, dur, vol)


def drum_kick(vol=0.28):
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    f = 140 * np.power(38 / 140, np.minimum(t / 0.10, 1.0))
    ph = np.cumsum(f) / SR
    click = lowpass_fast(rng.uniform(-1, 1, n), 3000, 2) * np.exp(-t / 0.006)
    return (np.sin(2 * np.pi * ph) * np.exp(-t / 0.13) + 0.30 * click) * vol


def drum_tom(freq=110.0, vol=0.20):
    n = int(0.36 * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.5 * np.exp(-t / 0.03))
    ph = np.cumsum(f) / SR
    return np.sin(2 * np.pi * ph) * np.exp(-t / 0.16) * vol


def drum_snare(vol=0.16):
    n = int(0.24 * SR)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    body = bandpass_fast(x, 1200, 7500, 2)
    tone = np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.038)
    return (body * np.exp(-t / 0.070) + 0.45 * tone) * vol


def drum_hat(vol=0.045, open_=False):
    n = int((0.22 if open_ else 0.08) * SR)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    dec = 0.11 if open_ else 0.018
    return bandpass_fast(x, 6500, 15000, 2) * np.exp(-t / dec) * vol


def timpani(freq=73.4, vol=0.24):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    w = (np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.35)
         + 0.5 * np.sin(2 * np.pi * freq * 1.5 * t) * np.exp(-t / 0.22)
         + 0.25 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.15))
    thump = lowpass_fast(rng.uniform(-1, 1, n), 400, 1) * np.exp(-t / 0.05) * 0.3
    return (w + thump) * vol


def riser(dur=1.6, vol=0.10):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    sweep = bandpass_fast(x, 400, 9000, 2)
    e = np.linspace(0, 1, n) ** 2
    return lowpass_fast(sweep * e, 8000, 1) * vol


# ----------------------------------------------------------------------------
# 리버브 (오버랩-애드 FFT 컨볼루션 · 메모리 절약)
# ----------------------------------------------------------------------------


def convolve_ola(x, ir):
    n_ir = len(ir)
    block = 1 << 17
    N = 1 << int(np.ceil(np.log2(block + n_ir)))
    H = np.fft.rfft(ir, N)
    out = np.zeros(len(x) + N, dtype=np.float64)
    for start in range(0, len(x), block):
        seg = x[start:start + block]
        X = np.fft.rfft(seg, N)
        y = np.fft.irfft(X * H, N)
        out[start:start + N] += y
    return out[:len(x)]


def reverb(L, wet=0.18, dur=1.6, damp=4200, predelay=0.02):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = rng.uniform(-1, 1, n) * np.exp(-t / (dur * 0.25))
    ir = lowpass_fast(ir, damp, 2)
    ir *= 1.0 - np.exp(-t / 0.004)          # 프리딜레이 완만한 시작
    p = int(predelay * SR)
    ir = np.concatenate([np.zeros(p), ir])
    ir[0] += 1.0
    ir /= np.sqrt(np.sum(ir ** 2))
    out = np.zeros_like(L)
    for c in range(2):
        out[:, c] = convolve_ola(L[:, c], ir)
    return L * (1 - wet) + out * wet * 1.5


def master(L, target=0.95):
    for c in range(2):
        L[:, c] = L[:, c] - lowpass_fast(L[:, c], 32, 1) * 0.9
    # 살짝 넓히기 (미드/사이드)
    mid = (L[:, 0] + L[:, 1]) * 0.5
    side = (L[:, 0] - L[:, 1]) * 0.5 * 1.18
    L[:, 0] = mid + side
    L[:, 1] = mid - side
    peak = np.max(np.abs(L)) or 1.0
    L = L / peak * 1.2
    L = np.tanh(L * 1.05) * 0.94
    peak = np.max(np.abs(L)) or 1.0
    L = L / peak * target
    fade = int(0.04 * SR)
    L[:fade] *= np.linspace(0, 1, fade)[:, None]
    L[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return L


def fold_loop(L, loop_sec):
    """곡 끝의 여운(리버브 꼬리)을 처음으로 접어 넣어 반복 재생이 끊기지 않게 한다."""
    n = int(loop_sec * SR)
    if n <= 0 or n >= len(L):
        return L
    out = L[:n].copy()
    tail = L[n:]
    m = min(len(tail), n)
    out[:m] += tail[:m]
    return out


def master_loop(L, target=0.95):
    for c in range(2):
        L[:, c] = L[:, c] - lowpass_fast(L[:, c], 32, 1) * 0.9
    mid = (L[:, 0] + L[:, 1]) * 0.5
    side = (L[:, 0] - L[:, 1]) * 0.5 * 1.18
    L[:, 0] = mid + side
    L[:, 1] = mid - side
    peak = np.max(np.abs(L)) or 1.0
    L = L / peak * 1.2
    L = np.tanh(L * 1.05) * 0.94
    peak = np.max(np.abs(L)) or 1.0
    L = L / peak * target
    fade = int(0.02 * SR)          # 이음매 클릭 방지용 아주 짧은 페이드
    L[:fade] *= np.linspace(0, 1, fade)[:, None]
    L[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return L


def save_wav(path, L):
    pcm = (np.clip(L, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def to_mp3(wav, mp3):
    ff = subprocess.run([sys.executable, '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                        capture_output=True, text=True).stdout.strip()
    subprocess.run([ff, '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '160k',
                    '-ar', str(SR), mp3], capture_output=True, check=False)


# ----------------------------------------------------------------------------
# 1) 로비 — 「성채의 새벽」 76 BPM · Am - F - C - G
# ----------------------------------------------------------------------------

def build_lobby():
    bpm = 76.0
    beat = 60.0 / bpm
    step = beat / 4.0
    bars = 16
    total = bars * 4 * beat + 3.0
    L = np.zeros((int(total * SR), 2))

    chords = [
        ('A2', ['A3', 'C4', 'E4']),
        ('F2', ['F3', 'A3', 'C4']),
        ('C3', ['C4', 'E4', 'G4']),
        ('G2', ['G3', 'B3', 'D4']),
    ]
    # 벨 멜로디: (마디, 스텝, 음, 길이)
    melody = [
        (0, 0, 'E5', 1.2), (0, 6, 'C5', 1.0), (0, 10, 'A4', 1.6),
        (1, 0, 'C5', 1.0), (1, 4, 'A4', 0.9), (1, 8, 'F4', 1.8),
        (2, 2, 'G4', 1.1), (2, 6, 'E4', 1.0), (2, 10, 'C5', 1.4),
        (3, 0, 'D5', 1.2), (3, 6, 'B4', 1.0), (3, 10, 'G4', 1.8),
        (4, 0, 'A5', 1.4), (4, 6, 'E5', 1.1), (4, 10, 'C5', 1.4),
        (5, 0, 'A4', 1.0), (5, 4, 'C5', 1.0), (5, 8, 'F5', 1.6),
        (6, 2, 'E5', 1.2), (6, 6, 'C5', 1.0), (6, 10, 'G4', 1.4),
        (7, 0, 'D5', 1.4), (7, 6, 'G4', 1.0), (7, 10, 'B4', 1.6),
    ]
    arp_pattern = [0, 1, 2, 1]

    for b in range(bars):
        t_bar = b * 4 * beat
        root, triad = chords[b % 4]
        # 패드
        place(L, t_bar, pad([note(n) for n in triad], 3.6 * beat, vol=0.075, bright=1500), 0.0)
        # 베이스
        place(L, t_bar, cello_bass(note(root), 1.8, 0.17), -0.05)
        place(L, t_bar + 2 * beat, cello_bass(note(root) * 2, 1.2, 0.10), 0.05)
        # 아르페지오 (벨) - 8분
        for s in range(8):
            f = note(triad[arp_pattern[s % 4]]) * (2 if s >= 4 else 1)
            v = 0.055 if s % 2 == 0 else 0.035
            place(L, t_bar + s * 2 * step, bell(f, 0.9, v), 0.22 if s % 2 else -0.18)
        # 멜로디 (2회 반복 구간에서 한 번 더)
        for rep in (0, 8):
            for (mb, ms, nm, ln) in melody:
                if mb + rep >= bars:
                    continue
                tt = (mb + rep) * 4 * beat + ms * step
                place(L, tt, bell(note(nm), max(0.9, ln * beat), 0.085), 0.1)
                place(L, tt, violin_lead(note(nm) / 2, ln * beat * 0.8, 0.030), -0.14)
        # 드럼(가벼운 하트/톰)
        if b >= 4:
            for s in (2, 6, 10, 14):
                place(L, t_bar + s * step, drum_hat(0.026), 0.3)
            place(L, t_bar, drum_tom(note(root) * 2, 0.06), -0.2)
    # 마지막 마디 마무리
    place(L, (bars - 1) * 4 * beat, timpani(note('A1'), 0.16), 0.0)
    return L, bars * 4 * beat


# ----------------------------------------------------------------------------
# 2) 전투 — 「균열의 행진」 128 BPM · Am - F - C - G
# ----------------------------------------------------------------------------

def build_battle():
    bpm = 128.0
    beat = 60.0 / bpm
    step = beat / 4.0
    bars = 40
    total = bars * 4 * beat + 2.0
    L = np.zeros((int(total * SR), 2))

    chords = [
        ('A2', ['A3', 'C4', 'E4']),
        ('F2', ['F3', 'A3', 'C4']),
        ('C3', ['C4', 'E4', 'G4']),
        ('G2', ['G3', 'B3', 'D4']),
    ]
    hook = [0, 7, 12, 7, 10, 7, 5, 3, 0, 5, 7, 10, 12, 10, 7, 5]
    hook2 = [12, 10, 7, 10, 12, 15, 14, 12, 10, 7, 5, 7, 10, 12, 7, 0]
    ostinato = [0, 0, 12, 0, 7, 0, 12, 3, 0, 0, 12, 0, 15, 12, 7, 0]

    for b in range(bars):
        t_bar = b * 4 * beat
        root, triad = chords[b % 4]
        r = note(root)
        intro = b < 4
        breakdown = 16 <= b < 20
        # 패드(얇게) + 브라스 스타브
        if not breakdown:
            place(L, t_bar, pad([note(n) for n in triad], 3.9 * beat, vol=0.05, bright=2100, attack=0.08), 0.0)
        if b % 4 == 0:
            place(L, t_bar, brass(note(triad[0]) / 2, 0.5, 0.10), -0.1)
            place(L, t_bar + 1.5 * beat, brass(note(triad[2]), 0.3, 0.055), 0.15)
        # 베이스 오스티나토 (16분)
        for s in range(16):
            sem = ostinato[s]
            f = r * (2 ** (sem / 12.0))
            v = 0.19 if s % 4 == 0 else 0.12
            place(L, t_bar + s * step, cello_bass(f, 0.10, v), -0.03)
        # 드럼
        if not intro:
            for s in (0, 6, 8, 14):
                place(L, t_bar + s * step, drum_kick(0.30), 0.0)
            for s in (4, 12):
                place(L, t_bar + s * step, drum_snare(0.15), 0.04)
            if not breakdown:
                for s in range(0, 16, 2):
                    place(L, t_bar + s * step, drum_hat(0.030 if s % 4 else 0.042), 0.28)
                for s in (7, 15):
                    place(L, t_bar + s * step, drum_hat(0.024, True), -0.25)
        # 리드 멜로디
        if b >= 4 and not breakdown:
            for s in range(16):
                if s % 2 == 0:
                    deg = (hook if (b // 4) % 2 == 0 else hook2)[s]
                    f = r * 4 * (2 ** (deg / 12.0))
                    place(L, t_bar + s * step, violin_lead(f, 0.22, 0.085), 0.07)
        # 후렴 강조
        if b % 8 == 7:
            place(L, t_bar + 12 * step, drum_tom(note('A2'), 0.16), -0.2)
            place(L, t_bar + 14 * step, drum_tom(note('E2'), 0.16), 0.2)
        if b == 15:
            place(L, t_bar + 3 * beat, riser(1.2, 0.08), 0.0)
    place(L, bars * 4 * beat - 1.2, timpani(note('A1'), 0.20), 0.0)
    return L, bars * 4 * beat


# ----------------------------------------------------------------------------
# 3) 보스 — 「심연의 왕좌」 142 BPM · Dm - Bb - Gm - A
# ----------------------------------------------------------------------------

def build_boss():
    bpm = 142.0
    beat = 60.0 / bpm
    step = beat / 4.0
    bars = 36
    total = bars * 4 * beat + 2.5
    L = np.zeros((int(total * SR), 2))

    # Dm, Bb, Gm, A(장) — 긴장과 해소
    chords = [
        ('D2', ['D3', 'F3', 'A3'], ['D4', 'F4', 'A4']),
        ('Bb1', ['Bb2', 'D3', 'F3'], ['Bb3', 'D4', 'F4']),
        ('G1', ['G2', 'Bb2', 'D3'], ['G3', 'Bb3', 'D4']),
        ('A1', ['A2', 'C#3', 'E3'], ['A3', 'C#4', 'E4']),
    ]
    ostinato = [0, 12, 0, 1, 0, 12, 0, 6, 0, 12, 0, 1, 7, 6, 12, 1]
    motif = [0, 0, 3, 0, 5, 3, 0, -2, 0, 0, 3, 5, 7, 5, 3, 0]

    for b in range(bars):
        t_bar = b * 4 * beat
        root, low, high = chords[b % 4]
        r = note(root)
        intro = b < 2
        # 저음 현 + 브라스 + 합창
        place(L, t_bar, cello_bass(r / 2, 4 * beat, 0.13), 0.0)
        if not intro:
            place(L, t_bar, pad([note(n) for n in high], 3.9 * beat, vol=0.055, bright=1400, attack=0.25), 0.0)
            place(L, t_bar, choir([note(low[0]) * 2, note(low[2]) * 2], 3.6 * beat, 0.045), 0.0)
        if b % 2 == 0:
            place(L, t_bar, brass(note(low[0]), 0.45, 0.13), -0.12)
            place(L, t_bar + 2 * beat, brass(note(low[2]), 0.35, 0.085), 0.12)
        # 16분 오스티나토 (불안)
        for s in range(16):
            f = r * (2 ** (ostinato[s] / 12.0))
            v = 0.15 if s % 4 == 0 else 0.085
            place(L, t_bar + s * step, cello_bass(f, 0.085, v), -0.05)
        # 모티프 (트라이톤 강조)
        if b >= 4:
            for s in range(0, 16, 2):
                deg = motif[s]
                f = note(high[0]) * (2 ** (deg / 12.0))
                place(L, t_bar + s * step, brass(f, 0.20, 0.065), 0.09)
        # 드럼 (팀파니 + 킥 + 스네어)
        if not intro:
            place(L, t_bar, timpani(r, 0.30), 0.0)
            place(L, t_bar + 2 * beat, timpani(r * 1.5, 0.16), -0.15)
            for s in (0, 3, 8, 11):
                place(L, t_bar + s * step, drum_kick(0.30), 0.0)
            for s in (4, 12):
                place(L, t_bar + s * step, drum_snare(0.17), 0.05)
            for s in range(0, 16, 2):
                place(L, t_bar + s * step, drum_hat(0.028 if s % 4 else 0.040), 0.26)
            for s in (7, 15):
                place(L, t_bar + s * step, drum_tom(note('D2'), 0.10), -0.24)
        if b == 19:
            place(L, t_bar + 2 * beat, riser(2.0, 0.09), 0.0)
    place(L, bars * 4 * beat - 1.4, timpani(note('D1'), 0.26), 0.0)
    place(L, bars * 4 * beat - 0.7, brass(note('D2'), 0.7, 0.16), 0.0)
    return L, bars * 4 * beat


# ----------------------------------------------------------------------------

TRACKS = {
    'lobby': ('build_lobby', 'audio/chrono-lobby.mp3', 0.22, 1.9, 3800),
    'battle': ('build_battle', 'audio/chrono-battle.mp3', 0.16, 1.4, 4600),
    'boss': ('build_boss', 'audio/chrono-boss.mp3', 0.19, 1.8, 4200),
}


def render(which):
    fn_name, out_mp3, wet, rv_dur, damp = TRACKS[which]
    L, loop_sec = globals()[fn_name]()
    L = reverb(L, wet=wet, dur=rv_dur, damp=damp)
    L = fold_loop(L, loop_sec)
    L = master_loop(L)
    os.makedirs('audio', exist_ok=True)
    os.makedirs('work_tmp/audio', exist_ok=True)
    wav = 'work_tmp/audio/chrono-%s.wav' % which
    save_wav(wav, L)
    to_mp3(wav, out_mp3)
    dur = L.shape[0] / SR
    peak = float(np.max(np.abs(L)))
    rms = float(np.sqrt(np.mean(L ** 2)))
    size = os.path.getsize(out_mp3) // 1024
    print('%s  %5.1fs  peak %.2f  rms %.3f  %4dKB' % (out_mp3, dur, peak, rms, size))


if __name__ == '__main__':
    args = sys.argv[1:] or ['all']
    picks = ['lobby', 'battle', 'boss'] if args == ['all'] else args
    for w in picks:
        render(w)
