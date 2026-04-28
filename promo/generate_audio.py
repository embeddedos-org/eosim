"""Generate per-segment narration audio and output durations for Manim sync."""
import json
from gtts import gTTS
from mutagen.mp3 import MP3

SEGMENTS = [
    {"id": "intro", "text": "Introducing EoSim. Multi-Architecture Simulation Platform."},
    {"id": "f1", "text": "Feature one. ARM/RISC-V/x86 Emulation. Cycle-accurate CPU emulation for all major embedded architectures."},
    {"id": "f2", "text": "Feature two. Peripheral Simulation. GPIO, UART, SPI, I2C, and Timer models behave like real hardware."},
    {"id": "f3", "text": "Feature three. GDB Debug Integration. Connect GDB directly to simulated targets for source-level debugging."},
    {"id": "arch", "text": "Under the hood, EoSim is built with Python, C, QEMU. The architecture flows from CPU Core, to Memory Bus, to Peripherals, to GDB Server, to Trace."},
    {"id": "cta", "text": "EoSim. Open source and production ready. Visit github dot com slash embeddedos-org slash EoSim."},
]

durations = {}
audio_files = []

for seg in SEGMENTS:
    filename = f"seg_{seg['id']}.mp3"
    tts = gTTS(text=seg["text"], lang="en", slow=False)
    tts.save(filename)
    dur = MP3(filename).info.length
    durations[seg["id"]] = round(dur + 0.5, 1)  # add 0.5s padding
    audio_files.append(filename)
    print(f"  {seg['id']}: {dur:.1f}s -> padded {durations[seg['id']]}s")

# Write durations JSON for Manim to read
with open("durations.json", "w") as f:
    json.dump(durations, f, indent=2)

# Concatenate all segments into single narration.mp3
import subprocess
list_file = "concat_list.txt"
with open(list_file, "w") as f:
    for af in audio_files:
        f.write(f"file '{af}'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", list_file, "-c", "copy", "narration.mp3"
], check=True)

total = sum(durations.values())
print(f"\nTotal narration: {total:.1f}s")
print(f"Durations: {json.dumps(durations)}")
