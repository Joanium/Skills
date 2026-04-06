---
name: RealtimeDatabaseSync
description: Build real-time data synchronization between clients and databases using Firebase, Supabase Realtime, PocketBase, Electric SQL, or custom WebSocket-based sync. Use when the user asks about live data updates, optimistic UI, conflict resolution, offline-first sync, reactive queries, or collaborative features.
---

You are an expert in real-time database synchronization, covering Firebase Realtime Database, Firestore, Supabase Realtime, PocketBase, CRDTs, optimistic updates, conflict resolution, and building collaborative and offline-first applications.

The user provides a real-time sync task: adding live updates to an app, handling offline state, implementing optimistic UI, resolving data conflicts, building collaborative editing, or choosing a sync architecture.

## Real-Time Sync Architecture Patterns

**Pattern 1: Server-Authoritative Push**
Server owns the truth. Clients subscribe and receive updates pushed down. Best for: dashboards, live feeds, collaborative tools.

**Pattern 2: Optimistic UI + Reconciliation**
Client immediately reflects changes locally, syncs to server async, reconciles on conflict. Best for: forms, todo apps, interactive tools.

**Pattern 3: CRDT-Based Sync**
Conflict-free Replicated Data Types — mathematically guarantee eventual consistency without conflict resolution logic. Best for: rich collaborative editing (text, drawing).

**Pattern 4: Event Sourcing**
Store a log of events, not current state. Clients replay events to build state. Best for: audit trails, collaborative features, complex undo/redo.

## Firebase (Firestore)

**Real-Time Listeners**

```ts
import { collection, doc, onSnapshot, query, where, orderBy } from 'firebase/firestore';

// Listen to a document
const unsubscribe = onSnapshot(
  doc(db, 'rooms', roomId),
  (snap) => {
    if (snap.exists()) {
      setRoom({ id: snap.id, ...snap.data() });
    } else {
      setRoom(null);
    }
  },
  (error) => {
    console.error('Listener error:', error);
  },
);

// Listen to a query
const q = query(
  collection(db, 'messages'),
  where('roomId', '==', roomId),
  orderBy('createdAt', 'asc'),
);

const unsubscribeMsgs = onSnapshot(
  q,
  (snapshot) => {
    const changes = snapshot.docChanges();
    changes.forEach((change) => {
      if (change.type === 'added') addMessage(change.doc);
      if (change.type === 'modified') updateMessage(change.doc);
      if (change.type === 'removed') removeMessage(change.doc.id);
    });
  },
  { includeMetadataChanges: true },
);

// Cleanup on unmount
useEffect(() => {
  return () => {
    unsubscribe();
    unsubscribeMsgs();
  };
}, [roomId]);
```

**Optimistic Writes with Firestore**

```ts
import { addDoc, serverTimestamp, writeBatch } from 'firebase/firestore';

async function sendMessage(content: string, userId: string) {
  // Generate a local ID immediately for optimistic UI
  const localId = crypto.randomUUID();
  const optimisticMsg = { id: localId, content, userId, createdAt: new Date(), pending: true };

  // Show immediately in UI
  addMessageToUI(optimisticMsg);

  try {
    const docRef = await addDoc(collection(db, 'messages'), {
      content,
      userId,
      roomId,
      createdAt: serverTimestamp(), // Server timestamp — avoid client clock skew
    });
    // Replace optimistic message with confirmed one
    updateMessageInUI(localId, { id: docRef.id, pending: false });
  } catch (err) {
    // Rollback
    removeMessageFromUI(localId);
    showError('Failed to send message');
  }
}

// Atomic batch writes
async function transferPoints(fromId: string, toId: string, amount: number) {
  const batch = writeBatch(db);
  batch.update(doc(db, 'users', fromId), { points: increment(-amount) });
  batch.update(doc(db, 'users', toId), { points: increment(amount) });
  batch.set(doc(collection(db, 'transfers')), {
    from: fromId,
    to: toId,
    amount,
    createdAt: serverTimestamp(),
  });
  await batch.commit(); // All or nothing
}
```

**Firestore Security Rules**

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Messages: authenticated users can read; only author can write
    match /messages/{messageId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null
        && request.resource.data.userId == request.auth.uid
        && request.resource.data.content is string
        && request.resource.data.content.size() < 2000;
      allow update, delete: if request.auth.uid == resource.data.userId;
    }

    // Room members only
    match /rooms/{roomId}/messages/{messageId} {
      allow read, write: if request.auth.uid in
        get(/databases/$(database)/documents/rooms/$(roomId)).data.members;
    }
  }
}
```

## Supabase Realtime

**Broadcast (ephemeral, no persistence)**

```ts
const channel = supabase.channel('room:123');

channel
  .on('broadcast', { event: 'cursor' }, ({ payload }) => {
    updateCursor(payload.userId, payload.x, payload.y);
  })
  .subscribe();

// Send cursor position
function onMouseMove(e: MouseEvent) {
  channel.send({
    type: 'broadcast',
    event: 'cursor',
    payload: { userId: currentUser.id, x: e.clientX, y: e.clientY },
  });
}
```

**Postgres Changes (DB-level real-time)**

```ts
const subscription = supabase
  .channel('messages-channel')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'messages', filter: `room_id=eq.${roomId}` },
    (payload) => {
      if (payload.eventType === 'INSERT') addMessage(payload.new);
      if (payload.eventType === 'UPDATE') updateMessage(payload.new);
      if (payload.eventType === 'DELETE') removeMessage(payload.old.id);
    },
  )
  .subscribe((status) => {
    if (status === 'SUBSCRIBED') console.log('Realtime connected');
  });

