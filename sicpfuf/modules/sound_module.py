"""
sicpfuf/modules/sound_module.py —  from sound import make_sound, play, sine_sound, ...

A WAVE IS A FUNCTION. It takes a time t in seconds and returns how far the
loudspeaker is pushed out at that moment, a number between -1 and 1:

    def a440(t):
        return math_sin(2 * math_pi * 440 * t)       # 440 swings per second: the note A

    play(make_sound(a440, 1.5))                      # a SOUND = a wave + a duration in seconds

A computer plays it by asking the wave for its value 44100 times per second
(SAMPLING), exactly as draw_connected asks a curve for its points.

    sine_sound(freq, duration)    square_sound, triangle_sound, sawtooth_sound, noise_sound, silence_sound
    consecutively(llist(s1, s2))  one after the other      simultaneously(llist(s1, s2))  at the same time
    adsr(attack, decay, sustain, release)(sound)           shape the loudness over time (an "envelope")
    piano(note, duration), violin, cello, trombone, bell   note = MIDI number (60 is middle C)

play(sound) prints a small picture of the wave. With  --out FOLDER  it also
writes a WAV file that any music player can open.
"""

import math
import random
import struct
import wave as wav_file

from ..errors import SicpError
from ..values import Closure, Builtin, type_name, a
from .rune_module import save_figure

NAMES = (
    "make_sound", "get_wave", "get_duration", "is_sound", "play", "play_in_tab", "play_wave", "stop",
    "noise_sound", "silence_sound", "sine_sound", "square_sound", "triangle_sound", "sawtooth_sound",
    "consecutively", "simultaneously", "adsr", "stacking_adsr", "phase_mod",
    "bell", "cello", "piano", "trombone", "violin",
    "midi_note_to_frequency", "letter_name_to_midi_note", "letter_name_to_frequency",
)

RATE = 44100                    # samples per second
LEVEL = 5                       # how many terms of the Fourier series for square / triangle / sawtooth
MAX_SECONDS = 60


class Sound:
    __slots__ = ("wave", "duration")

    def __init__(self, wave, duration):
        self.wave = wave        # a Python function: time → number, 0 after `duration`
        self.duration = duration

    def __repr__(self):
        return "<Sound>"


