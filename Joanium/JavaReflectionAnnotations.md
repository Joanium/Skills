---
name: Java Reflection & Annotations
trigger: java reflection, annotations, custom annotation, annotation processor, getclass, getmethod, getfield, invoke, annotation retention, annotation target, java metadata, reflect, class inspection java
description: Use Java reflection and custom annotations to write flexible, meta-programmatic code. Covers annotation creation, retention policies, runtime inspection, and when NOT to use reflection.
---

# ROLE
You are a senior Java engineer. Your job is to help developers use reflection and annotations correctly — powerful tools that enable frameworks but carry real costs. Misuse causes slow, brittle code. Know when to reach for them and when to step back.

# CORE PRINCIPLES
```
ANNOTATIONS ARE METADATA:  They don't do anything alone — something must read them
REFLECTION IS EXPENSIVE:   Cache reflected objects — never reflect in hot paths
FRAMEWORKS DO HEAVY LIFTING: Spring, JPA, Jackson all use reflection — you rarely need to
TYPE SAFETY LOST:          Reflection bypasses the compiler — errors become runtime exceptions
ACCESS IS A CONTRACT:      setAccessible(true) breaks encapsulation — use carefully
```

# ANNOTATIONS

## Built-in Java Annotations
```java
@Override           // compiler checks you actually override a supertype method
@Deprecated         // marks method/class as obsolete — compiler warns callers
@SuppressWarnings("unchecked")  // silences specific compiler warnings
@FunctionalInterface  // compiler enforces exactly one abstract method
@SafeVarargs        // suppress heap pollution warning for generic varargs
```

## Custom Annotation
```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)   // visible at runtime via reflection
@Target(ElementType.METHOD)           // can only be applied to methods
@Documented                           // appears in Javadoc
public @interface Timed {
    String value() default "";        // optional name for the timer
    boolean logResult() default false;
}

// Retention policies:
// SOURCE   → compiler only, discarded in .class (e.g. @Override, @SuppressWarnings)
// CLASS    → in .class file but NOT loaded at runtime (default — rarely what you want)
// RUNTIME  → loaded at runtime, readable via reflection (Spring, JPA, Jackson use this)

// Target values:
// TYPE          → class, interface, enum
// METHOD        → method
// FIELD         → field
// PARAMETER     → method parameter
// CONSTRUCTOR   → constructor
// LOCAL_VARIABLE → local variable
// ANNOTATION_TYPE → annotation type
// PACKAGE       → package declaration
```

## Reading Annotations at Runtime
```java
@Timed("fetchUser")
public User findById(Long id) { ... }

// Read from method
Method method = UserService.class.getMethod("findById", Long.class);
if (method.isAnnotationPresent(Timed.class)) {
    Timed timed = method.getAnnotation(Timed.class);
    System.out.println("Timer name: " + timed.value());  // "fetchUser"
}

// Read from class
@Component
@RequestMapping("/users")
class UserController { }

RequestMapping rm = UserController.class.getAnnotation(RequestMapping.class);
String[] paths = rm.value();
```

# REFLECTION — CLASS INSPECTION
```java
Class<?> clazz = SomeClass.class;
// or:
Class<?> clazz = obj.getClass();
// or:
Class<?> clazz = Class.forName("com.example.SomeClass");  // dynamic, slower

// Class info
clazz.getName();           // "com.example.SomeClass"
clazz.getSimpleName();     // "SomeClass"
clazz.getPackageName();    // "com.example"
clazz.getSuperclass();
clazz.getInterfaces();
clazz.isInterface();
clazz.isEnum();
clazz.isAnnotation();
Modifier.isAbstract(clazz.getModifiers());
```

## Fields
```java
// getDeclaredFields() → all fields of THIS class (including private)
// getFields()         → all PUBLIC fields (including inherited)
Field[] fields = clazz.getDeclaredFields();

for (Field field : fields) {
    field.setAccessible(true);          // bypass private access
    Object value = field.get(instance); // read value
    field.set(instance, newValue);      // write value

    field.getName();
    field.getType();
    field.getAnnotations();
    Modifier.isPrivate(field.getModifiers());
}
```

## Methods
```java
// getDeclaredMethods() → all methods of THIS class
// getMethods()         → all PUBLIC methods including inherited

Method method = clazz.getDeclaredMethod("processOrder", Order.class, boolean.class);
method.setAccessible(true);

// Invoke
Object result = method.invoke(instance, order, true);

// If static
Object result = method.invoke(null, arg1, arg2);

// Method info
method.getName();
method.getReturnType();
method.getParameterTypes();
method.getExceptionTypes();
method.isAnnotationPresent(Transactional.class);
```

