---
name: Java Design Patterns
trigger: design patterns java, singleton, factory, builder, observer, strategy, decorator, adapter, command, proxy, template method, facade, java patterns, gang of four, oop patterns, creational structural behavioral
description: Implement the essential Gang of Four design patterns correctly in Java. Covers creational, structural, and behavioral patterns with real-world examples and when to use vs. when to avoid each.
---

# ROLE
You are a senior Java architect. Your job is to guide correct, idiomatic implementation of design patterns in Java. Patterns are solutions to recurring design problems — not templates to apply blindly. Know when NOT to use them as much as when to use them.

# PATTERN CATEGORIES
```
CREATIONAL    → How objects are created
              Singleton, Factory Method, Abstract Factory, Builder, Prototype

STRUCTURAL    → How objects are composed
              Adapter, Decorator, Facade, Proxy, Composite, Bridge, Flyweight

BEHAVIORAL    → How objects communicate
              Strategy, Observer, Command, Template Method, Iterator, State,
              Chain of Responsibility, Mediator, Visitor
```

# CREATIONAL PATTERNS

## Singleton — One Instance Globally
```java
// BEST — Enum singleton (thread-safe, serialization-safe, JVM guaranteed)
public enum AppConfig {
    INSTANCE;
    private final String dbUrl = System.getenv("DB_URL");
    public String getDbUrl() { return dbUrl; }
}
AppConfig.INSTANCE.getDbUrl();

// Double-checked locking (when enum isn't suitable)
public class Connection {
    private static volatile Connection instance;

    private Connection() {}

    public static Connection getInstance() {
        if (instance == null) {
            synchronized (Connection.class) {
                if (instance == null) instance = new Connection();
            }
        }
        return instance;
    }
}

// WHEN TO USE: logging, config, thread pool, cache
// AVOID: don't use for objects that need state per user/request — use IoC instead
```

## Factory Method — Delegate Creation to Subclass
```java
public abstract class NotificationSender {
    // Factory method — subclass decides what to create
    protected abstract Notification createNotification(String message);

    public void send(String message) {
        Notification n = createNotification(message);   // uses factory method
        n.deliver();
    }
}

public class EmailNotificationSender extends NotificationSender {
    @Override
    protected Notification createNotification(String message) {
        return new EmailNotification(message);
    }
}
// WHEN TO USE: when the exact class to instantiate should be decided by subclass
```

## Builder — Construct Complex Objects Step-by-Step
```java
public class HttpRequest {
    private final String url;
    private final String method;
    private final Map<String, String> headers;
    private final String body;
    private final int timeoutMs;

    private HttpRequest(Builder b) {
        this.url       = b.url;
        this.method    = b.method;
        this.headers   = Collections.unmodifiableMap(b.headers);
        this.body      = b.body;
        this.timeoutMs = b.timeoutMs;
    }

    public static class Builder {
        private final String url;
        private String method = "GET";
        private Map<String, String> headers = new HashMap<>();
        private String body;
        private int timeoutMs = 5000;

        public Builder(String url) { this.url = url; }
        public Builder method(String m) { this.method = m; return this; }
        public Builder header(String k, String v) { headers.put(k, v); return this; }
        public Builder body(String b) { this.body = b; return this; }
        public Builder timeout(int ms) { this.timeoutMs = ms; return this; }
        public HttpRequest build() { return new HttpRequest(this); }
    }
}

// Usage
HttpRequest req = new HttpRequest.Builder("https://api.example.com/users")
    .method("POST")
    .header("Content-Type", "application/json")
    .body("{\"name\":\"Alice\"}")
    .timeout(3000)
    .build();

// With Lombok — @Builder annotation generates the builder automatically
@Builder
public class HttpRequest { ... }
```

# STRUCTURAL PATTERNS

