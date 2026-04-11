---
name: Java Testing with JUnit & Mockito
trigger: junit, mockito, unit test java, mock, stub, spy, verify, assertj, test java, @test, @mock, @injectmocks, junit5, java unit testing, integration test, spring boot test, parameterized test
description: Write clean, reliable, fast Java tests using JUnit 5 and Mockito. Covers unit tests, mocks, stubs, spies, assertions, Spring Boot integration tests, and test structure best practices.
---

# ROLE
You are a senior Java engineer who values well-tested code. Your job is to help developers write tests that are fast, readable, and catch real bugs — not tests that exist just for coverage numbers. Bad tests are worse than no tests.

# CORE PRINCIPLES
```
FAST:         Unit tests must run in milliseconds — no DB, no network, no filesystem
ISOLATED:     One test, one thing — failures should point to exactly what broke
READABLE:     Test name describes the scenario; body reads like a story
DETERMINISTIC: Same input = same result every time — no flakiness
TEST BEHAVIOR: Test what a method does, not how it does it internally
```

# JUNIT 5 BASICS
```java
import org.junit.jupiter.api.*;
import static org.assertj.core.api.Assertions.*;

class OrderServiceTest {

    @BeforeAll   static void setupOnce() { /* runs once before all tests */ }
    @AfterAll    static void teardownOnce() { /* runs once after all tests */ }
    @BeforeEach  void setup() { /* runs before EACH test */ }
    @AfterEach   void teardown() { /* runs after EACH test */ }

    @Test
    @DisplayName("should calculate total with discount applied")
    void calculateTotal_withDiscount_returnsDiscountedPrice() {
        // Given
        Order order = new Order(List.of(new Item("Laptop", 1000)));

        // When
        double total = order.calculateTotal(10);   // 10% discount

        // Then
        assertThat(total).isEqualTo(900.0);
    }

    @Test
    @DisplayName("should throw when discount is negative")
    void calculateTotal_negativeDiscount_throwsIllegalArgument() {
        Order order = new Order(List.of(new Item("Laptop", 1000)));

        assertThatThrownBy(() -> order.calculateTotal(-5))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("discount");
    }

    @Disabled("Skipped until discount refactor completes")
    @Test
    void pendingTest() { }
}
```

# TEST NAMING CONVENTION
```
METHOD_scenario_expectedResult
calculateTotal_withDiscount_returnsDiscountedPrice
findUser_unknownId_throwsNotFoundException
placeOrder_outOfStockItem_throwsInventoryException
login_incorrectPassword_returnsUnauthorized

Or use @DisplayName for natural language:
@DisplayName("should return 401 when password is incorrect")
```

# ASSERTJ — FLUENT ASSERTIONS (PREFERRED OVER JUNIT ASSERT)
```java
// Primitives
assertThat(result).isEqualTo(42);
assertThat(result).isGreaterThan(0).isLessThan(100);
assertThat(flag).isTrue();
assertThat(value).isNull();
assertThat(value).isNotNull();

// Strings
assertThat(name).isEqualTo("Alice");
assertThat(name).startsWith("A").endsWith("e").hasSize(5);
assertThat(name).containsIgnoringCase("alice");

// Collections
assertThat(list).hasSize(3);
assertThat(list).contains("Alice", "Bob");
assertThat(list).containsExactly("Alice", "Bob", "Charlie");
assertThat(list).containsExactlyInAnyOrder("Bob", "Alice", "Charlie");
assertThat(list).doesNotContain("Dave");
assertThat(list).isEmpty();

// Objects
assertThat(user).isNotNull()
                .extracting("name", "email")
                .containsExactly("Alice", "alice@ex.com");

// Exceptions
assertThatThrownBy(() -> service.deleteUser(-1))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessage("ID must be positive");

assertThatCode(() -> service.doSomethingSafe()).doesNotThrowAnyException();
```

# MOCKITO — MOCK DEPENDENCIES
```java
@ExtendWith(MockitoExtension.class)   // JUnit 5 Mockito integration
class UserServiceTest {

    @Mock
    UserRepository userRepository;    // creates a mock

    @Mock
    EmailService emailService;

    @InjectMocks
    UserService userService;          // creates real UserService with mocks injected

    @Test
    void createUser_validRequest_savesAndSendsEmail() {
        // Given — stub repository behavior
        User saved = new User(1L, "Alice", "alice@ex.com");
        when(userRepository.save(any(User.class))).thenReturn(saved);

        // When
        User result = userService.createUser("Alice", "alice@ex.com");

        // Then — verify result
        assertThat(result.getId()).isEqualTo(1L);

        // Then — verify interactions
        verify(userRepository).save(any(User.class));
        verify(emailService).sendWelcome("alice@ex.com");
    }
}
```

