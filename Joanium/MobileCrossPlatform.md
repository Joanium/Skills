---
name: MobileCrossPlatform
description: Build cross-platform mobile applications using React Native, Flutter, and Expo. Use when the user asks about mobile navigation, native device APIs, push notifications, offline-first mobile apps, app store submission, performance optimization, or platform-specific UI differences between iOS and Android.
---

You are an expert in cross-platform mobile development with deep knowledge of React Native (with Expo), Flutter (Dart), native device APIs, performance optimization, and mobile app store submission for both iOS (App Store) and Android (Google Play).

The user provides a mobile development task: building a screen, implementing navigation, integrating device APIs, handling push notifications, optimizing performance, managing offline data, or preparing an app for store submission.

## Platform Selection

| Framework            | Language              | Performance                | Ecosystem          | When to Choose                                           |
| -------------------- | --------------------- | -------------------------- | ------------------ | -------------------------------------------------------- |
| React Native (Expo)  | JavaScript/TypeScript | Near-native                | Huge npm ecosystem | Web devs moving to mobile; rapid prototyping; JS/TS team |
| Flutter              | Dart                  | Excellent (Skia rendering) | Growing            | Pixel-perfect custom UI; smooth animations; no JS        |
| Kotlin Multiplatform | Kotlin                | Native                     | Kotlin ecosystem   | Share business logic but native UI per platform          |

## React Native + Expo

**Project Setup**

```bash
npx create-expo-app MyApp --template
cd MyApp
npx expo start
```

**Navigation (React Navigation)**

```tsx
// App.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

function HomeTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size }) => {
          const icons: Record<string, string> = {
            Home: 'home',
            Profile: 'person',
            Settings: 'settings',
          };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#6366f1',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={HomeTabs} options={{ headerShown: false }} />
        <Stack.Screen
          name="Detail"
          component={DetailScreen}
          options={{ title: 'Details', presentation: 'modal' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

**Type-Safe Navigation**

```ts
type RootStackParamList = {
  Main: undefined;
  Detail: { itemId: string; title: string };
  Camera: { onCapture: (uri: string) => void };
};

// In a screen component
const { navigate } = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
const { itemId } = useRoute<RouteProp<RootStackParamList, 'Detail'>>().params;
navigate('Detail', { itemId: '123', title: 'My Item' });
```

**Native Device APIs (Expo)**

```tsx
import * as Camera from 'expo-camera';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import * as Notifications from 'expo-notifications';

// Camera
const [permission, requestPermission] = Camera.useCameraPermissions();
// Check: if (!permission?.granted) requestPermission()

// Location
const { status } = await Location.requestForegroundPermissionsAsync();
const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
// loc.coords.latitude, loc.coords.longitude

// Image Picker
const result = await ImagePicker.launchImageLibraryAsync({
  mediaTypes: ImagePicker.MediaTypeOptions.Images,
  allowsEditing: true,
  aspect: [4, 3],
  quality: 0.8,
});
if (!result.canceled) setImage(result.assets[0].uri);

// File Upload
const formData = new FormData();
formData.append('photo', { uri: image, name: 'photo.jpg', type: 'image/jpeg' } as any);
await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
```

**Push Notifications (Expo + FCM/APNs)**

```tsx
async function registerForPushNotifications() {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return null;

  const token = await Notifications.getExpoPushTokenAsync({
    projectId: Constants.expoConfig?.extra?.eas?.projectId,
  });

  // Send token to your backend
  await api.post('/users/push-token', { token: token.data });
  return token.data;
}

// Listen for notifications
useEffect(() => {
  const foregroundSub = Notifications.addNotificationReceivedListener((notification) => {
    // Handle foreground notification
    console.log(notification);
  });

  const responseSub = Notifications.addNotificationResponseReceivedListener((response) => {
    // User tapped notification — navigate to relevant screen
    const data = response.notification.request.content.data;
    navigation.navigate('Detail', { itemId: data.itemId });
  });

  return () => {
    foregroundSub.remove();
    responseSub.remove();
  };
}, []);
```

**Platform-Specific Code**

```tsx
import { Platform, StyleSheet } from 'react-native';

// Conditional rendering
{
  Platform.OS === 'ios' && <IOSSpecificComponent />;
}
{
  Platform.OS === 'android' && <AndroidSpecificComponent />;
}

// Platform-specific styles
const styles = StyleSheet.create({
  header: {
    paddingTop: Platform.select({ ios: 44, android: 24, default: 0 }),
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1 },
      android: { elevation: 4 },
    }),
  },
});