## Adapter — Bridge Incompatible Interfaces
```java
// Existing class we can't change
public class LegacyXmlParser {
    public String parseXml(String xml) { ... }
}

// Interface our system expects
public interface JsonParser {
    String parse(String json);
}

// Adapter — wraps legacy, speaks new interface
public class XmlToJsonAdapter implements JsonParser {
    private final LegacyXmlParser legacy;

    public XmlToJsonAdapter(LegacyXmlParser legacy) { this.legacy = legacy; }

    @Override
    public String parse(String json) {
        String xml = convertJsonToXml(json);
        return legacy.parseXml(xml);
    }
}
// WHEN TO USE: integrating third-party or legacy code into a modern interface
```

## Decorator — Add Behavior Without Subclassing
```java
public interface Logger {
    void log(String message);
}

public class ConsoleLogger implements Logger {
    @Override public void log(String message) { System.out.println(message); }
}

// Decorator wraps a Logger to add behavior
public class TimestampLogger implements Logger {
    private final Logger wrapped;
    public TimestampLogger(Logger wrapped) { this.wrapped = wrapped; }

    @Override
    public void log(String message) {
        wrapped.log(LocalDateTime.now() + " " + message);
    }
}

public class PrefixLogger implements Logger {
    private final Logger wrapped;
    private final String prefix;
    public PrefixLogger(Logger wrapped, String prefix) {
        this.wrapped = wrapped; this.prefix = prefix;
    }
    @Override
    public void log(String m) { wrapped.log("[" + prefix + "] " + m); }
}

// Stack decorators
Logger logger = new PrefixLogger(new TimestampLogger(new ConsoleLogger()), "AUTH");
logger.log("User logged in");   // [AUTH] 2024-01-15T10:30:00 User logged in

// WHEN TO USE: adding cross-cutting concerns (logging, caching, auth) to objects
// Real-world: Java I/O streams are all decorators (BufferedReader wraps FileReader)
```

## Facade — Simple Interface to Complex Subsystem
```java
// Complex subsystem
class VideoEncoder { void encode(String path) { ... } }
class AudioMixer   { void mix(String path) { ... } }
class ThumbnailGen { void generate(String path) { ... } }
class CDNUploader  { void upload(String path) { ... } }

// Facade — single entry point for the whole flow
public class VideoProcessingFacade {
    private final VideoEncoder encoder = new VideoEncoder();
    private final AudioMixer   mixer   = new AudioMixer();
    private final ThumbnailGen thumbs  = new ThumbnailGen();
    private final CDNUploader  cdn     = new CDNUploader();

    public void processAndPublish(String videoPath) {
        encoder.encode(videoPath);
        mixer.mix(videoPath);
        thumbs.generate(videoPath);
        cdn.upload(videoPath);
    }
}
// Client calls one method, doesn't know about 4 subsystems
```

## Proxy — Controlled Access to an Object
```java
public interface ImageLoader {
    void display(String filename);
}

public class RealImageLoader implements ImageLoader {
    @Override
    public void display(String filename) { /* expensive disk/network load */ }
}

// Lazy-loading proxy — defer real work until needed
public class ImageLoaderProxy implements ImageLoader {
    private RealImageLoader real;
    private final String filename;

    public ImageLoaderProxy(String filename) { this.filename = filename; }

    @Override
    public void display(String filename) {
        if (real == null) real = new RealImageLoader();  // lazy init
        real.display(filename);
    }
}
// WHEN TO USE: lazy init, access control, caching, remote calls
// Spring AOP, Hibernate lazy loading — both use dynamic proxy
```

# BEHAVIORAL PATTERNS

## Strategy — Swap Algorithms at Runtime
```java
public interface SortStrategy {
    void sort(int[] data);
}

public class QuickSort  implements SortStrategy { ... }
public class MergeSort  implements SortStrategy { ... }
public class BubbleSort implements SortStrategy { ... }

public class Sorter {
    private SortStrategy strategy;

    public Sorter(SortStrategy strategy) { this.strategy = strategy; }
    public void setStrategy(SortStrategy s) { this.strategy = s; }
    public void sort(int[] data) { strategy.sort(data); }
}

// Java 8+ — strategy IS a functional interface, use lambdas
Sorter sorter = new Sorter(data -> Arrays.sort(data));
sorter.setStrategy((data) -> myCustomSort(data));

// WHEN TO USE: payment methods, validation rules, compression algorithms, pricing strategies
```

