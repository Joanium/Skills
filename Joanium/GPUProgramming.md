---
name: GPU Programming
trigger: GPU, CUDA, WebGPU, WGSL, compute shader, parallel computing, GPU kernel, SIMD, warp, thread block, shared memory, GPU optimization, GPGPU, OpenCL, metal shader, GPU pipeline, coalesced memory, occupancy
description: Write high-performance GPU code using CUDA, WebGPU/WGSL, and compute shaders. Covers GPU architecture, memory hierarchy, kernel design, occupancy optimization, and porting CPU algorithms to massively parallel GPU execution.
---

# ROLE
You are a GPU engineer. You write compute kernels that exploit massive parallelism for numerical computation, graphics, machine learning, and simulation. You think in warps, not threads, and in bandwidth, not FLOPS.

# CORE PRINCIPLES
```
GPU IS A THROUGHPUT MACHINE — not a latency machine; thousands of concurrent threads
MEMORY BANDWIDTH IS THE BOTTLENECK — most real programs are memory-bound, not compute-bound
COALESCED ACCESS WINS — threads in a warp accessing adjacent memory = 1 transaction
DIVERGENCE KILLS WARPS — if-else inside a warp serializes; all branches run
OCCUPY THE GPU — hide latency with enough warps in flight (high occupancy)
SHARED MEMORY IS L1 — explicit scratchpad; 48KB–164KB per SM
PROFILE BEFORE OPTIMIZING — Nsight/RenderDoc tells you what to fix
```

# GPU ARCHITECTURE MENTAL MODEL
```
CPU (8–64 cores):              GPU (thousands of cores):
  Few powerful cores             Many weak cores (CUDA cores / shader units)
  Deep cache hierarchy           Shallow cache, wide memory bus
  Out-of-order execution         In-order, hide latency with threads
  Branch predictor               Warp-level SIMD (32 threads / warp)
  Low latency                    High throughput

NVIDIA HIERARCHY:
  Grid → Blocks → Warps (32 threads) → Threads
  SM (Streaming Multiprocessor) executes blocks
  Registers: per-thread, fastest; spilling to local mem is slow
  Shared mem: per-block, explicit, ~100x faster than global
  L2 cache: shared across all SMs
  Global DRAM: 80–140 GB/s (consumer), 2–3 TB/s (HBM on data center GPUs)
```

# CUDA — C/C++ GPU Programming

## Kernel Basics
```cuda
// Vector addition: classic "hello world" of CUDA
__global__ void vectorAdd(const float* A, const float* B, float* C, int n) {
    // Each thread handles one element
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        C[idx] = A[idx] + B[idx];
    }
}

int main() {
    const int N = 1 << 20;  // 1M elements
    const int bytes = N * sizeof(float);

    // Allocate and fill host memory
    float *h_A = new float[N], *h_B = new float[N], *h_C = new float[N];
    for (int i = 0; i < N; i++) { h_A[i] = 1.0f; h_B[i] = 2.0f; }

    // Allocate device memory
    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, bytes);
    cudaMalloc(&d_B, bytes);
    cudaMalloc(&d_C, bytes);

    // Copy to device
    cudaMemcpy(d_A, h_A, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, bytes, cudaMemcpyHostToDevice);

    // Launch: 256 threads/block, ceil(N/256) blocks
    int threadsPerBlock = 256;
    int blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
    vectorAdd<<<blocksPerGrid, threadsPerBlock>>>(d_A, d_B, d_C, N);

    // Wait for GPU
    cudaDeviceSynchronize();

    // Copy result back
    cudaMemcpy(h_C, d_C, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
    delete[] h_A; delete[] h_B; delete[] h_C;
}
```

## Shared Memory — Tiled Matrix Multiplication
```cuda
#define TILE_SIZE 16

__global__ void matMulTiled(const float* A, const float* B, float* C, int N) {
    __shared__ float tileA[TILE_SIZE][TILE_SIZE];
    __shared__ float tileB[TILE_SIZE][TILE_SIZE];

    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;
    float sum = 0.0f;

    for (int t = 0; t < N / TILE_SIZE; t++) {
        // Cooperatively load tile into shared memory
        tileA[threadIdx.y][threadIdx.x] = A[row * N + (t * TILE_SIZE + threadIdx.x)];
        tileB[threadIdx.y][threadIdx.x] = B[(t * TILE_SIZE + threadIdx.y) * N + col];
        __syncthreads();  // barrier: all threads must finish loading

        // Compute partial dot product from shared tile
        for (int k = 0; k < TILE_SIZE; k++)
            sum += tileA[threadIdx.y][k] * tileB[k][threadIdx.x];
        
        __syncthreads();  // barrier: all threads done computing before next tile
    }

    C[row * N + col] = sum;
}
// WHY THIS IS FAST: each element of A and B loaded from global memory once
// then reused TILE_SIZE times from fast shared memory
// Achieves ~10x speedup over naive global-memory version
```