// Platform-specific files (auto-selected by bundler)
// Button.ios.tsx — used on iOS
// Button.android.tsx — used on Android
// Button.tsx — fallback
```

**Offline-First with MMKV + React Query**

```tsx
import { MMKV } from 'react-native-mmkv';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';
import { persistQueryClient } from '@tanstack/react-query-persist-client';

const storage = new MMKV();
const persister = createSyncStoragePersister({
  storage: {
    getItem: (key) => storage.getString(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  },
});

// Persist query cache across sessions
persistQueryClient({ queryClient, persister, maxAge: 1000 * 60 * 60 * 24 });

// Queries with staleTime serve cached data instantly while revalidating
const { data } = useQuery({
  queryKey: ['feed'],
  queryFn: fetchFeed,
  staleTime: 1000 * 60 * 5, // 5 minutes
});
```

## Flutter

**Widget Fundamentals**

```dart
// Stateful widget
class CounterScreen extends StatefulWidget {
  const CounterScreen({super.key});

  @override
  State<CounterScreen> createState() => _CounterScreenState();
}

class _CounterScreenState extends State<CounterScreen> {
  int _count = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Counter')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('$_count', style: Theme.of(context).textTheme.displayLarge),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => setState(() => _count++),
              icon: const Icon(Icons.add),
              label: const Text('Increment'),
            ),
          ],
        ),
      ),
    );
  }
}
```

**State Management (Riverpod)**

```dart
// Define providers
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(authRepositoryProvider));
});

final userFeedProvider = FutureProvider.autoDispose<List<Post>>((ref) async {
  final userId = ref.watch(authProvider.select((s) => s.userId));
  return ref.watch(postsRepositoryProvider).getFeed(userId);
});

// Use in widget
class FeedScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedAsync = ref.watch(userFeedProvider);

    return feedAsync.when(
      loading: () => const CircularProgressIndicator(),
      error: (err, stack) => ErrorView(error: err),
      data: (posts) => ListView.builder(
        itemCount: posts.length,
        itemBuilder: (_, i) => PostCard(post: posts[i]),
      ),
    );
  }
}
```

**Navigation (GoRouter)**

```dart
final router = GoRouter(routes: [
  GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
  GoRoute(
    path: '/post/:id',
    builder: (context, state) => PostDetailScreen(id: state.pathParameters['id']!),
  ),
  ShellRoute(
    builder: (_, __, child) => ScaffoldWithNavBar(child: child),
    routes: [
      GoRoute(path: '/feed', builder: (_, __) => const FeedScreen()),
      GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
    ],
  ),
]);
```

## Performance

**React Native**

- Use `FlatList` (not `ScrollView`) for long lists — virtualized rendering
- `memo()` on list item components to prevent re-renders
- Move heavy computation off the JS thread with `react-native-reanimated` (runs on UI thread)
- Use `InteractionManager.runAfterInteractions()` to defer non-critical work
- Profile with Flipper or React DevTools Profiler
- Enable Hermes engine (default in Expo SDK 48+)

**Flutter**

- Use `const` constructors everywhere possible — prevents widget rebuilds
- `RepaintBoundary` to isolate frequently-repainting subtrees
- `ListView.builder` instead of `ListView` with children list
- Profile with Flutter DevTools Performance tab
- Avoid `setState` at high levels of the widget tree

## App Store Submission

**iOS (App Store)**

```bash
# Build with EAS (Expo)
eas build --platform ios --profile production
eas submit --platform ios

# Required: Apple Developer account ($99/year)
# Required: App Store Connect app record, privacy policy URL
# Required: Screenshots for all required device sizes (6.7", 6.1", 12.9" iPad)
# Typical review: 1–3 days
```

**Android (Google Play)**

```bash
eas build --platform android --profile production
eas submit --platform android

# Required: Google Play Developer account ($25 one-time)
# Required: Policy declaration, content rating questionnaire
# Required: 512x512 icon, feature graphic (1024x500), screenshots
# Internal testing → Closed testing → Open testing → Production
```

**App Config (app.json)**

```json
{
  "expo": {
    "name": "MyApp",
    "slug": "myapp",
    "version": "1.2.0",
    "ios": {
      "bundleIdentifier": "com.company.myapp",
      "buildNumber": "42",
      "infoPlist": {
        "NSCameraUsageDescription": "We use your camera to scan QR codes",
        "NSLocationWhenInUseUsageDescription": "We use your location to show nearby stores"
      }
    },
    "android": {
      "package": "com.company.myapp",
      "versionCode": 42,
      "permissions": ["CAMERA", "ACCESS_FINE_LOCATION"]
    }
  }
}
```
