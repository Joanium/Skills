---
name: Quantum Computing
trigger: quantum computing, qubit, quantum circuit, quantum gate, superposition, entanglement, quantum algorithm, Qiskit, Cirq, quantum measurement, Hadamard, CNOT, quantum Fourier transform, Grover's algorithm, Shor's algorithm, variational quantum eigensolver, VQE, QAOA, quantum noise, decoherence, quantum error correction
description: Design and simulate quantum circuits and algorithms. Covers qubits, quantum gates, superposition, entanglement, Qiskit programming, quantum algorithms (Grover, QFT, VQE), noise models, and the current NISQ era landscape.
---

# ROLE
You are a quantum software engineer. You design quantum circuits, implement quantum algorithms, and run them on simulators and real quantum hardware. You understand both the mathematics and the practical engineering constraints of today's noisy intermediate-scale quantum (NISQ) devices.

# CORE PRINCIPLES
```
QUBITS ARE PROBABILITY AMPLITUDES — not just 0 or 1; complex-valued superpositions
MEASUREMENT DESTROYS SUPERPOSITION — you only get a classical bit when you look
ENTANGLEMENT IS CORRELATION — measuring one qubit instantly determines the other's outcome
QUANTUM CIRCUITS ARE UNITARY — all operations are reversible (except measurement)
NOISE IS THE ENEMY — decoherence, gate errors, and crosstalk limit real quantum advantage
NISQ = NO ERROR CORRECTION — today's quantum devices have noisy qubits and limited depth
```

# QUANTUM MECHANICS ESSENTIALS

## Qubit State Representation
```
Single qubit state:
  |ψ⟩ = α|0⟩ + β|1⟩     where α, β ∈ ℂ  and |α|² + |β|² = 1

  |0⟩ = [1, 0]ᵀ   (basis state "zero")
  |1⟩ = [0, 1]ᵀ   (basis state "one")

  |α|² = probability of measuring 0
  |β|² = probability of measuring 1

Important states:
  |+⟩ = (|0⟩ + |1⟩) / √2  → equal superposition (H applied to |0⟩)
  |-⟩ = (|0⟩ - |1⟩) / √2  → equal superposition with phase flip

Two-qubit state (tensor product):
  |ψ₁⟩ ⊗ |ψ₂⟩ = [α₁α₂, α₁β₂, β₁α₂, β₁β₂]ᵀ   (4-dimensional vector)

Bell state (maximally entangled):
  |Φ⁺⟩ = (|00⟩ + |11⟩) / √2
  Measuring first qubit as 0 → second qubit is definitely 0 (and vice versa)
```

## Key Quantum Gates
```
Single-qubit gates (2×2 unitary matrices):

HADAMARD (H): creates superposition from |0⟩ or |1⟩
  H = (1/√2) [[1,  1],
               [1, -1]]
  H|0⟩ = |+⟩,  H|1⟩ = |-⟩

PAULI-X (NOT): flips |0⟩↔|1⟩
  X = [[0, 1], [1, 0]]

PAULI-Z: phase flip  |0⟩→|0⟩, |1⟩→-|1⟩
  Z = [[1, 0], [0, -1]]

T GATE: π/8 phase rotation (important for universal quantum computation)
  T = [[1, 0], [0, e^(iπ/4)]]

Rz(θ): rotation around Z-axis by angle θ
  Rz(θ) = [[e^(-iθ/2), 0], [0, e^(iθ/2)]]

Two-qubit gates:
CNOT (Controlled-NOT): flip target if control = |1⟩
  Matrix (control=q0, target=q1):
  [[1,0,0,0],
   [0,1,0,0],
   [0,0,0,1],
   [0,0,1,0]]

SWAP: exchange two qubit states
CZ:  apply Z gate to target if control = |1⟩ (symmetric)
```

# QISKIT — IBM QUANTUM SDK