def to_wav_bytes(samples):
    import io
    buffer = io.BytesIO()
    with wav_file.open(buffer, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    return buffer.getvalue()


def picture(sound, width=64, height=9):
    """A text picture of the first few swings of the wave."""
    span = min(sound.duration, 0.02) or 0.02
    values = [max(-1.0, min(1.0, sound.wave(span * i / width))) for i in range(width)]
    rows = [[" "] * width for _ in range(height)]
    for col, v in enumerate(values):
        rows[int(round((1 - v) / 2 * (height - 1)))][col] = "█"
    middle = height // 2
    for col in range(width):
        if rows[middle][col] == " ":
            rows[middle][col] = "·"
    return "\n".join("│" + "".join(r) + "│" for r in rows)


NOTE_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def make(interp):
    from ..lib import builtin

    def number(fname, x, pname):
        if type(x) is not int and type(x) is not float:
            raise SicpError("TypeError", f"{fname} expects a number as {pname}, but got {a(type_name(x))}")
        return x

    def sound(fname, s):
        if type(s) is not Sound:
            raise SicpError("TypeError", f"{fname} expects a sound, but got {a(type_name(s))}")
        return s

    def as_python_wave(fname, w):
        if type(w) is not Closure and type(w) is not Builtin:
            raise SicpError("TypeError", f"{fname} expects a wave (a function from time to a number), "
                            f"but got {a(type_name(w))}")

        def call(t):
            v = interp.apply(w, [t])
            if type(v) is not int and type(v) is not float:
                raise SicpError("TypeError", f"a wave must return a number, but this one returned {a(type_name(v))}")
            return v
        return call

    def new_sound(fn, duration):
        return Sound(lambda t: 0 if t >= duration or t < 0 else fn(t), duration)

    def items(fname, xs):
        """The sounds of a linked list (or, from §3, of a list)."""
        out, node = [], xs
        while type(node) is list and len(node) == 2 and type(node[0]) is Sound and \
                (node[1] is None or (type(node[1]) is list and len(node[1]) == 2)):
            out.append(node[0])                     # a linked list: sound, then the rest
            node = node[1]
        if node is not None:
            if type(xs) is not list:
                raise SicpError("TypeError", f"{fname} expects a linked list of sounds, "
                                f"but got {a(type_name(xs))}")
            out = list(xs)                          # a Python list of sounds (from §3)
        for s in out:
            sound(fname, s)
        return out

    # ------------------------------------------------------------ making and reading sounds
    def make_sound(w, duration):
        number("make_sound", duration, "duration")
        if duration < 0:
            raise SicpError("ValueError", "make_sound: the duration must not be negative")
        return new_sound(as_python_wave("make_sound", w), duration)

    def get_wave(s):
        fn = sound("get_wave", s).wave
        return builtin("wave", lambda t: fn(number("wave", t, "t")), 1)

    def play(interp_, node, s):
        sound("play", s)
        if s.duration > MAX_SECONDS:
            raise SicpError("ValueError", f"play: this sound is {s.duration} seconds long; "
                            f"sicpfuf plays at most {MAX_SECONDS} seconds")
        interp_.write(f"[sound: {s.duration} s]\n{picture(s)}\n")
        if getattr(interp_, "out_dir", None):
            samples = [s.wave(i / RATE) for i in range(int(math.ceil(RATE * s.duration)))]
            path = save_figure(interp_, "sound", "wav", to_wav_bytes(samples), binary=True)
            if not getattr(interp_, "out_stem", None):
                interp_.write(f"[saved {path}]\n")
        return s

    def play_wave(interp_, node, w, duration):
        return play(interp_, node, make_sound(w, duration))

    # ------------------------------------------------------------ ready-made waves
    def sine(freq):
        return lambda t: math.sin(2 * math.pi * t * freq)

    def square(freq):
        return lambda t: (4 / math.pi) * sum(math.sin(2 * math.pi * (2 * i - 1) * freq * t) / (2 * i - 1)
                                              for i in range(1, LEVEL + 1))

    def triangle(freq):
        return lambda t: (8 / math.pi / math.pi) * sum((-1) ** i * math.sin((2 * i + 1) * t * freq * math.pi * 2)
                                                       / (2 * i + 1) ** 2 for i in range(LEVEL))

    def sawtooth(freq):
        return lambda t: 1 / 2 - (1 / math.pi) * sum(math.sin(2 * math.pi * i * freq * t) / i
                                                      for i in range(1, LEVEL + 1))

    def producer(name, shape):
        def produce(freq, duration):
            number(name, freq, "freq")
            number(name, duration, "duration")
            return new_sound(shape(freq), duration)
        return produce

    sine_sound, square_sound = producer("sine_sound", sine), producer("square_sound", square)
    triangle_sound, sawtooth_sound = producer("triangle_sound", triangle), producer("sawtooth_sound", sawtooth)

    def noise_sound(duration):
        return new_sound(lambda t: random.random() * 2 - 1, number("noise_sound", duration, "duration"))

    def silence_sound(duration):
        return new_sound(lambda t: 0, number("silence_sound", duration, "duration"))

    # ------------------------------------------------------------ combining sounds
    def consecutively(xs):
        sounds = items("consecutively", xs)
        starts, total = [], 0
        for s in sounds:
            starts.append(total)
            total += s.duration

        def fn(t):
            for s, start in zip(sounds, starts):
                if start <= t < start + s.duration:
                    return s.wave(t - start)
            return 0
        return new_sound(fn, total)

    def simultaneously(xs):
        sounds = items("simultaneously", xs)
        if not sounds:
            return new_sound(lambda t: 0, 0)
        n = len(sounds)
        return new_sound(lambda t: sum(s.wave(t) for s in sounds) / n, max(s.duration for s in sounds))

    def adsr_transform(attack_ratio, decay_ratio, sustain_level, release_ratio):
        def transform(s):
            sound("adsr", s)
            d = s.duration
            attack, decay, release = d * attack_ratio, d * decay_ratio, d * release_ratio

            def fn(t):
                v = s.wave(t)
                if t < attack:
                    return v * (t / attack)
                if t < attack + decay:
                    return v * ((1 - sustain_level) * math.exp(-5 * (t - attack) / decay) + sustain_level) \
                        if decay else v * sustain_level
                if t < d - release:
                    return v * sustain_level
                return v * sustain_level * math.exp(-5 * (t - (d - release)) / release) if release else 0
            return new_sound(fn, d)
        return transform

    def adsr(attack_ratio, decay_ratio, sustain_level, release_ratio):
        for v, n in ((attack_ratio, "attack_ratio"), (decay_ratio, "decay_ratio"),
                     (sustain_level, "sustain_level"), (release_ratio, "release_ratio")):
            number("adsr", v, n)
        return builtin("envelope", adsr_transform(attack_ratio, decay_ratio, sustain_level, release_ratio), 1)

    def stack_envelopes(waveform, base_frequency, duration, envelopes):
        harmonics = [envelope(waveform(base_frequency * (i + 1), duration)) for i, envelope in enumerate(envelopes)]
        n = len(harmonics)
        return new_sound(lambda t: sum(h.wave(t) for h in harmonics) / n, duration)

    def stacking_adsr(waveform, base_frequency, duration, envelopes):
        number("stacking_adsr", base_frequency, "base_frequency")
        number("stacking_adsr", duration, "duration")
        chain, node = [], envelopes
        while type(node) is list and len(node) == 2:
            chain.append(node[0])
            node = node[1]
        return stack_envelopes(lambda f, d: sound("stacking_adsr", interp.apply(waveform, [f, d])),
                               base_frequency, duration,
                               [lambda s, e=e: sound("stacking_adsr", interp.apply(e, [s])) for e in chain])

    def phase_mod(freq, duration, amount):
        for v, n in ((freq, "freq"), (duration, "duration"), (amount, "amount")):
            number("phase_mod", v, n)

        def transform(modulator):
            sound("phase_mod", modulator)
            return new_sound(lambda t: math.sin(2 * math.pi * t * freq + amount * modulator.wave(t)), duration)
        return builtin("phase_mod", transform, 1)

    # ------------------------------------------------------------ notes and instruments
    def midi_note_to_frequency(note):
        return 440 * 2 ** ((number("midi_note_to_frequency", note, "note") - 69) / 12)

    def letter_name_to_midi_note(name):
        text = name if type(name) is str else ""
        if not text or text[0].upper() not in NOTE_OFFSETS:
            raise SicpError("ValueError", f"letter_name_to_midi_note: {name!r} is not a note name like 'A4' or 'C#5'")
        note, rest = NOTE_OFFSETS[text[0].upper()], text[1:]
        while rest[:1] in ("#", "b"):
            note += 1 if rest[0] == "#" else -1
            rest = rest[1:]
        octave = int(rest) if rest.lstrip("-").isdigit() else 4
        return 12 * (octave + 1) + note

    def instrument(name, shape, envelopes):
        def make_note(note, duration):
            number(name, note, "note")
            number(name, duration, "duration")
            return stack_envelopes(producer(name, shape), midi_note_to_frequency(note), duration,
                                   [adsr_transform(*e) for e in envelopes])
        return make_note

    module = {
        "make_sound": builtin("make_sound", make_sound, 2),
        "get_wave": builtin("get_wave", get_wave, 1),
        "get_duration": builtin("get_duration", lambda s: sound("get_duration", s).duration, 1),
        "is_sound": builtin("is_sound", lambda x: type(x) is Sound, 1),
        "play": builtin("play", play, 1, -1, True),
        "play_in_tab": builtin("play_in_tab", play, 1, -1, True),
        "play_wave": builtin("play_wave", play_wave, 2, -1, True),
        "stop": builtin("stop", lambda: None, 0),
        "noise_sound": builtin("noise_sound", noise_sound, 1),
        "silence_sound": builtin("silence_sound", silence_sound, 1),
        "sine_sound": builtin("sine_sound", sine_sound, 2),
        "square_sound": builtin("square_sound", square_sound, 2),
        "triangle_sound": builtin("triangle_sound", triangle_sound, 2),
        "sawtooth_sound": builtin("sawtooth_sound", sawtooth_sound, 2),
        "consecutively": builtin("consecutively", consecutively, 1),
        "simultaneously": builtin("simultaneously", simultaneously, 1),
        "adsr": builtin("adsr", adsr, 4),
        "stacking_adsr": builtin("stacking_adsr", stacking_adsr, 4),
        "phase_mod": builtin("phase_mod", phase_mod, 3),
        "midi_note_to_frequency": builtin("midi_note_to_frequency", midi_note_to_frequency, 1),
        "letter_name_to_midi_note": builtin("letter_name_to_midi_note", letter_name_to_midi_note, 1),
        "letter_name_to_frequency": builtin(
            "letter_name_to_frequency", lambda name: midi_note_to_frequency(letter_name_to_midi_note(name)), 1),
        "bell": builtin("bell", instrument("bell", square, [(0, 0.6, 0, 0.05), (0, 0.6618, 0, 0.05),
                                                            (0, 0.7618, 0, 0.05), (0, 0.9071, 0, 0.05)]), 2),
        "cello": builtin("cello", instrument("cello", square, [(0.05, 0, 1, 0.1), (0.05, 0, 1, 0.15),
                                                               (0, 0, 0.2, 0.15)]), 2),
        "piano": builtin("piano", instrument("piano", triangle, [(0, 0.515, 0, 0.05), (0, 0.32, 0, 0.05),
                                                                 (0, 0.2, 0, 0.05)]), 2),
        "trombone": builtin("trombone", instrument("trombone", square, [(0.2, 0, 1, 0.1),
                                                                       (0.3236, 0.6, 0, 0.1)]), 2),
        "violin": builtin("violin", instrument("violin", sawtooth, [(0.35, 0, 1, 0.15), (0.35, 0, 1, 0.15),
                                                                    (0.45, 0, 1, 0.15), (0.45, 0, 1, 0.15)]), 2),
    }
    return module
