import sounddevice as sd
import soundfile as sf

duration = 5  # seconds
fs = 44100  # sample rate

print("Recording...")
audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()  # Wait until recording is finished
print("Recording finished.")

# Save and play the recorded audio
sf.write('output.wav', audio, fs)
print("Playing back the recorded audio...")
sd.play(audio, fs)
sd.wait()