## Parallel Reduction (Sum)
```cuda
// Classic pattern: halve active threads each step
__global__ void reduceSum(float* input, float* output, int n) {
    __shared__ float sdata[256];

    unsigned int tid = threadIdx.x;
    unsigned int idx = blockIdx.x * blockDim.x * 2 + threadIdx.x;

    // Load two elements per thread
    sdata[tid] = (idx < n ? input[idx] : 0.0f) 
               + (idx + blockDim.x < n ? input[idx + blockDim.x] : 0.0f);
    __syncthreads();

    // Reduce in shared memory
    for (unsigned int s = blockDim.x / 2; s > 32; s >>= 1) {
        if (tid < s) sdata[tid] += sdata[tid + s];
        __syncthreads();
    }

    // Warp-level reduction (no __syncthreads needed — warp is synchronous)
    if (tid < 32) {
        volatile float* vdata = sdata;
        vdata[tid] += vdata[tid + 32];
        vdata[tid] += vdata[tid + 16];
        vdata[tid] += vdata[tid +  8];
        vdata[tid] += vdata[tid +  4];
        vdata[tid] += vdata[tid +  2];
        vdata[tid] += vdata[tid +  1];
    }

    if (tid == 0) output[blockIdx.x] = sdata[0];
}
```

# WEBGPU / WGSL — GPU IN THE BROWSER

## Compute Shader Setup
```javascript
// Initialize WebGPU
const adapter = await navigator.gpu.requestAdapter();
const device = await adapter.requestDevice();

// Write WGSL compute shader
const shaderCode = /* wgsl */`
  @group(0) @binding(0) var<storage, read>       inputA : array<f32>;
  @group(0) @binding(1) var<storage, read>       inputB : array<f32>;
  @group(0) @binding(2) var<storage, read_write> output : array<f32>;

  @compute @workgroup_size(64)
  fn main(@builtin(global_invocation_id) gid : vec3<u32>) {
    let idx = gid.x;
    if (idx >= arrayLength(&output)) { return; }
    output[idx] = inputA[idx] + inputB[idx];
  }
`;

const module = device.createShaderModule({ code: shaderCode });

const N = 1024 * 1024;
const byteSize = N * 4;  // f32 = 4 bytes

// Create GPU buffers
const bufA = device.createBuffer({ size: byteSize, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST });
const bufB = device.createBuffer({ size: byteSize, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST });
const bufOut = device.createBuffer({ size: byteSize, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });
const readBuf = device.createBuffer({ size: byteSize, usage: GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST });

// Upload data
const dataA = new Float32Array(N).fill(1.0);
const dataB = new Float32Array(N).fill(2.0);
device.queue.writeBuffer(bufA, 0, dataA);
device.queue.writeBuffer(bufB, 0, dataB);

// Pipeline
const pipeline = device.createComputePipeline({
  layout: 'auto',
  compute: { module, entryPoint: 'main' }
});

const bindGroup = device.createBindGroup({
  layout: pipeline.getBindGroupLayout(0),
  entries: [
    { binding: 0, resource: { buffer: bufA } },
    { binding: 1, resource: { buffer: bufB } },
    { binding: 2, resource: { buffer: bufOut } },
  ]
});

// Encode and submit
const encoder = device.createCommandEncoder();
const pass = encoder.beginComputePass();
pass.setPipeline(pipeline);
pass.setBindGroup(0, bindGroup);
pass.dispatchWorkgroups(Math.ceil(N / 64));  // total threads = 64 * ceil(N/64)
pass.end();
encoder.copyBufferToBuffer(bufOut, 0, readBuf, 0, byteSize);
device.queue.submit([encoder.finish()]);

// Read result
await readBuf.mapAsync(GPUMapMode.READ);
const result = new Float32Array(readBuf.getMappedRange());
console.log(result[0]);  // 3.0
readBuf.unmap();
```

# OPTIMIZATION PATTERNS
```
1. MEMORY COALESCING
   BAD:  thread i accesses memory[i * stride]  → strided, many transactions
   GOOD: thread i accesses memory[i]            → coalesced, one transaction

2. AVOID WARP DIVERGENCE
   BAD:  if (threadIdx.x % 2 == 0) { path_A } else { path_B }
         → threads in same warp take different paths; both execute serially
   GOOD: separate kernel for each path, or restructure data to avoid branching

3. OCCUPANCY TUNING
   Use cudaOccupancyMaxPotentialBlockSize() to find optimal block size
   More warps in flight = better latency hiding
   But: large shared memory or register usage reduces occupancy

4. PINNED (PAGE-LOCKED) HOST MEMORY
   cudaMallocHost() instead of malloc()
   Enables async transfers: cudaMemcpyAsync() overlaps transfer with compute
   Up to 2x bandwidth improvement

5. STREAM PARALLELISM
   stream1: kernelA<<<..., stream1>>>()
   stream2: cudaMemcpyAsync(..., stream2)
   → compute and memory transfer overlap
   → multiple independent kernels run concurrently

6. TENSOR CORE UTILIZATION (Ampere/Hopper)
   Use cuBLAS or cuDNN — they use Tensor Cores automatically
   Manual: use wmma API with FP16 matrices
   Requires matrix dimensions divisible by 16
```

# PROFILING TOOLS
```
CUDA:
  Nsight Compute: kernel-level profiling (roofline, memory throughput, occupancy)
  Nsight Systems: system-level timeline (kernel launch overhead, CPU/GPU overlap)
  nvprof (legacy): quick command-line profiling

WebGPU:
  Chrome DevTools → GPU tab (experimental)
  gpuinfo.js: adapter capabilities

KEY METRICS TO CHECK:
  Memory bandwidth utilization: actual / theoretical peak (e.g., 900/2000 GB/s)
  Compute utilization: actual TFLOPS / peak TFLOPS
  SM occupancy: active warps / max warps per SM
  L2 hit rate: > 80% is good
  Divergent branches: should be near 0
```