## Constructors
```java
// Create instance via reflection (no-arg constructor)
Object instance = clazz.getDeclaredConstructor().newInstance();

// With arguments
Constructor<?> ctor = clazz.getDeclaredConstructor(String.class, int.class);
ctor.setAccessible(true);
Object instance = ctor.newInstance("Alice", 30);
```

# PRACTICAL USE CASE — CUSTOM ANNOTATION PROCESSOR
```java
// Annotation: @Validate marks fields that should be checked for null
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Validate {
    boolean notNull() default true;
    int maxLength() default Integer.MAX_VALUE;
}

// Validator that reads the annotation at runtime
public class BeanValidator {
    public static List<String> validate(Object obj) throws IllegalAccessException {
        List<String> errors = new ArrayList<>();
        for (Field field : obj.getClass().getDeclaredFields()) {
            if (!field.isAnnotationPresent(Validate.class)) continue;

            field.setAccessible(true);
            Validate v = field.getAnnotation(Validate.class);
            Object value = field.get(obj);

            if (v.notNull() && value == null) {
                errors.add(field.getName() + " must not be null");
            }
            if (value instanceof String s && s.length() > v.maxLength()) {
                errors.add(field.getName() + " exceeds max length " + v.maxLength());
            }
        }
        return errors;
    }
}

// Usage
public class UserRequest {
    @Validate(notNull = true, maxLength = 100)
    private String name;

    @Validate(notNull = true)
    private String email;
}

List<String> errors = BeanValidator.validate(request);
```

# GENERIC TYPE AT RUNTIME (TYPE TOKENS)
```java
// Generic type info is erased — List<String> at runtime is just List
// Workaround: ParameterizedTypeReference (Spring) or TypeToken (Guava)

// Jackson — deserialize to generic type
ObjectMapper mapper = new ObjectMapper();
List<User> users = mapper.readValue(json,
    new TypeReference<List<User>>() {});   // anonymous subclass captures type

// Spring RestTemplate
ResponseEntity<List<User>> response = restTemplate.exchange(
    url, HttpMethod.GET, null,
    new ParameterizedTypeReference<List<User>>() {});
```

# PERFORMANCE — REFLECTION IS SLOW
```java
// Method.invoke() is ~50–100x slower than direct call
// Cache reflected objects — never reflect inside a loop or hot path

// BAD — reflects on every call
public Object getValue(Object obj, String fieldName) throws Exception {
    return obj.getClass().getDeclaredField(fieldName).get(obj);  // ✗ reflects every call
}

// GOOD — cache the Field
private static final Map<String, Field> fieldCache = new ConcurrentHashMap<>();

public Object getValue(Object obj, String fieldName) throws Exception {
    Field field = fieldCache.computeIfAbsent(
        obj.getClass().getName() + "#" + fieldName,
        k -> {
            try {
                Field f = obj.getClass().getDeclaredField(fieldName);
                f.setAccessible(true);
                return f;
            } catch (NoSuchFieldException e) { throw new RuntimeException(e); }
        });
    return field.get(obj);
}

// EVEN BETTER — use MethodHandles (Java 7+, faster than reflection after JIT)
MethodHandles.Lookup lookup = MethodHandles.privateLookupIn(MyClass.class, MethodHandles.lookup());
VarHandle handle = lookup.findVarHandle(MyClass.class, "name", String.class);
String name = (String) handle.get(obj);
```

# WHEN NOT TO USE REFLECTION
```
✗ Hot code paths (per-request processing, inner loops)
✗ When a simple interface or abstract class solves the problem cleanly
✗ For dependency injection — use Spring
✗ For JSON/XML mapping — use Jackson/JAXB
✗ For ORM — use JPA/Hibernate
✓ Framework/library internals (serialization, DI, AOP)
✓ Testing — accessing private fields in unit tests
✓ Generic tools (validators, mappers) that operate across many types
✓ Plugin systems that load classes dynamically
```

# BEST PRACTICES CHECKLIST
```
[ ] Use RUNTIME retention only when you need to read the annotation at runtime
[ ] Cache Field, Method, Constructor objects — never reflect in loops or hot paths
[ ] Prefer setAccessible(true) only in tests or framework code — not business logic
[ ] Use MethodHandles for performance-critical reflective access (faster after JIT)
[ ] Use @Retention(SOURCE) for annotations only needed by the compiler
[ ] Use Spring @EventListener, AOP, or JSR-380 before rolling your own annotation processor
[ ] Test custom annotation processors with dedicated unit tests
[ ] Wrap reflection exceptions in meaningful runtime exceptions with context
[ ] Document why you're using reflection — it's the exception, not the rule
[ ] Prefer TypeReference / ParameterizedTypeReference over reflection for generic type capture
```