## Circuit Basics
```python
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

# Create Bell state: (|00⟩ + |11⟩) / √2
qc = QuantumCircuit(2, 2)  # 2 qubits, 2 classical bits

qc.h(0)          # Hadamard on qubit 0: |0⟩ → |+⟩ = (|0⟩ + |1⟩)/√2
qc.cx(0, 1)      # CNOT: control=0, target=1
                 # Entangles: |+⟩|0⟩ → (|00⟩ + |11⟩)/√2

qc.measure([0, 1], [0, 1])  # measure qubits into classical bits

print(qc.draw())

# Simulate
sim = AerSimulator()
job = sim.run(qc, shots=1024)
counts = job.result().get_counts()
print(counts)  # {'00': ~512, '11': ~512} — perfect correlation
```

## Grover's Algorithm (Quantum Search)
```python
from qiskit import QuantumCircuit
import numpy as np

def grover_oracle(n_qubits: int, target: int) -> QuantumCircuit:
    """
    Oracle: flips the phase of the target state.
    |target⟩ → -|target⟩, all others unchanged.
    """
    qc = QuantumCircuit(n_qubits)
    # Convert target to binary; apply X where bit is 0
    binary = format(target, f'0{n_qubits}b')
    for i, bit in enumerate(reversed(binary)):
        if bit == '0':
            qc.x(i)
    
    # Multi-controlled-Z: flip phase if all qubits are |1⟩
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)  # multi-controlled X
    qc.h(n_qubits - 1)
    
    for i, bit in enumerate(reversed(binary)):
        if bit == '0':
            qc.x(i)
    return qc

def diffusion_operator(n_qubits: int) -> QuantumCircuit:
    """
    Grover diffusion: amplifies the marked state.
    2|s⟩⟨s| - I  where |s⟩ = uniform superposition
    """
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    qc.h(n_qubits - 1)
    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    return qc

def grover_search(n_qubits: int, target: int, shots: int = 1024):
    """
    Grover's algorithm: finds target in unsorted database of 2^n items.
    Classical: O(N) steps. Quantum: O(√N) steps.
    """
    N = 2 ** n_qubits
    n_iterations = int(np.pi / 4 * np.sqrt(N))  # optimal iterations ≈ π/4 * √N
    
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # Initialize: uniform superposition
    qc.h(range(n_qubits))
    
    # Grover iterations
    oracle = grover_oracle(n_qubits, target)
    diffusion = diffusion_operator(n_qubits)
    
    for _ in range(n_iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffusion, inplace=True)
    
    qc.measure(range(n_qubits), range(n_qubits))
    
    sim = AerSimulator()
    counts = sim.run(qc, shots=shots).result().get_counts()
    
    # Most frequent result should be target
    top_result = max(counts, key=counts.get)
    return int(top_result, 2), counts
```

## Variational Quantum Eigensolver (VQE)
```python
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
import numpy as np

# VQE: find ground state energy of a Hamiltonian using NISQ hardware
# Hybrid: quantum circuit evaluates energy; classical optimizer adjusts parameters

def vqe_example():
    # Simple H2 molecule Hamiltonian (simplified)
    hamiltonian = SparsePauliOp.from_list([
        ("II", -1.0523732),
        ("IZ", 0.39793742),
        ("ZI", -0.39793742),
        ("ZZ", -0.01128010),
        ("XX", 0.18093120)
    ])
    
    n_qubits = 2
    
    # Ansatz: parameterized quantum circuit
    ansatz = TwoLocal(n_qubits, 'ry', 'cx', reps=2)
    n_params = ansatz.num_parameters
    
    sim = AerSimulator(method='statevector')
    
    def energy(params):
        """Evaluate expectation value ⟨ψ(θ)|H|ψ(θ)⟩"""
        bound_circuit = ansatz.assign_parameters(params)
        # Use estimator primitive (Qiskit 1.0+)
        from qiskit.primitives import StatevectorEstimator
        estimator = StatevectorEstimator()
        job = estimator.run([(bound_circuit, hamiltonian)])
        result = job.result()
        return result[0].data.evs.real
    
    # Classical optimization
    initial_params = np.random.uniform(0, 2*np.pi, n_params)
    result = minimize(energy, initial_params, method='COBYLA',
                     options={'maxiter': 300})
    
    print(f"VQE ground state energy: {result.fun:.6f} Hartree")
    print(f"Exact value:             -1.137270 Hartree")
    return result
```

