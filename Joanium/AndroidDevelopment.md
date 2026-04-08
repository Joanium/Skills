---
name: Android Development
trigger: android app, android development, kotlin android, jetpack compose, android studio, android fragments, android viewmodel, android architecture, material design android, android sdk
description: Build modern Android applications using Kotlin, Jetpack Compose, and Android Architecture Components. Covers project structure, UI, state management, navigation, networking, and Play Store deployment.
---

# ROLE
You are a senior Android engineer. Your job is to build well-architected, performant, and maintainable Android applications using modern Kotlin and Jetpack libraries. Android has a fragmented ecosystem — consistency and lifecycle-awareness are survival skills.

# CORE PRINCIPLES
```
LIFECYCLE-AWARE:   Everything in Android can be destroyed. Design accordingly.
UNIDIRECTIONAL:    Data flows down (state), events flow up (actions). Never reverse.
COMPOSE-FIRST:     New UI = Jetpack Compose. Views/XML only for legacy migration.
SINGLE ACTIVITY:   One Activity + Navigation Component. Avoid multi-Activity patterns.
REPOSITORY:        ViewModels don't know where data comes from. Only repositories do.
```

# PROJECT STRUCTURE
```
app/
├── src/main/
│   ├── java/com/example/app/
│   │   ├── data/
│   │   │   ├── local/          # Room DAOs, entities, database
│   │   │   ├── remote/         # Retrofit services, DTOs
│   │   │   └── repository/     # Repository implementations
│   │   ├── domain/
│   │   │   ├── model/          # Business models (not DTOs)
│   │   │   └── usecase/        # Use cases / interactors
│   │   ├── ui/
│   │   │   ├── feature_name/
│   │   │   │   ├── FeatureScreen.kt      # Composable
│   │   │   │   └── FeatureViewModel.kt   # ViewModel
│   │   │   └── theme/          # Color, Typography, Theme
│   │   ├── di/                 # Hilt modules
│   │   └── MainActivity.kt
│   └── res/
│       ├── values/             # strings, colors, dimens
│       └── drawable/
└── build.gradle.kts
```

# ARCHITECTURE — MVVM + CLEAN
```kotlin
// ViewModel — holds state, handles user events
@HiltViewModel
class PostsViewModel @Inject constructor(
    private val getPostsUseCase: GetPostsUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow<PostsUiState>(PostsUiState.Loading)
    val uiState: StateFlow<PostsUiState> = _uiState.asStateFlow()

    init {
        loadPosts()
    }

    fun loadPosts() {
        viewModelScope.launch {
            _uiState.value = PostsUiState.Loading
            getPostsUseCase()
                .onSuccess { posts -> _uiState.value = PostsUiState.Success(posts) }
                .onFailure { err -> _uiState.value = PostsUiState.Error(err.message ?: "Unknown error") }
        }
    }
}

sealed interface PostsUiState {
    data object Loading : PostsUiState
    data class Success(val posts: List<Post>) : PostsUiState
    data class Error(val message: String) : PostsUiState
}

// Composable Screen — observes state, emits events
@Composable
fun PostsScreen(viewModel: PostsViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    when (val state = uiState) {
        is PostsUiState.Loading -> LoadingIndicator()
        is PostsUiState.Success -> PostsList(posts = state.posts)
        is PostsUiState.Error   -> ErrorScreen(message = state.message, onRetry = viewModel::loadPosts)
    }
}
```

# JETPACK COMPOSE PATTERNS
```kotlin
// Stateless composable — easy to test and preview
@Composable
fun PostCard(
    post: Post,
    onLike: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = post.title, style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = post.body, style = MaterialTheme.typography.bodyMedium)
            IconButton(onClick = { onLike(post.id) }) {
                Icon(Icons.Default.Favorite, contentDescription = "Like")
            }
        }
    }
}

// LazyColumn for lists (RecyclerView equivalent)
@Composable
fun PostsList(posts: List<Post>) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(posts, key = { it.id }) { post ->
            PostCard(post = post, onLike = { /* handle */ })
        }
    }
}

// Side effects — launch once
LaunchedEffect(Unit) {
    viewModel.events.collect { event ->
        when (event) {
            is UiEvent.ShowSnackbar -> snackbarHostState.showSnackbar(event.message)
            is UiEvent.Navigate     -> navController.navigate(event.route)
        }
    }
}
```

# NAVIGATION
```kotlin
// NavGraph setup
@Composable
fun AppNavGraph(navController: NavHostController) {
    NavHost(navController = navController, startDestination = "posts") {
        composable("posts") {
            PostsScreen(onNavigateToDetail = { id ->
                navController.navigate("post_detail/$id")
            })
        }
        composable(
            route = "post_detail/{postId}",
            arguments = listOf(navArgument("postId") { type = NavType.StringType })
        ) { backStackEntry ->
            val postId = backStackEntry.arguments?.getString("postId") ?: return@composable
            PostDetailScreen(postId = postId)
        }
    }
}
```

# ROOM DATABASE
```kotlin
// Entity
@Entity(tableName = "posts")
data class PostEntity(
    @PrimaryKey val id: String,
    val title: String,
    val body: String,
    val createdAt: Long = System.currentTimeMillis()
)

// DAO
@Dao
interface PostDao {
    @Query("SELECT * FROM posts ORDER BY createdAt DESC")
    fun getAllPosts(): Flow<List<PostEntity>>

    @Upsert
    suspend fun upsertPost(post: PostEntity)

    @Delete
    suspend fun deletePost(post: PostEntity)
}

// Database
@Database(entities = [PostEntity::class], version = 1, exportSchema = true)
abstract class AppDatabase : RoomDatabase() {
    abstract fun postDao(): PostDao
}
```

# DEPENDENCY INJECTION (HILT)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app_db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun providePostDao(db: AppDatabase): PostDao = db.postDao()
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    @Provides @Singleton
    fun providePostService(retrofit: Retrofit): PostApiService =
        retrofit.create(PostApiService::class.java)
}
```

# PERMISSIONS
```kotlin
// Runtime permissions — always request at point of need
val cameraPermission = rememberPermissionState(Manifest.permission.CAMERA)

Button(onClick = {
    when {
        cameraPermission.status.isGranted -> openCamera()
        cameraPermission.status.shouldShowRationale -> showRationale()
        else -> cameraPermission.launchPermissionRequest()
    }
}) { Text("Take Photo") }
```

# BACKGROUND WORK — WORKMANAGER
```kotlin
// For durable background tasks (sync, upload, cleanup)
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = try {
        syncRepository.syncAll()
        Result.success()
    } catch (e: Exception) {
        if (runAttemptCount < 3) Result.retry() else Result.failure()
    }
}

// Schedule periodic sync
val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)
    .setConstraints(Constraints(requiredNetworkType = NetworkType.CONNECTED))
    .build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "sync", ExistingPeriodicWorkPolicy.KEEP, syncRequest
)
```

# PERFORMANCE CHECKLIST
```
[ ] Use remember / derivedStateOf to avoid recomposition
[ ] Key LazyColumn items by stable ID (not position)
[ ] Profile with Layout Inspector and Composition tracing
[ ] Avoid reading State in composition scope unnecessarily — use lambda reads
[ ] Use coil-compose for image loading (never decode bitmaps on main thread)
[ ] ProGuard / R8 enabled for release builds
[ ] Enable baseline profiles for startup performance
```

# BUILD CONFIG
```kotlin
// build.gradle.kts
android {
    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    buildFeatures { compose = true; buildConfig = true }
}
```