## Observer — Notify Dependents of State Change
```java
// Observer interface
public interface EventListener<T> {
    void onEvent(T event);
}

// Observable
public class EventBus<T> {
    private final List<EventListener<T>> listeners = new ArrayList<>();

    public void subscribe(EventListener<T> listener) { listeners.add(listener); }
    public void unsubscribe(EventListener<T> listener) { listeners.remove(listener); }
    public void publish(T event) { listeners.forEach(l -> l.onEvent(event)); }
}

// Java has built-in: PropertyChangeSupport, java.util.Observable (legacy)
// Spring events: ApplicationEventPublisher / @EventListener

@Component
public class OrderService {
    @Autowired ApplicationEventPublisher publisher;

    public void placeOrder(Order order) {
        saveOrder(order);
        publisher.publishEvent(new OrderPlacedEvent(order));  // decouple notification
    }
}

@Component
public class EmailService {
    @EventListener
    public void onOrderPlaced(OrderPlacedEvent event) {
        sendConfirmation(event.getOrder());
    }
}
```

## Command — Encapsulate Actions as Objects
```java
public interface Command {
    void execute();
    void undo();
}

public class TextEditor {
    private StringBuilder text = new StringBuilder();

    public class InsertCommand implements Command {
        private final String toInsert;
        private final int position;

        public InsertCommand(String text, int pos) { this.toInsert = text; this.position = pos; }
        public void execute() { text.insert(position, toInsert); }
        public void undo()    { text.delete(position, position + toInsert.length()); }
    }
}

// Command history (undo stack)
Deque<Command> history = new ArrayDeque<>();
Command cmd = editor.new InsertCommand("Hello", 0);
cmd.execute();
history.push(cmd);
history.pop().undo();   // undo last action

// WHEN TO USE: undo/redo, job queues, transaction logs, UI buttons
```

## Template Method — Define Skeleton, Defer Steps to Subclass
```java
public abstract class ReportGenerator {
    // Template method — defines the algorithm skeleton
    public final void generate() {
        fetchData();
        processData();
        formatOutput();    // abstract — subclass decides format
        saveReport();
    }

    protected abstract void formatOutput();   // hook — must override

    protected void fetchData()    { /* default DB fetch */ }
    protected void processData()  { /* default transform */ }
    protected void saveReport()   { /* default save */ }
}

public class PdfReportGenerator extends ReportGenerator {
    @Override
    protected void formatOutput() { /* PDF-specific logic */ }
}

// WHEN TO USE: common algorithm with varying steps (parsers, report generators, games)
// Java examples: HttpServlet.service(), AbstractList
```

# WHEN NOT TO USE PATTERNS
```
Singleton   → If you're using Spring — Spring beans ARE singletons. Don't double-up.
Factory     → If simple new() is fine — patterns add indirection cost
Observer    → If one listener — just call it directly; EventBus for 3+ is overkill
Decorator   → If behavior is fixed — subclassing or composition might be simpler
Builder     → If < 3 constructor params — overengineering; use constructor directly
```

# BEST PRACTICES CHECKLIST
```
[ ] Apply a pattern because it solves a real problem — not to show knowledge
[ ] Prefer composition over inheritance — it's more flexible and testable
[ ] Strategy pattern fits anywhere you'd write a switch-on-type dispatch
[ ] Use Spring @EventListener for Observer — don't roll your own bus
[ ] Builder pattern via Lombok @Builder avoids boilerplate
[ ] Command + Deque = undo/redo stack — simplest correct implementation
[ ] Decorator is how Java I/O works — understand it before writing wrappers
[ ] Template Method prefers abstract methods — not empty default implementations
```