# QUANTUM FOURIER TRANSFORM (QFT)
```python
def qft(n: int) -> QuantumCircuit:
    """
    Quantum Fourier Transform on n qubits.
    Quantum analogue of DFT; core of Shor's algorithm and phase estimation.
    Runs in O(n²) gates vs O(n·2^n) classical.
    """
    qc = QuantumCircuit(n)
    
    for j in range(n):
        qc.h(j)  # Hadamard
        for k in range(j + 1, n):
            angle = np.pi / (2 ** (k - j))
            qc.cp(angle, k, j)  # Controlled phase rotation
    
    # Reverse qubit order
    for i in range(n // 2):
        qc.swap(i, n - i - 1)
    
    return qc
```

# NOISE AND DECOHERENCE
```python
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error

# Build realistic noise model
noise_model = NoiseModel()

# Single-qubit gate error (1% depolarizing)
single_qubit_error = depolarizing_error(0.01, 1)
noise_model.add_all_qubit_quantum_error(single_qubit_error, ['h', 'rx', 'ry', 'rz'])

# Two-qubit gate error (5% depolarizing — CNOT is much noisier)
two_qubit_error = depolarizing_error(0.05, 2)
noise_model.add_all_qubit_quantum_error(two_qubit_error, ['cx'])

# T1/T2 relaxation (qubit decays over time)
t1, t2 = 50e-6, 30e-6  # 50 μs T1, 30 μs T2
gate_time = 50e-9       # 50 ns gate time
relax_error = thermal_relaxation_error(t1, t2, gate_time)
noise_model.add_all_qubit_quantum_error(relax_error, ['h', 'cx'])

# Simulate with noise
sim_noisy = AerSimulator(noise_model=noise_model)
```

# NISQ ERA LANDSCAPE
```
CURRENT HARDWARE (2024-2025):
  IBM Quantum:  127–1000+ qubit devices; Eagle, Osprey, Condor, Heron
                Qiskit SDK; IBM Quantum Network access
  Google:       70-qubit Sycamore; demonstrated "quantum supremacy" (2019)
  IonQ:         Trapped ion; fewer qubits (25–35) but higher fidelity
  Quantinuum:   Trapped ion; H2 (56 qubits); highest fidelity currently
  Rigetti:      79-qubit; cloud access via AWS Braket / Rigetti Cloud

FIDELITY NUMBERS (approximate 2024):
  Single-qubit gate error:  0.05% – 0.5% (trapped ion better than superconducting)
  Two-qubit gate error:     0.3% – 2%
  T1 coherence time:        10 μs – 1 ms
  Circuit depth limit:      ~100-1000 gates before noise dominates

QUANTUM ADVANTAGE EXISTS TODAY FOR:
  → Random circuit sampling (Google Sycamore 2019, limited practical use)
  → Boson sampling (limited practical use)
  → Possibly: quantum simulation of chemistry near-term

QUANTUM ADVANTAGE COMING FOR:
  → Cryptography (Shor's algorithm: needs ~4000 error-corrected qubits — not yet)
  → Database search (Grover: quadratic speedup — needs error correction)
  → Optimization (QAOA — NISQ era, unclear practical advantage currently)
  → Chemistry simulation (VQE — most near-term promising)

SDK COMPARISON:
  Qiskit (IBM):      Most popular; best hardware access; Python
  Cirq (Google):     Low-level control; Google hardware; Python
  PennyLane:         Best for QML / hybrid algorithms; differentiable
  Amazon Braket:     Multi-hardware cloud access; AWS integration
  Azure Quantum:     Multi-hardware; IonQ, Quantinuum, Rigetti via Azure
```
