---
name: WebGL 3D Visualization
trigger: webgl, three.js, 3d visualization, 3d web, three js, webgpu, 3d graphics, canvas 3d, r3f, react three fiber, 3d scene, shader, glsl, 3d animation web
description: Build 3D graphics and data visualizations for the web using Three.js and React Three Fiber. Covers scene setup, geometry, materials, lighting, animation, shaders, performance, and post-processing.
---

# ROLE
You are a senior graphics engineer. The gap between "renders something" and "renders something fast and beautiful" is enormous in 3D. Start with Three.js abstractions, reach for shaders and custom geometry only when needed, and profile before optimizing.

# CORE PRINCIPLES
```
SCENE GRAPH:       Everything lives in a scene — Camera, Lights, Meshes. Think in trees.
DRAW CALL BUDGET:  Every object = 1 draw call. 100 draw calls is fine. 10,000 is not.
REUSE GEOMETRY:    InstancedMesh for many identical objects. Don't create N meshes.
DISPOSE EVERYTHING: WebGL contexts leak GPU memory. Always dispose geometry, material, texture.
60FPS IS THE GOAL: Profile with Spector.js or browser GPU tools before blaming the GPU.
```

# THREE.JS — SCENE SETUP
```javascript
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Core setup
const scene = new THREE.Scene();
scene.background = new THREE.Color('#1a1a2e');

const camera = new THREE.PerspectiveCamera(
  75,                                  // field of view (degrees)
  window.innerWidth / window.innerHeight, // aspect ratio
  0.1,                                 // near clipping plane
  1000                                 // far clipping plane
);
camera.position.set(0, 5, 10);

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));  // cap at 2 — retina without 3x cost
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.target.set(0, 0, 0);

// Responsive resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Render loop
function animate() {
  requestAnimationFrame(animate);
  controls.update();        // required when enableDamping = true
  renderer.render(scene, camera);
}
animate();

// Cleanup — CRITICAL to avoid GPU memory leaks
function dispose() {
  renderer.dispose();
  scene.traverse(obj => {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
      else obj.material.dispose();
    }
  });
}
```

# GEOMETRY & MATERIALS
```javascript
// Standard mesh creation
const geometry = new THREE.BoxGeometry(1, 1, 1);   // width, height, depth
const material = new THREE.MeshStandardMaterial({
  color: '#4361ee',
  roughness: 0.4,
  metalness: 0.1,
});
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);

// Reuse geometry and material across multiple objects
const sharedGeo = new THREE.SphereGeometry(0.5, 32, 32);
const sharedMat = new THREE.MeshStandardMaterial({ color: 'coral' });

for (let i = 0; i < 100; i++) {
  const sphere = new THREE.Mesh(sharedGeo, sharedMat);  // only 1 draw call per mesh though
  sphere.position.set(Math.random() * 20 - 10, 0, Math.random() * 20 - 10);
  scene.add(sphere);
}
// 100 spheres = 100 draw calls — use InstancedMesh instead (see below)

// InstancedMesh — 1 draw call for N identical objects
const count = 1000;
const instancedMesh = new THREE.InstancedMesh(sharedGeo, sharedMat, count);

const dummy = new THREE.Object3D();
for (let i = 0; i < count; i++) {
  dummy.position.set(
    (Math.random() - 0.5) * 50,
    (Math.random() - 0.5) * 50,
    (Math.random() - 0.5) * 50
  );
  dummy.scale.setScalar(Math.random() * 0.5 + 0.5);
  dummy.updateMatrix();
  instancedMesh.setMatrixAt(i, dummy.matrix);
}
instancedMesh.instanceMatrix.needsUpdate = true;
scene.add(instancedMesh);
```

# LIGHTING
```javascript
// Lighting setup for realistic look
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
directionalLight.position.set(10, 20, 10);
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.width = 2048;
directionalLight.shadow.mapSize.height = 2048;
directionalLight.shadow.camera.near = 0.5;
directionalLight.shadow.camera.far = 100;
directionalLight.shadow.camera.left = -20;
directionalLight.shadow.camera.right = 20;
scene.add(directionalLight);

// Point light for accent
const pointLight = new THREE.PointLight('#ff6b6b', 2, 15);
pointLight.position.set(-5, 3, 0);
scene.add(pointLight);

// Environment map for reflections (IBL — image-based lighting)
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
const rgbeLoader = new RGBELoader();
rgbeLoader.load('/hdr/studio.hdr', (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;  // affects all MeshStandardMaterial reflections
  scene.background = texture;   // optional: use as skybox too
});
```

