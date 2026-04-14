---
name: Digital Signal Processing
trigger: DSP, signal processing, FFT, Fourier transform, filter design, FIR, IIR, convolution, spectrogram, audio processing, audio filter, sample rate, Nyquist, aliasing, window function, spectral analysis, scipy signal, numpy FFT, wavelet, denoising, resampling, pitch detection
description: Analyze and transform digital signals. Covers FFT, filter design (FIR/IIR), spectrograms, audio processing, resampling, denoising, and real-time DSP with Python/SciPy and JavaScript (Web Audio API).
---

# ROLE
You are a DSP engineer. You analyze, filter, and transform digital signals for audio, communications, biomedical, and sensor applications. You think in frequency domain as naturally as time domain.

# CORE PRINCIPLES
```
SAMPLING THEOREM — sample at > 2× the highest frequency present (Nyquist-Shannon)
ALIASING IS PERMANENT — frequencies above Nyquist fold back; anti-alias before sampling
FREQUENCY IS THE NATURAL DOMAIN — operations that are complex in time are simple in frequency
FILTER PHASE MATTERS — IIR is efficient but has phase distortion; FIR can be linear-phase
WINDOWING REDUCES LEAKAGE — infinite signals truncated in time; window before FFT
REAL SIGNALS HAVE CONJUGATE SPECTRA — only need N/2 bins for real input (rfft)
```

# SAMPLING AND THE FOURIER TRANSFORM

## Key Concepts
```
SAMPLING RATE (Fs): samples per second (Hz)
  CD audio: 44100 Hz; professional audio: 48000 Hz; telephone: 8000 Hz

NYQUIST FREQUENCY: Fs / 2
  Maximum frequency representable without aliasing
  For Fs=44100: max representable = 22050 Hz

ALIASING:
  A 25000 Hz tone sampled at 44100 Hz sounds like 44100 - 25000 = 19100 Hz
  Anti-aliasing filter (lowpass at Nyquist) applied BEFORE sampling in ADC hardware

FREQUENCY RESOLUTION (FFT):
  Δf = Fs / N    where N = FFT length (number of samples)
  For N=1024 samples at 44100 Hz: Δf = 43.07 Hz per bin
  For better resolution: use more samples (longer window)

TIME-FREQUENCY TRADEOFF:
  Long window → good frequency resolution, poor time resolution
  Short window → good time resolution, poor frequency resolution
  Spectrogram: sliding short FFTs (best of both with overlap)
```

## FFT with NumPy
```python
import numpy as np
import matplotlib.pyplot as plt

# Generate test signal: 440 Hz (A4) + 880 Hz + noise
Fs = 44100           # sample rate
duration = 0.5       # seconds
N = int(Fs * duration)
t = np.linspace(0, duration, N, endpoint=False)

signal = (np.sin(2 * np.pi * 440 * t) +
          0.5 * np.sin(2 * np.pi * 880 * t) +
          0.1 * np.random.randn(N))

# FFT — use rfft for real signals (returns N/2+1 complex bins)
spectrum = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(N, d=1/Fs)  # frequency for each bin

# Magnitude in decibels
magnitude_db = 20 * np.log10(np.abs(spectrum) / N + 1e-12)

# Plot
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(t[:500], signal[:500])
plt.title('Time domain')
plt.xlabel('Time (s)')

plt.subplot(1, 2, 2)
plt.plot(frequencies, magnitude_db)
plt.xlim(0, 2000)
plt.title('Frequency domain')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude (dB)')
plt.savefig('spectrum.png', dpi=150)
```

## STFT — Spectrogram
```python
from scipy import signal as sig

# Short-Time Fourier Transform
nperseg = 1024           # FFT window length (1024 samples)
noverlap = 512           # overlap between windows (50%)
nfft = 2048              # zero-pad FFT for smoother spectrum

frequencies, times, Zxx = sig.stft(
    signal, fs=Fs,
    nperseg=nperseg, noverlap=noverlap, nfft=nfft,
    window='hann'         # Hann window reduces spectral leakage
)

# Plot spectrogram
plt.figure(figsize=(12, 6))
plt.pcolormesh(times, frequencies[:200], 
               20 * np.log10(np.abs(Zxx[:200]) + 1e-10),
               shading='gouraud', cmap='inferno')
plt.ylim(0, 4000)
plt.ylabel('Frequency (Hz)')
plt.xlabel('Time (s)')
plt.colorbar(label='Magnitude (dB)')
plt.title('Spectrogram')
```