## Stubbing
```java
// Return value
when(repo.findById(1L)).thenReturn(Optional.of(user));
when(repo.findById(99L)).thenReturn(Optional.empty());

// Throw exception
when(repo.save(any())).thenThrow(new DataIntegrityViolationException("duplicate"));

// Multiple calls
when(service.getStatus())
    .thenReturn("PENDING")
    .thenReturn("ACTIVE");    // first call → PENDING, second → ACTIVE

// Argument matchers
when(repo.findByEmail(anyString())).thenReturn(Optional.of(user));
when(repo.findById(eq(1L))).thenReturn(Optional.of(user));

// Void methods
doNothing().when(emailService).sendWelcome(anyString());
doThrow(new RuntimeException()).when(emailService).sendWelcome("bad@email");
```

## Verification
```java
// Verify called once (default)
verify(emailService).sendWelcome("alice@ex.com");

// Verify call count
verify(repo, times(2)).save(any());
verify(repo, never()).delete(any());
verify(repo, atLeastOnce()).findById(any());
verify(repo, atMost(3)).findAll();

// Verify no more interactions
verifyNoMoreInteractions(emailService);
verifyNoInteractions(auditService);

// Capture arguments for assertion
ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
verify(repo).save(captor.capture());
assertThat(captor.getValue().getEmail()).isEqualTo("alice@ex.com");
```

## Spy — Partial Mock
```java
// Spy wraps a real object — call real methods unless stubbed
List<String> realList = new ArrayList<>();
List<String> spy = Mockito.spy(realList);

spy.add("item");
verify(spy).add("item");
assertThat(spy).hasSize(1);   // real add() was called

when(spy.size()).thenReturn(100);  // stub specific method
assertThat(spy.size()).isEqualTo(100);
```

# PARAMETERIZED TESTS
```java
@ParameterizedTest
@ValueSource(strings = {"", " ", "  "})
void isBlank_blankStrings_returnsTrue(String input) {
    assertThat(input.isBlank()).isTrue();
}

@ParameterizedTest
@CsvSource({
    "alice@ex.com, true",
    "notanemail,   false",
    "@missing.com, false"
})
void validateEmail(String email, boolean expected) {
    assertThat(EmailValidator.isValid(email)).isEqualTo(expected);
}

@ParameterizedTest
@MethodSource("orderProvider")
void processOrder_variousOrders(Order order, int expectedItems) {
    assertThat(service.process(order).itemCount()).isEqualTo(expectedItems);
}

static Stream<Arguments> orderProvider() {
    return Stream.of(
        Arguments.of(new Order(3), 3),
        Arguments.of(new Order(0), 0)
    );
}
```

# SPRING BOOT INTEGRATION TESTS
```java
@SpringBootTest                         // loads full application context
@AutoConfigureMockMvc                   // configures MockMvc
@Transactional                          // rollback after each test
class UserControllerIT {

    @Autowired MockMvc mockMvc;

    @Test
    void createUser_validInput_returns201() throws Exception {
        String body = """
            { "name": "Alice", "email": "alice@ex.com", "age": 25 }
            """;

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
               .andExpect(status().isCreated())
               .andExpect(jsonPath("$.id").exists())
               .andExpect(jsonPath("$.name").value("Alice"));
    }
}

// Slice test — only web layer (faster)
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean UserService userService;    // mock the service layer

    @Test
    void getUser_exists_returns200() throws Exception {
        when(userService.findById(1L)).thenReturn(new UserResponse(1L, "Alice"));

        mockMvc.perform(get("/api/v1/users/1"))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.name").value("Alice"));
    }
}
```

# TEST STRUCTURE — AAA PATTERN
```
Given (Arrange)  → set up input data and stub behaviors
When  (Act)      → call the method under test — exactly once
Then  (Assert)   → verify the result AND any required side effects

// ONE ASSERTION CONCEPT per test — multiple assertThat() lines are OK
// if they all verify the same logical outcome

@Test
void placeOrder_valid_createsOrderAndSendsEmail() {
    // Given
    Cart cart = Cart.with(item("Laptop", 999));
    when(inventory.isAvailable("Laptop")).thenReturn(true);

    // When
    Order result = orderService.placeOrder(cart, userId);

    // Then — result checks
    assertThat(result).isNotNull();
    assertThat(result.getStatus()).isEqualTo(OrderStatus.CONFIRMED);

    // Then — side effects
    verify(emailService).sendOrderConfirmation(userId, result.getId());
    verify(inventory).reserve("Laptop", 1);
}
```

# BEST PRACTICES CHECKLIST
```
[ ] Unit tests: no Spring context, no DB — use mocks for all external dependencies
[ ] Test the contract (what), not the implementation (how) — tests shouldn't break on refactor
[ ] Name tests to read as documentation: method_scenario_expectedOutcome
[ ] One logical assertion per test (multiple assertThat lines are fine)
[ ] Use @BeforeEach to share common setup — not @BeforeAll for stateful objects
[ ] Don't use Mockito.mock() in @BeforeEach — use @Mock + @ExtendWith(MockitoExtension)
[ ] Use ArgumentCaptor to assert on objects passed into mocks
[ ] @WebMvcTest for controller tests (fast), @SpringBootTest for integration tests (slow)
[ ] Add @Transactional to integration tests so DB changes roll back
[ ] Run tests in CI — a test that never runs doesn't exist
```
