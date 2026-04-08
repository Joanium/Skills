---
name: SwiftUI iOS Development
trigger: swiftui, ios development, swift app, xcode, ios app, swift ui, ios architecture, swift async, combine swiftui, swiftdata, ios design patterns
description: Build modern iOS applications using SwiftUI, Swift concurrency, and Apple frameworks. Covers app architecture, navigation, state management, data persistence, networking, and App Store submission.
---

# ROLE
You are a senior iOS engineer. Your job is to build polished, performant, and maintainable iOS apps using SwiftUI and modern Swift. Apple's ecosystem rewards those who follow its patterns — fight the framework and you'll lose.

# CORE PRINCIPLES
```
DECLARATIVE UI:    SwiftUI describes what the UI looks like, not how to draw it.
SOURCE OF TRUTH:   One owner per piece of state. Never duplicate, never sync manually.
VALUE TYPES:       Prefer structs over classes. Use classes only for shared mutable state.
ASYNC/AWAIT:       Modern concurrency everywhere. Combine only for existing codebases.
OBSERVABLE:        @Observable (iOS 17+) or ObservableObject for shared app state.
```

# PROJECT STRUCTURE
```
MyApp/
├── App/
│   └── MyApp.swift          # @main entry point
├── Features/
│   ├── Posts/
│   │   ├── PostsView.swift
│   │   ├── PostDetailView.swift
│   │   └── PostsViewModel.swift
│   └── Settings/
│       └── SettingsView.swift
├── Data/
│   ├── Models/              # Codable structs
│   ├── Services/            # API clients, persistence
│   └── Repositories/        # Abstractions over services
├── Core/
│   ├── Extensions/
│   ├── Components/          # Reusable UI components
│   └── Utilities/
└── Resources/
    ├── Assets.xcassets
    └── Localizable.xcstrings
```

# STATE MANAGEMENT
```swift
// @Observable (iOS 17+) — preferred
@Observable
final class PostsViewModel {
    var posts: [Post] = []
    var isLoading = false
    var errorMessage: String?

    private let repository: PostRepository

    init(repository: PostRepository = .live) {
        self.repository = repository
    }

    func loadPosts() async {
        isLoading = true
        defer { isLoading = false }
        do {
            posts = try await repository.fetchPosts()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// In View
struct PostsView: View {
    @State private var viewModel = PostsViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView()
            } else if let error = viewModel.errorMessage {
                ErrorView(message: error, onRetry: { Task { await viewModel.loadPosts() } })
            } else {
                PostsList(posts: viewModel.posts)
            }
        }
        .task { await viewModel.loadPosts() }
    }
}

// Older (iOS 14/15) — ObservableObject
@MainActor
final class PostsViewModelLegacy: ObservableObject {
    @Published var posts: [Post] = []
    @Published var isLoading = false
}
```

# NAVIGATION
```swift
// NavigationStack (iOS 16+) — programmatic navigation
struct AppView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            PostsView(path: $path)
                .navigationDestination(for: Post.self) { post in
                    PostDetailView(post: post)
                }
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .settings: SettingsView()
                    case .profile(let id): ProfileView(userId: id)
                    }
                }
        }
    }
}

// Navigate by pushing typed values
Button("Open Post") {
    path.append(post)           // goes to PostDetailView
    path.append(AppRoute.settings) // goes to SettingsView
}

// Tab-based navigation
struct RootView: View {
    var body: some View {
        TabView {
            PostsView().tabItem { Label("Posts", systemImage: "doc.text") }
            ProfileView().tabItem { Label("Profile", systemImage: "person") }
        }
    }
}
```

# NETWORKING — ASYNC/AWAIT
```swift
// API Client
struct APIClient {
    let baseURL: URL
    let session: URLSession

    func fetch<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        let request = endpoint.urlRequest(baseURL: baseURL)
        let (data, response) = try await session.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.httpError(statusCode: http.statusCode)
        }
        return try JSONDecoder.iso8601.decode(T.self, from: data)
    }
}

extension JSONDecoder {
    static let iso8601: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        d.dateDecodingStrategy = .iso8601
        return d
    }()
}

enum APIError: LocalizedError {
    case invalidResponse
    case httpError(statusCode: Int)
    var errorDescription: String? {
        switch self {
        case .invalidResponse: "Received an invalid response from the server."
        case .httpError(let code): "Server returned error \(code)."
        }
    }
}
```

# DATA PERSISTENCE — SWIFTDATA
```swift
// Model (iOS 17+)
@Model
final class Post {
    var id: String
    var title: String
    var body: String
    var createdAt: Date

    init(id: String, title: String, body: String) {
        self.id = id
        self.title = title
        self.body = body
        self.createdAt = .now
    }
}

// Setup
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: Post.self)
    }
}

// Query in views
struct PostsListView: View {
    @Query(sort: \Post.createdAt, order: .reverse) var posts: [Post]
    @Environment(\.modelContext) var context

    var body: some View {
        List(posts) { post in
            Text(post.title)
                .swipeActions { Button("Delete", role: .destructive) { context.delete(post) } }
        }
    }
}
```

# SWIFTUI COMPONENT PATTERNS
```swift
// Prefer environment for dependency injection over explicit passing
struct MyView: View {
    @Environment(\.apiClient) var apiClient
    @Environment(AuthManager.self) var authManager
}

// ViewModifier for reusable styling
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(16)
            .background(.background)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .shadow(color: .black.opacity(0.08), radius: 8, y: 4)
    }
}

extension View {
    func cardStyle() -> some View { modifier(CardStyle()) }
}

// AsyncImage for remote images
AsyncImage(url: URL(string: post.imageURL)) { phase in
    switch phase {
    case .success(let image): image.resizable().aspectRatio(contentMode: .fill)
    case .failure:            Image(systemName: "photo").foregroundStyle(.secondary)
    case .empty:              ProgressView()
    @unknown default:         EmptyView()
    }
}
.frame(height: 200)
.clipped()
```

# ACCESSIBILITY
```swift
// Always add accessibility labels and traits
Image(systemName: "heart.fill")
    .accessibilityLabel("Liked")
    .accessibilityAddTraits(.isButton)

// Group related elements
VStack {
    Text(post.title)
    Text(post.body)
}
.accessibilityElement(children: .combine)

// Dynamic Type — always use .font(.body) etc., never fixed sizes
Text("Hello").font(.title2)  ✓
Text("Hello").font(.system(size: 22)) ✗
```

# PERFORMANCE CHECKLIST
```
[ ] Heavy work off MainActor — use async let or Task for concurrent fetches
[ ] Use @MainActor on ViewModels to avoid threading issues
[ ] Equatable structs for list items to avoid unnecessary diff work
[ ] Instruments: Time Profiler for CPU, Allocations for memory
[ ] Avoid large opaque types in body — break into sub-views
[ ] Lazy stacks (LazyVStack/LazyHStack) for long scrolling content
[ ] Images: use appropriate resolution assets in xcassets
```

# APP STORE CHECKLIST
```
[ ] Privacy manifest (PrivacyInfo.xcprivacy) for required reason APIs
[ ] App Privacy "nutrition labels" filled accurately in App Store Connect
[ ] NSPhotoLibraryUsageDescription and all permission strings in Info.plist
[ ] Support all device sizes — test on smallest (SE) and largest (Pro Max)
[ ] VoiceOver tested with screen reader on
[ ] Minimum deployment target set appropriately
[ ] Release build tested on real device (not Simulator)
```
