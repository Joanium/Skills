---
name: Zero-Knowledge Proofs
trigger: zero-knowledge proof, ZKP, zk-SNARK, zk-STARK, zkEVM, Groth16, PLONK, circom, ZoKrates, snarkjs, bulletproofs, commitment scheme, witness, verifier, prover, zkRollup, privacy-preserving, cryptographic proof, zk circuit
description: Build privacy-preserving cryptographic systems using zero-knowledge proofs. Covers ZK fundamentals, zk-SNARKs, zk-STARKs, circuit design in Circom, trusted setup, real-world applications (zkRollups, identity, voting), and tooling.
---

# ROLE
You are a cryptographic engineer specializing in zero-knowledge proofs. You design ZK circuits and integrate ZKP systems to prove statements about private data without revealing the data itself.

# CORE PRINCIPLES
```
PROOF ≠ KNOWLEDGE — proving you know X without revealing X is the point
CIRCUIT = CONSTRAINT SYSTEM — ZK computations are arithmetic circuits of constraints
SOUNDNESS: ADVERSARY CANNOT FAKE — a false statement cannot produce a valid proof
ZERO-KNOWLEDGE: VERIFIER LEARNS NOTHING EXTRA — only that the statement is true
TRUSTED SETUP IS A RISK — Groth16 requires a ceremony; STARKs do not
SUCCINCTNESS MATTERS — proofs must be small and fast to verify
```

# INTUITIVE UNDERSTANDING

## The Classic Example: Proof of Graph 3-Coloring
```
Problem: You claim a graph is 3-colorable (each vertex colored; adjacent ≠ same color)
         but you don't want to reveal the coloring.

Protocol (interactive):
1. Prover: randomly permute colors; commit to coloring (sealed envelopes per vertex)
2. Verifier: picks random edge (u, v)
3. Prover: reveals colors of u and v only
4. Verifier: checks they are different
5. Repeat 100 times

After 100 rounds: 
  → If coloring is valid, every round passes
  → If coloring is invalid, probability of not getting caught → 0
  → Verifier never sees the full coloring (just random pairs) = zero knowledge

Non-interactive ZKP (zk-SNARK): this whole protocol compressed into one proof
```

## What ZKPs Are Used For
```
zkRollups (Ethereum L2):     Prove that 1000 transactions are valid without replaying all on L1
Identity systems:            Prove you are over 18 without revealing your birthdate
Voting:                      Prove your vote was counted correctly without revealing your vote
Private DeFi:                Prove you have sufficient collateral without revealing your balance
Authentication:              Prove you know a password without sending the password
```

# ZK-SNARK FUNDAMENTALS

## The R1CS Constraint System
```
ZK-SNARKs work by converting a computation into a constraint system:
R1CS = Rank-1 Constraint System

Each constraint has the form:
  (a · w) * (b · w) = (c · w)

Where:
  w = witness vector (private inputs + intermediate values)
  a, b, c = vectors of coefficients

Example: Prove I know x such that x³ + x + 5 = 35

Intermediate variables:
  x₁ = x * x        → constraint: (x) * (x) = x₁
  x₂ = x₁ * x       → constraint: (x₁) * (x) = x₂
  out = x₂ + x + 5  → constraint: (x₂ + x + 5) * (1) = out

Public input: out = 35
Private input (witness): x = 3 (kept secret)
Proof: I know x such that these constraints hold with out = 35
```

# CIRCOM — ZK CIRCUIT LANGUAGE

## Basic Circuit
```circom
pragma circom 2.1.4;

// Prove knowledge of a preimage of a Poseidon hash
// Public input: hash
// Private input: preimage

include "node_modules/circomlib/circuits/poseidon.circom";

template HashPreimage() {
    // Private input (witness)
    signal input preimage;
    
    // Public input (what the verifier knows)
    signal input hash;
    
    // Compute hash of preimage
    component hasher = Poseidon(1);
    hasher.inputs[0] <== preimage;
    
    // Constraint: computed hash must equal public hash
    // <== is both assignment AND constraint in Circom
    hash === hasher.out;
}

component main {public [hash]} = HashPreimage();
```

## Range Proof Circuit
```circom
pragma circom 2.1.4;

include "node_modules/circomlib/circuits/comparators.circom";

// Prove: value is in range [min, max] without revealing value
template RangeProof(n) {
    signal input value;       // private
    signal input min;         // public
    signal input max;         // public

    // Check value >= min
    component geMin = GreaterEqThan(n);
    geMin.in[0] <== value;
    geMin.in[1] <== min;
    geMin.out === 1;

    // Check value <= max
    component leMax = LessEqThan(n);
    leMax.in[0] <== value;
    leMax.in[1] <== max;
    leMax.out === 1;
}

// n=32 means values up to 2^32
component main {public [min, max]} = RangeProof(32);

// Use case: prove my age is between 18 and 120 without revealing my age
```

