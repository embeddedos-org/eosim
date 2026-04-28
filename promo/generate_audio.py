"""Generate narration audio using Google Text-to-Speech."""
from gtts import gTTS

NARRATION = (
    "Introducing EoSim. Multi-architecture embedded simulation platform. Feature one: Emulates ARM, RISC-V, and x86 architectures in software. Feature two: Peripheral simulation models real hardware behavior. Feature three: GDB debug integration lets you step through embedded code. EoSim. Open source and developer friendly. Visit github dot com slash embeddedos-org slash EoSim."
)

tts = gTTS(text=NARRATION, lang="en", slow=False)
tts.save("narration.mp3")
print(f"Generated narration.mp3 ({len(NARRATION)} chars)")