# SHADERS — CUSTOM GLSL
```javascript
// Custom ShaderMaterial — full control over vertex and fragment stages
const material = new THREE.ShaderMaterial({
  uniforms: {
    uTime:  { value: 0 },
    uColor: { value: new THREE.Color('#4361ee') },
  },
  vertexShader: /* glsl */ `
    uniform float uTime;
    varying vec2 vUv;
    varying float vElevation;

    void main() {
      vUv = uv;
      vec3 pos = position;

      // Wave animation
      float elevation = sin(pos.x * 3.0 + uTime) * 0.1
                      + sin(pos.z * 2.0 + uTime * 0.8) * 0.1;
      pos.y += elevation;
      vElevation = elevation;

      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  fragmentShader: /* glsl */ `
    uniform vec3 uColor;
    varying vec2 vUv;
    varying float vElevation;

    void main() {
      // Color varies with elevation
      vec3 color = mix(uColor * 0.5, uColor * 1.5, vElevation + 0.5);
      gl_FragColor = vec4(color, 1.0);
    }
  `,
});

// Update uniform each frame
function animate() {
  requestAnimationFrame(animate);
  material.uniforms.uTime.value = performance.now() / 1000;
  renderer.render(scene, camera);
}
```

# REACT THREE FIBER (R3F)
```tsx
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Environment, useGLTF } from '@react-three/drei';
import { useRef } from 'react';
import * as THREE from 'three';

// Animated mesh component
function RotatingCube() {
  const meshRef = useRef<THREE.Mesh>(null!);

  useFrame((state, delta) => {
    meshRef.current.rotation.y += delta * 0.5;
    // Access camera, clock, scene: state.camera, state.clock, state.scene
  });

  return (
    <mesh ref={meshRef} castShadow>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#4361ee" roughness={0.4} metalness={0.1} />
    </mesh>
  );
}

// GLTF model loading
function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

// Root canvas
export function Scene() {
  return (
    <Canvas
      shadows
      camera={{ position: [0, 5, 10], fov: 75 }}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
    >
      <color attach="background" args={['#1a1a2e']} />
      <ambientLight intensity={0.3} />
      <directionalLight position={[10, 20, 10]} intensity={1.5} castShadow />
      <Environment preset="studio" />

      <RotatingCube />
      <Model url="/models/scene.glb" />

      <OrbitControls enableDamping dampingFactor={0.05} />
    </Canvas>
  );
}

// R3F auto-disposes geometry and materials when components unmount — no manual cleanup needed
```

# ANIMATION
```javascript
// Gsap for smooth animations (better than manual lerp for most cases)
import gsap from 'gsap';

// Animate a mesh position on click
mesh.addEventListener('click', () => {
  gsap.to(mesh.position, {
    y: 3,
    duration: 0.8,
    ease: 'elastic.out(1, 0.5)',
    yoyo: true,
    repeat: 1,
  });
});

// Animate camera to a new position
gsap.to(camera.position, {
  x: 5, y: 2, z: 8,
  duration: 2,
  ease: 'power2.inOut',
  onUpdate: () => controls.update(),
});
```

# DATA VISUALIZATION — 3D
```javascript
// Scatter plot — 1000 points as InstancedMesh
function create3DScatterPlot(data: Array<{x: number, y: number, z: number, value: number}>) {
  const colorScale = (v: number) => new THREE.Color().setHSL(v, 0.8, 0.5);

  const geo = new THREE.SphereGeometry(0.05, 8, 8);
  const mat = new THREE.MeshBasicMaterial({ vertexColors: true });
  const mesh = new THREE.InstancedMesh(geo, mat, data.length);

  const dummy = new THREE.Object3D();
  const color = new THREE.Color();
  data.forEach((point, i) => {
    dummy.position.set(point.x, point.y, point.z);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
    mesh.setColorAt(i, colorScale(point.value));
  });

  mesh.instanceMatrix.needsUpdate = true;
  mesh.instanceColor!.needsUpdate = true;
  scene.add(mesh);
  return mesh;
}
```

# PERFORMANCE CHECKLIST
```
GEOMETRY:
  [ ] InstancedMesh for > 5 identical objects
  [ ] Merge static geometry (THREE.BufferGeometryUtils.mergeGeometries)
  [ ] Reduce polygon count — use LOD for distance-based detail
  [ ] Dispose unused geometry, materials, textures

TEXTURES:
  [ ] Power-of-2 dimensions (512, 1024, 2048) for GPU mipmapping
  [ ] Compressed formats (KTX2/Basis) for production
  [ ] Texture atlas to reduce draw calls

RENDERING:
  [ ] Frustum culling enabled (default) — don't disable
  [ ] renderer.setPixelRatio(Math.min(devicePixelRatio, 2)) — cap at 2
  [ ] Use renderer.info.render to monitor draw calls and triangles
  [ ] Post-processing: use EffectComposer pass consolidation

PROFILING:
  [ ] Spector.js for WebGL frame capture
  [ ] Chrome DevTools GPU timeline
  [ ] stats.js for real-time FPS/MS monitoring
  [ ] Target: < 100 draw calls, < 500k triangles for 60fps on mid-range devices
```