## Merkle Tree Membership Proof
```circom
pragma circom 2.1.4;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/mux1.circom";

// Prove: leaf is in Merkle tree with given root (without revealing leaf path)
template MerkleTreeInclusionProof(levels) {
    signal input leaf;                    // private: the leaf value
    signal input pathElements[levels];    // private: sibling hashes
    signal input pathIndices[levels];     // private: 0=left, 1=right
    signal input root;                    // public: Merkle root

    component hashers[levels];
    component muxes[levels];
    
    signal currentHash[levels + 1];
    currentHash[0] <== leaf;

    for (var i = 0; i < levels; i++) {
        hashers[i] = Poseidon(2);
        muxes[i] = MultiMux1(2);
        
        // pathIndices[i] = 0: current hash is left child
        // pathIndices[i] = 1: current hash is right child
        muxes[i].c[0][0] <== currentHash[i];
        muxes[i].c[0][1] <== pathElements[i];
        muxes[i].c[1][0] <== pathElements[i];
        muxes[i].c[1][1] <== currentHash[i];
        muxes[i].s <== pathIndices[i];

        hashers[i].inputs[0] <== muxes[i].out[0];
        hashers[i].inputs[1] <== muxes[i].out[1];
        currentHash[i + 1] <== hashers[i].out;
    }

    // Constraint: computed root must match public root
    root === currentHash[levels];
}

component main {public [root]} = MerkleTreeInclusionProof(20);
// Proves membership in a tree of up to 2^20 leaves
```

# SNARKJS — COMPILING AND USING CIRCUITS

## Complete Workflow
```bash
# 1. Compile the circuit
circom HashPreimage.circom --r1cs --wasm --sym

# 2. Trusted setup (Groth16 — requires ceremony for production)
snarkjs groth16 setup HashPreimage.r1cs pot12_final.ptau setup_0000.zkey
snarkjs zkey contribute setup_0000.zkey setup_final.zkey --name="Contributor"
snarkjs zkey export verificationkey setup_final.zkey verification_key.json

# 3. Generate proof
# Create input.json: {"preimage": "12345", "hash": "...computed_hash..."}
node generate_witness.js HashPreimage_js/HashPreimage.wasm input.json witness.wtns
snarkjs groth16 prove setup_final.zkey witness.wtns proof.json public.json

# 4. Verify proof
snarkjs groth16 verify verification_key.json public.json proof.json
# Output: OK  (or INVALID)

# 5. Export Solidity verifier (for on-chain verification)
snarkjs zkey export solidityverifier setup_final.zkey verifier.sol
```

## JavaScript Proof Generation & Verification
```javascript
import { groth16 } from 'snarkjs';

// Generate proof (in browser or Node.js)
async function proveHashPreimage(preimage, hash) {
  const input = {
    preimage: BigInt(preimage),
    hash: BigInt(hash)
  };
  
  const { proof, publicSignals } = await groth16.fullProve(
    input,
    "HashPreimage_js/HashPreimage.wasm",
    "setup_final.zkey"
  );
  
  return { proof, publicSignals };
}

// Verify proof (lightweight — verifier only needs verification key)
async function verifyProof(proof, publicSignals) {
  const vkey = await fetch('/verification_key.json').then(r => r.json());
  const isValid = await groth16.verify(vkey, publicSignals, proof);
  return isValid;  // true/false
}

// Proof size: ~200 bytes (Groth16)
// Verification time: ~10ms
// Proving time: ~1-10s (depending on circuit size)
```

# ZK-STARK vs ZK-SNARK
```
                    zk-SNARK (Groth16)    zk-STARK
─────────────────────────────────────────────────────
Trusted setup:      Required (ceremony)   Not required (transparent)
Proof size:         ~200 bytes            ~50-200 KB
Verify time:        ~10ms                 ~100ms
Post-quantum safe:  No (elliptic curves)  Yes (hash-based)
Prover time:        Fast                  Slower
Best for:           zkRollups, on-chain   High-security, large proofs
Libraries:          snarkjs, bellman      StarkWare, RISC Zero
```

# COMMON CIRCUIT PATTERNS
```
RANGE CHECK: value ∈ [0, 2^n)
  → Decompose into n bits; verify each bit is 0 or 1; verify bit reconstruction

CONDITIONAL SELECTION: out = cond ? a : b
  → Circom: out <== cond * a + (1 - cond) * b
  → Requires cond ∈ {0, 1}; verify with cond * (1 - cond) === 0

EQUALITY WITHOUT REVEALING:
  → Hash both values; compare hashes in circuit

SIGNATURE VERIFICATION:
  → Use circomlib/circuits/eddsa.circom (EdDSA on BabyJubJub curve)

PRIVATE BALANCE TRANSFER:
  → Prove: old_balance - amount >= 0 (range check)
  → Prove: new_balance = old_balance - amount (arithmetic constraint)
  → Commitments (hashes) to balances are public; values are private
```

# TOOLING & LIBRARIES
```
Circuit Languages:
  Circom 2.x:     Most widely used; snarkjs ecosystem
  Cairo:          StarkNet's ZK-native language
  Noir:           Rust-like syntax; Aztec Network
  Halo2:          Zcash/EF; Rust; no trusted setup
  Leo:            Aleo blockchain

Libraries:
  circomlib:      Standard circuits (hashes, comparators, ECDSA)
  snarkjs:        Groth16/PLONK prover/verifier in JS
  bellman (Rust): Low-level Groth16
  arkworks:       Rust ZK toolkit
  gnark (Go):     Fast proving, production-ready

Testing:
  circom --inspect: reports signal warnings
  Mocha + snarkjs: unit test constraints
  Assert final output values; check under/overconstrained signals
```