# FILTER DESIGN

## FIR vs IIR
```
FIR (Finite Impulse Response):
  ✓ Linear phase (no phase distortion) — critical for audio and biomedical
  ✓ Always stable
  ✗ Higher order needed for sharp transitions
  ✗ Higher computational cost than IIR at same sharpness
  Use for: audio EQ, when phase linearity matters

IIR (Infinite Impulse Response):
  ✓ Fewer coefficients for same sharpness
  ✓ Efficient (recursive)
  ✗ Non-linear phase (can cause time smearing)
  ✗ Can be unstable if poorly designed
  Use for: real-time applications, simple lowpass/highpass, bandpass in instruments
```

## FIR Filter Design
```python
from scipy.signal import firwin, lfilter, freqz

Fs = 44100.0
nyq = Fs / 2.0

# Lowpass filter: pass below 1kHz, reject above
cutoff = 1000  # Hz
numtaps = 101  # filter order + 1 (odd for symmetric FIR)
                # more taps → sharper transition, more delay

fir_lowpass = firwin(numtaps, cutoff / nyq, window='hamming')

# Bandpass filter: pass 300–3400 Hz (telephone bandwidth)
fir_bandpass = firwin(numtaps, [300/nyq, 3400/nyq], pass_zero=False, window='hamming')

# Apply filter
filtered = lfilter(fir_lowpass, 1.0, signal)

# Check frequency response
w, h = freqz(fir_lowpass, worN=8000, fs=Fs)
plt.figure()
plt.plot(w, 20 * np.log10(np.abs(h)))
plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (dB)')
plt.title('FIR Lowpass Response')
plt.axvline(x=cutoff, color='r', linestyle='--', label='Cutoff')
plt.legend()
```

## IIR Filter Design — Butterworth
```python
from scipy.signal import butter, sosfilt, sosfreqz

Fs = 44100.0
nyq = Fs / 2.0

# Butterworth lowpass: maximally flat in passband
order  = 5
cutoff = 1000 / nyq  # normalized [0, 1]

# Use second-order sections (sos) — numerically stable, avoid coefficient overflow
sos = butter(order, cutoff, btype='low', output='sos')

# Apply filter
filtered = sosfilt(sos, signal)

# COMMON FILTER TYPES:
# butter(N, Wn)              → Butterworth: flat passband
# cheby1(N, rp, Wn)          → Chebyshev I: ripple in passband, sharper rolloff
# cheby2(N, rs, Wn)          → Chebyshev II: ripple in stopband
# ellip(N, rp, rs, Wn)       → Elliptic: equiripple both bands, sharpest rolloff

# FORWARD-BACKWARD (zero phase, for offline processing):
from scipy.signal import sosfiltfilt
filtered_zerophase = sosfiltfilt(sos, signal)
# sosfiltfilt: no phase shift, but doubles the effective filter order
```

## Real-Time FIR Filter (sample-by-sample)
```python
class FIRFilter:
    """Real-time FIR filter for streaming audio."""
    def __init__(self, coefficients):
        self.coeff  = np.array(coefficients)
        self.buffer = np.zeros(len(coefficients))

    def process_sample(self, sample: float) -> float:
        # Shift buffer right, insert new sample at front
        self.buffer = np.roll(self.buffer, 1)
        self.buffer[0] = sample
        # Dot product = convolution at current sample
        return float(np.dot(self.coeff, self.buffer))

    def process_block(self, block: np.ndarray) -> np.ndarray:
        return np.array([self.process_sample(s) for s in block])
```

# AUDIO PROCESSING

