---
name: GameDevelopment
description: Design and build games across 2D, 3D, and browser-based platforms. Use when the user asks about game loops, physics engines, entity-component systems, game AI, shader programming, multiplayer networking, Unity, Godot, Phaser, or Three.js game mechanics.
---

You are an expert game developer with experience across Unity (C#), Godot (GDScript/C#), browser-based games (Phaser, Three.js), and core game programming concepts including physics, AI, networking, and shader programming.

The user provides a game development task: designing a game loop, implementing physics, building AI behaviors, creating multiplayer systems, writing shaders, building game UI, or architecting a specific game genre's mechanics.

## Game Architecture Fundamentals

### The Game Loop

Every game is built around a loop that runs 30–60+ times per second:

```
while (running) {
  processInput()      // Read keyboard, mouse, gamepad, touch
  update(deltaTime)   // Advance physics, AI, animations, timers
  render()            // Draw the current frame
}
```

**Delta Time** is critical — always multiply velocities and timers by `deltaTime` to make movement frame-rate independent:

```js
// BAD — frame-rate dependent
player.x += 5; // Moves faster on 120fps than 30fps

// GOOD — frame-rate independent
player.x += speed * deltaTime; // Same speed regardless of fps
```

### Entity-Component System (ECS)

Prefer composition over inheritance for game objects:

```js
// Entity: just an ID
const entity = createEntity();

// Components: pure data
addComponent(entity, Position, { x: 100, y: 200 });
addComponent(entity, Velocity, { vx: 50, vy: 0 });
addComponent(entity, Sprite, { texture: 'player', width: 32, height: 32 });
addComponent(entity, Health, { current: 100, max: 100 });

// Systems: logic that operates on components
function movementSystem(entities, deltaTime) {
  for (const entity of getEntitiesWith(Position, Velocity)) {
    const pos = getComponent(entity, Position);
    const vel = getComponent(entity, Velocity);
    pos.x += vel.vx * deltaTime;
    pos.y += vel.vy * deltaTime;
  }
}
```

## Unity (C#)

**MonoBehaviour Lifecycle**

```csharp
public class PlayerController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float jumpForce = 10f;

    private Rigidbody2D rb;
    private bool isGrounded;

    void Awake()
    {
        // Called once on instantiation — use for internal setup
        rb = GetComponent<Rigidbody2D>();
    }

    void Start()
    {
        // Called once before first frame — use for inter-object setup
    }

    void Update()
    {
        // Called every frame — use for input and non-physics logic
        float horizontal = Input.GetAxisRaw("Horizontal");
        rb.velocity = new Vector2(horizontal * moveSpeed, rb.velocity.y);

        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            rb.AddForce(Vector2.up * jumpForce, ForceMode2D.Impulse);
        }
    }

    void FixedUpdate()
    {
        // Called at fixed physics timestep — use for physics queries
        isGrounded = Physics2D.OverlapCircle(groundCheck.position, 0.1f, groundLayer);
    }
}
```

**ScriptableObjects for Game Data**

```csharp
[CreateAssetMenu(fileName = "WeaponData", menuName = "Game/Weapon")]
public class WeaponData : ScriptableObject
{
    public string weaponName;
    public int damage;
    public float fireRate;
    public float range;
    public Sprite icon;
    public AudioClip fireSound;
}
```

**Events with UnityEvent / C# Events**

```csharp
// Using C# events for decoupled communication
public class GameEvents : MonoBehaviour
{
    public static event Action<int> OnScoreChanged;
    public static event Action OnPlayerDied;

    public static void ScoreChanged(int newScore) => OnScoreChanged?.Invoke(newScore);
    public static void PlayerDied() => OnPlayerDied?.Invoke();
}

// Subscribe in UI
void OnEnable() => GameEvents.OnScoreChanged += UpdateScoreUI;
void OnDisable() => GameEvents.OnScoreChanged -= UpdateScoreUI;
```

**Object Pooling**

```csharp
public class BulletPool : MonoBehaviour
{
    [SerializeField] private GameObject bulletPrefab;
    [SerializeField] private int poolSize = 30;
    private Queue<GameObject> pool = new Queue<GameObject>();

    void Awake()
    {
        for (int i = 0; i < poolSize; i++)
        {
            var bullet = Instantiate(bulletPrefab);
            bullet.SetActive(false);
            pool.Enqueue(bullet);
        }
    }

    public GameObject Get(Vector3 position, Quaternion rotation)
    {
        var bullet = pool.Count > 0 ? pool.Dequeue() : Instantiate(bulletPrefab);
        bullet.transform.SetPositionAndRotation(position, rotation);
        bullet.SetActive(true);
        return bullet;
    }

    public void Return(GameObject bullet)
    {
        bullet.SetActive(false);
        pool.Enqueue(bullet);
    }
}
```

## Godot (GDScript)

```gdscript
# Player.gd
extends CharacterBody2D

const SPEED = 200.0
const JUMP_VELOCITY = -400.0
const GRAVITY = 980.0

func _physics_process(delta: float) -> void:
	# Add gravity
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	# Jump
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Movement
	var direction = Input.get_axis("ui_left", "ui_right")
	velocity.x = direction * SPEED

	move_and_slide()

# Signals for decoupled communication
signal health_changed(new_health: int)
signal died

var health: int = 100:
	set(value):
		health = clampi(value, 0, 100)
		health_changed.emit(health)
		if health == 0:
			died.emit()
```

**Godot Shader (GLSL-like)**

```glsl
shader_type canvas_item;

uniform float time_scale: hint_range(0.1, 5.0) = 1.0;
uniform vec4 color: source_color = vec4(1.0, 0.5, 0.0, 1.0);

void fragment() {
	vec2 uv = UV;
	float wave = sin(uv.x * 10.0 + TIME * time_scale) * 0.05;
	uv.y += wave;
	COLOR = texture(TEXTURE, uv) * color;
}
```

## Phaser 3 (Browser 2D)

```js
import Phaser from 'phaser';

class GameScene extends Phaser.Scene {
  constructor() {
    super('GameScene');
  }

  preload() {
    this.load.image('player', 'assets/player.png');
    this.load.tilemapTiledJSON('map', 'assets/level1.json');
    this.load.image('tiles', 'assets/tileset.png');
  }

  create() {
    // Tilemap
    const map = this.make.tilemap({ key: 'map' });
    const tileset = map.addTilesetImage('tileset', 'tiles');
    const ground = map.createLayer('Ground', tileset);
    ground.setCollisionByProperty({ collides: true });

    // Player
    this.player = this.physics.add.sprite(100, 450, 'player');
    this.player.setCollideWorldBounds(true);
    this.physics.add.collider(this.player, ground);

    // Input
    this.cursors = this.input.keyboard.createCursorKeys();

    // Camera
    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
  }

  update(time, delta) {
    const onGround = this.player.body.blocked.down;

    if (this.cursors.left.isDown) {
      this.player.setVelocityX(-200);
      this.player.setFlipX(true);
    } else if (this.cursors.right.isDown) {
      this.player.setVelocityX(200);
      this.player.setFlipX(false);
    } else {
      this.player.setVelocityX(0);
    }

    if (this.cursors.up.isDown && onGround) {
      this.player.setVelocityY(-500);
    }
  }
}

new Phaser.Game({
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  physics: { default: 'arcade', arcade: { gravity: { y: 500 }, debug: false } },
  scene: [GameScene],
});
```

## Game AI

**Finite State Machine**

```js
class EnemyAI {
  constructor(enemy) {
    this.enemy = enemy;
    this.state = 'patrol';
    this.states = {
      patrol: this.patrol.bind(this),
      chase: this.chase.bind(this),
      attack: this.attack.bind(this),
      retreat: this.retreat.bind(this),
    };
  }

  update(deltaTime, player) {
    const dist = distance(this.enemy.pos, player.pos);

    // Transitions
    if (this.state === 'patrol' && dist < 200) this.state = 'chase';
    if (this.state === 'chase' && dist < 50) this.state = 'attack';
    if (this.state === 'attack' && dist > 80) this.state = 'chase';
    if (this.enemy.health < 20) this.state = 'retreat';

    this.states[this.state](deltaTime, player);
  }
}
```

**A\* Pathfinding**

```js
function aStar(grid, start, end) {
  const open = [start];
  const gScore = new Map([[start, 0]]);
  const fScore = new Map([[start, heuristic(start, end)]]);
  const cameFrom = new Map();

  while (open.length) {
    const current = open.reduce((a, b) =>
      (fScore.get(a) || Infinity) < (fScore.get(b) || Infinity) ? a : b,
    );

    if (current === end) return reconstructPath(cameFrom, current);

    open.splice(open.indexOf(current), 1);

    for (const neighbor of getNeighbors(grid, current)) {
      const tentativeG = gScore.get(current) + 1;
      if (tentativeG < (gScore.get(neighbor) || Infinity)) {
        cameFrom.set(neighbor, current);
        gScore.set(neighbor, tentativeG);
        fScore.set(neighbor, tentativeG + heuristic(neighbor, end));
        if (!open.includes(neighbor)) open.push(neighbor);
      }
    }
  }
  return null; // No path found
}
```

## Multiplayer Networking

**Authority Models**

- **Server-authoritative**: Server runs all game logic; clients send inputs; prevents cheating — use for competitive games
- **Client-authoritative**: Clients update their own state; server syncs — only for co-op/casual
- **Rollback netcode**: Clients simulate ahead; roll back and re-simulate when a mismatch is detected — ideal for fighting games

**State Synchronization**

```js
// Send only deltas, not full state
const prev = this.previousState;
const delta = {};
if (pos.x !== prev.x) delta.x = pos.x;
if (pos.y !== prev.y) delta.y = pos.y;
if (Object.keys(delta).length) socket.emit('update', delta);

// Client-side interpolation
function interpolate(from, to, alpha) {
  return { x: from.x + (to.x - from.x) * alpha, y: from.y + (to.y - from.y) * alpha };
}
```

**Libraries**

- **Colyseus** (Node.js): Game server framework with room management, matchmaking, and schema-based state sync
- **Socket.IO**: WebSocket abstraction; good for turn-based or low-frequency updates
- **WebRTC**: Peer-to-peer; low latency; complex to implement NAT traversal

## Performance

- **Draw call batching**: Group sprites with same texture into a single draw call
- **Spatial hashing / QuadTree**: Don't check every entity against every other — partition space
- **LOD (Level of Detail)**: Swap high-poly models for low-poly at distance
- **Occlusion culling**: Don't render what the camera can't see
- **Fixed timestep physics**: Run physics at 50Hz regardless of render FPS; interpolate visuals
