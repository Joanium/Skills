---
name: Debug — React Native / Expo
trigger: react native error, expo bug, metro bundler, red screen, yellow warning, native module not found, expo go, eas build failing, ios crash, android crash, flipper, hermes, bridge error, react native not working
description: Hyper-specific debugging guide for React Native and Expo. Real red screen errors, real causes, real fixes. Covers Metro bundler, native modules, Expo SDK, EAS Build, iOS/Android platform issues, and performance.
---

# Debug — React Native / Expo

## First Move

```bash
# Clear EVERYTHING — fixes 80% of mysterious RN issues
npx expo start --clear         # Expo — clear Metro cache
npx react-native start --reset-cache  # bare RN

# Full clean for iOS
cd ios && pod install && cd ..
watchman watch-del-all
rm -rf /tmp/metro-*
npm start -- --reset-cache

# Full clean for Android
cd android && ./gradlew clean && cd ..

# Check Expo SDK / RN version alignment
cat package.json | grep -E '"expo"|"react-native"'
npx expo-doctor  # checks for compatibility issues

# Check connected devices
adb devices          # Android
xcrun simctl list    # iOS simulators
```

---

## Red Screen Errors

### `Unable to resolve module 'X'`

```bash
# 1. Clear cache and restart Metro
npx expo start --clear

# 2. Module actually missing — install it
npm install some-package
# For Expo managed workflow — check if it's in the Expo SDK first:
npx expo install some-package  # installs Expo-compatible version

# 3. Wrong platform — some modules are web-only or native-only
# Fix: platform-specific imports
import { Platform } from 'react-native'
const Storage = Platform.OS === 'web'
  ? require('@react-native-async-storage/async-storage').default
  : require('./NativeStorage').default

# 4. Bare RN: native module installed but pods not linked
cd ios && pod install  # iOS — always after adding native dependencies
cd android && ./gradlew clean  # Android

# 5. Path alias not resolving
# babel.config.js needs babel-plugin-module-resolver:
module.exports = {
  plugins: [['module-resolver', { alias: { '@': './src' } }]]
}
```

---

### `Invariant Violation: "main" has not been registered`

```javascript
// Root component not registered correctly

// Fix: check your entry point
// For Expo: index.js or App.js should have:
import { registerRootComponent } from 'expo'
import App from './App'
registerRootComponent(App)

// For bare RN: index.js should have:
import { AppRegistry } from 'react-native'
import App from './App'
import { name as appName } from './app.json'
AppRegistry.registerComponent(appName, () => App)

// Check app.json / app.config.js for correct app name
cat app.json | grep '"name"'
```

---

### `Native module cannot be null` / `NativeModules.X is null`

```bash
# The native module is installed but not linked/built

# Expo managed workflow: check if module supports Expo
npx expo install package-name  # use expo install not npm install
# Some native modules ONLY work in bare workflow or EAS Build — check docs

# Bare workflow — rebuild the native app
cd ios && pod install && cd ..  # iOS: re-link
npx react-native run-ios         # rebuild iOS app

cd android && ./gradlew clean && cd ..
npx react-native run-android     # rebuild Android app

# Verify the module is in your podfile (iOS)
cat ios/Podfile | grep package-name

# Verify in android/settings.gradle (older RN without autolinking)
cat android/settings.gradle | grep package-name
```

---

## Metro Bundler Issues

```bash
# Watchman errors — often cause Metro to miss file changes
watchman watch-del-all
watchman shutdown-server
# Then restart Metro

# Port conflict
npx expo start --port 8082  # use different port

# Symlink issues (monorepo)
# metro.config.js — add symlink support:
const { getDefaultConfig } = require('expo/metro-config')
const config = getDefaultConfig(__dirname)
config.resolver.unstable_enableSymlinks = true
module.exports = config

# Module resolution in monorepo
config.watchFolders = [path.resolve(__dirname, '../../')]  # watch root
config.resolver.nodeModulesPaths = [
  path.resolve(__dirname, 'node_modules'),
  path.resolve(__dirname, '../../node_modules'),  # hoisted packages
]
```

---

## iOS Specific

```bash
# Build fails — see the actual error
cd ios
xcodebuild -workspace YourApp.xcworkspace \
  -scheme YourApp \
  -configuration Debug \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  2>&1 | grep -E "error:|warning:" | head -30

# Pod install issues
cd ios
pod deintegrate     # remove all pods
pod install         # clean reinstall
# If that fails:
pod repo update     # update CocoaPods spec repo
pod install --repo-update

# Signing issues (physical device)
# Open ios/YourApp.xcworkspace in Xcode
# Select your target → Signing & Capabilities
# Set Team, enable Automatically manage signing

# Code signing error in EAS Build
# Fix: configure credentials in eas.json:
{
  "build": {
    "production": {
      "ios": { "credentialsSource": "remote" }
    }
  }
}
eas credentials  # manage certificates and provisioning profiles
```