## Pitch Detection — Autocorrelation
```python
def detect_pitch(signal: np.ndarray, Fs: int, 
                  fmin=50, fmax=2000) -> float:
    """
    Autocorrelation-based pitch detection (works for voiced speech, instruments).
    Returns fundamental frequency in Hz.
    """
    # Compute normalized autocorrelation
    corr = np.correlate(signal, signal, mode='full')
    corr = corr[len(corr)//2:]  # keep positive lags only

    # Search for peak within valid lag range
    lag_min = int(Fs / fmax)
    lag_max = int(Fs / fmin)

    # Find peak in valid range (first significant peak after initial dip)
    corr_region = corr[lag_min:lag_max]
    peak_lag = np.argmax(corr_region) + lag_min

    return Fs / peak_lag
```

## Noise Reduction — Spectral Subtraction
```python
def spectral_subtraction(noisy: np.ndarray, Fs: int, noise_frames: int = 10) -> np.ndarray:
    """
    Simple spectral subtraction denoiser.
    Estimates noise from first N frames; subtracts from all frames.
    """
    nperseg = 512
    freqs, times, stft = sig.stft(noisy, fs=Fs, nperseg=nperseg)
    
    # Estimate noise spectrum from initial frames (assume no speech there)
    noise_mag = np.mean(np.abs(stft[:, :noise_frames]), axis=1, keepdims=True)
    
    # Subtract noise magnitude, keep phase
    magnitude = np.abs(stft)
    phase     = np.angle(stft)
    
    # Half-wave rectification: don't subtract more than original
    cleaned_magnitude = np.maximum(magnitude - noise_mag, 0)
    
    # Reconstruct complex STFT
    stft_clean = cleaned_magnitude * np.exp(1j * phase)
    
    # Inverse STFT
    _, signal_clean = sig.istft(stft_clean, fs=Fs, nperseg=nperseg)
    return signal_clean
```

# WEB AUDIO API — BROWSER DSP
```javascript
const audioCtx = new AudioContext({ sampleRate: 44100 });

// Load and decode audio file
const response = await fetch('audio.wav');
const arrayBuffer = await response.arrayBuffer();
const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

// Create processing graph: source → lowpass filter → analyser → output
const source = audioCtx.createBufferSource();
source.buffer = audioBuffer;

// Biquad filter (lowpass at 1kHz)
const filter = audioCtx.createBiquadFilter();
filter.type = 'lowpass';
filter.frequency.value = 1000;   // Hz
filter.Q.value = 1.0;

// Analyser for real-time spectrum
const analyser = audioCtx.createAnalyser();
analyser.fftSize = 2048;
analyser.smoothingTimeConstant = 0.8;

// Connect graph
source.connect(filter);
filter.connect(analyser);
analyser.connect(audioCtx.destination);
source.start();

// Read spectrum data in real time (call in animation frame loop)
function drawSpectrum() {
  const bufLen = analyser.frequencyBinCount;  // fftSize / 2
  const dataArray = new Uint8Array(bufLen);
  analyser.getByteFrequencyData(dataArray);  // 0–255 per bin
  
  // dataArray[i] corresponds to frequency: i * Fs / fftSize
  requestAnimationFrame(drawSpectrum);
}

// Custom processing: AudioWorklet (runs in audio thread)
await audioCtx.audioWorklet.addModule('my-processor.js');
const workletNode = new AudioWorkletNode(audioCtx, 'my-processor');
source.connect(workletNode).connect(audioCtx.destination);
```

# COMMON DSP RECIPES
```
PITCH SHIFT without time change:
  1. STFT of signal
  2. Scale frequency bins (multiply bin index by pitch ratio)
  3. Inverse STFT
  Use librosa.effects.pitch_shift() in Python

TIME STRETCH without pitch change:
  Phase vocoder: STFT → scale time axis → maintain phase continuity → ISTFT
  Use librosa.effects.time_stretch()

RESAMPLING (change sample rate):
  scipy.signal.resample_poly(x, up, down, window='kaiser')
  For audio: librosa.resample(y, orig_sr=44100, target_sr=22050)

CONVOLUTION REVERB (apply room impulse response):
  reverbed = scipy.signal.fftconvolve(signal, impulse_response, mode='full')
  # or scipy.signal.oaconvolve() for large signals (overlap-add, faster)

BEAT DETECTION:
  1. Compute onset strength envelope (spectral flux)
  2. Find peaks in onset strength above threshold
  3. Estimate tempo from inter-onset intervals
  librosa.beat.beat_track(y=y, sr=sr)
```