// Cleanup
return () => supabase.removeChannel(subscription);
```

**Presence (who's online)**

```ts
const channel = supabase.channel('room:123', {
  config: { presence: { key: currentUser.id } },
});

channel
  .on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState();
    // state = { userId1: [{ online_at, ...meta }], userId2: [...] }
    setOnlineUsers(Object.keys(state));
  })
  .on('presence', { event: 'join' }, ({ key, newPresences }) => {
    showToast(`${key} joined`);
  })
  .on('presence', { event: 'leave' }, ({ key }) => {
    removeFromOnline(key);
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({ online_at: new Date().toISOString(), name: currentUser.name });
    }
  });
```

## Optimistic UI Pattern

```ts
// Generic optimistic update hook
function useOptimisticMutation<T, V>(
  mutationFn: (variables: V) => Promise<T>,
  options: {
    onOptimisticUpdate: (variables: V) => void;
    onSuccess: (result: T, variables: V) => void;
    onError: (error: Error, variables: V) => void;
  },
) {
  return async (variables: V) => {
    options.onOptimisticUpdate(variables);
    try {
      const result = await mutationFn(variables);
      options.onSuccess(result, variables);
      return result;
    } catch (error) {
      options.onError(error as Error, variables);
      throw error;
    }
  };
}

// Usage with React Query
const { mutate: sendMsg } = useMutation({
  mutationFn: api.sendMessage,
  onMutate: async (newMsg) => {
    await queryClient.cancelQueries({ queryKey: ['messages', roomId] });
    const previous = queryClient.getQueryData(['messages', roomId]);

    // Optimistically add message
    queryClient.setQueryData(['messages', roomId], (old: Message[]) => [
      ...(old || []),
      { ...newMsg, id: `temp-${Date.now()}`, pending: true },
    ]);

    return { previous }; // Return context for rollback
  },
  onError: (err, newMsg, context) => {
    queryClient.setQueryData(['messages', roomId], context?.previous);
    toast.error('Failed to send message');
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['messages', roomId] });
  },
});
```

## Offline-First Sync

**IndexedDB + Background Sync**

```ts
import Dexie, { type Table } from 'dexie';

class AppDatabase extends Dexie {
  messages!: Table<Message>;
  pendingOps!: Table<PendingOperation>;

  constructor() {
    super('AppDB');
    this.version(1).stores({
      messages: 'id, roomId, createdAt',
      pendingOps: '++id, type, status, createdAt',
    });
  }
}

const db = new AppDatabase();

async function sendMessageOfflineFirst(content: string) {
  const localId = crypto.randomUUID();
  const msg = { id: localId, content, roomId, createdAt: new Date(), syncStatus: 'pending' };

  // Save locally first — works even when offline
  await db.messages.put(msg);

  // Queue for sync
  await db.pendingOps.add({
    type: 'CREATE_MESSAGE',
    payload: msg,
    status: 'pending',
    createdAt: new Date(),
  });

  // Attempt sync if online
  if (navigator.onLine) {
    syncPendingOps();
  }
}

async function syncPendingOps() {
  const pending = await db.pendingOps.where('status').equals('pending').toArray();

  for (const op of pending) {
    try {
      await processOperation(op);
      await db.pendingOps.update(op.id!, { status: 'synced' });
    } catch (err) {
      await db.pendingOps.update(op.id!, { status: 'failed', error: String(err) });
    }
  }
}

// Auto-sync when connection is restored
window.addEventListener('online', syncPendingOps);
```

## Conflict Resolution Strategies

**Last-Write-Wins (LWW)**

- Server accepts the latest timestamp
- Simple, but loses concurrent edits
- Good for: user settings, profile data

**Operational Transformation (OT)**

- Transform operations against each other to maintain intent
- Used by: Google Docs, older collaborative editors
- Complex to implement correctly

**CRDTs (Conflict-free Replicated Data Types)**

```ts
import * as Y from 'yjs'; // Yjs is the most popular CRDT library
import { WebrtcProvider } from 'y-webrtc';
import { IndexeddbPersistence } from 'y-indexeddb';

const doc = new Y.Doc();

// Persist locally
const indexeddbProvider = new IndexeddbPersistence('my-doc', doc);

// Sync with peers (P2P) or use y-websocket for server-based sync
const provider = new WebrtcProvider('room-id', doc);

// Shared data types
const text = doc.getText('content'); // Collaborative text
const array = doc.getArray('items'); // Collaborative list
const map = doc.getMap('metadata'); // Collaborative key-value

// Bind to editor (Tiptap, CodeMirror, etc.)
import { yCollab } from 'y-codemirror.next';
const extensions = [yCollab(text, provider.awareness)];

// Observe changes
text.observe(() => {
  setContent(text.toString());
});

// Make changes (auto-merged with remote)
text.insert(0, 'Hello ');
array.push(['new item']);
map.set('title', 'My Document');
```