---

## Android Specific

```bash
# See all Android build errors (not just the last one)
cd android
./gradlew assembleDebug 2>&1 | tail -50

# Duplicate resource error
# Usually caused by a library including conflicting resources
# Fix in android/app/build.gradle:
android {
    packagingOptions {
        pickFirst 'lib/x86/libc++_shared.so'
        pickFirst 'lib/arm64-v8a/libc++_shared.so'
    }
}

# Minimum SDK version conflict
# Fix: set minSdkVersion to match what your dependencies need
android {
    defaultConfig {
        minSdkVersion 23  # check what your deps require
    }
}

# Hermes engine issues
# Check if Hermes is enabled:
cat android/app/build.gradle | grep hermesEnabled
# If causing issues, disable temporarily:
# project.ext.react = [enableHermes: false]

# ADB debug
adb logcat | grep -i "react\|error\|fatal"  # filter logs
adb reverse tcp:8081 tcp:8081  # allow device to reach Metro on localhost
```

---

## Expo Go vs Development Build

```bash
# Expo Go only supports Expo SDK modules — custom native code won't work

# Check if you need a dev build:
# - Using any custom native module → need dev build
# - Using expo-dev-client package → use dev build

# Create a development build
npx expo install expo-dev-client
eas build --profile development --platform ios
eas build --profile development --platform android

# eas.json profile for dev build:
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    }
  }
}
```

---

## EAS Build Failures

```bash
# Check build logs — full output
eas build:list  # see recent builds
eas build:view  # open logs for a build

# Common causes:

# 1. Environment variables missing in EAS
eas secret:create --scope project --name API_KEY --value "value"
# Reference in eas.json:
{
  "build": {
    "production": {
      "env": { "API_KEY": "$API_KEY" }
    }
  }
}

# 2. node_modules not in sync — ensure package-lock.json is committed
git add package-lock.json && git commit

# 3. Expo SDK version mismatch
npx expo-doctor  # tells you exactly what's wrong
npx expo install --fix  # auto-fix compatible versions

# 4. iOS: certificate/provisioning profile expired
eas credentials --platform ios  # view and update credentials
```

---

## Performance Debugging

```javascript
// React Native FPS drops — profile in Flipper or Hermes debugger

// 1. Heavy component re-renders — same as React
import { memo, useCallback, useMemo } from 'react'
const ExpensiveItem = memo(({ item, onPress }) => ...)

// 2. Long JS thread work — use InteractionManager for post-transition work
import { InteractionManager } from 'react-native'
InteractionManager.runAfterInteractions(() => {
  // Run after animation completes — doesn't block the animation
  loadHeavyData()
})

// 3. FlatList performance — common mistakes
<FlatList
  data={items}
  keyExtractor={(item) => item.id}  // must be string, must be stable
  renderItem={({ item }) => <Item item={item} />}  // ← don't define inline
  getItemLayout={(data, index) => ({  // massive perf boost if items have fixed height
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
  removeClippedSubviews={true}  // unmount off-screen items (be careful with some content)
  maxToRenderPerBatch={10}      // control render batch size
  windowSize={10}               // render 5 screens above/below
/>

// 4. Image performance
import { Image } from 'expo-image'  // replace React Native's Image — much better caching
// Always specify width/height to avoid layout recalculation
// Use blurhash for low-res placeholders while loading

// 5. Debug what's causing re-renders
import { useFocusEffect } from '@react-navigation/native'
const renderCount = useRef(0)
renderCount.current++
console.log('MyComponent render count:', renderCount.current)
```

---

## Navigation Issues

```javascript
// React Navigation — screen not found
// Error: The action 'NAVIGATE' with payload {"name":"Profile"} was not handled

// Fix: check screen is registered in the navigator
<Stack.Navigator>
  <Stack.Screen name="Profile" component={ProfileScreen} />  // must be here
</Stack.Navigator>

// Nested navigator navigation — must specify nested screen
navigation.navigate('HomeTab', {
  screen: 'Profile',           // screen inside HomeTab navigator
  params: { userId: '123' }
})

// Params not arriving — check they're passed correctly
// Sender:
navigation.navigate('Profile', { userId: user.id })
// Receiver:
const { userId } = route.params  // params, not props!

// Deep linking not working
// Check your linking config matches your screen names exactly:
const linking = {
  prefixes: ['myapp://'],
  config: {
    screens: {
      Profile: 'user/:userId',  // screen name must match Stack.Screen name="Profile"
    }
  }
}
```
