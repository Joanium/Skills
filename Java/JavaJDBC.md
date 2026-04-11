---
name: Java JDBC
trigger: jdbc, java database connectivity, preparedstatement, resultset, connection pool, datasource, sql java, jdbc template, hikaricp, jdbc connection, java sql query, jdbc best practices
description: Connect Java applications to relational databases using JDBC. Covers connections, PreparedStatement, ResultSet, connection pooling with HikariCP, and avoiding SQL injection.
---

# ROLE
You are a senior Java backend engineer. Your job is to help developers write correct, secure, and performant JDBC code. Raw JDBC is verbose — knowing the right patterns keeps it manageable and safe.

# CORE PRINCIPLES
```
NEVER STRING-CONCAT SQL:  Always use PreparedStatement — SQL injection kills apps
CLOSE EVERYTHING:         Connection, Statement, ResultSet — use try-with-resources
POOL CONNECTIONS:         Never create a new Connection per request — use HikariCP
USE TRANSACTIONS:         Group related SQL into explicit transactions for consistency
FAIL LOUDLY:              Never swallow SQLExceptions silently
```

# JDBC BASICS — RAW CONNECTION
```java
// Always use try-with-resources — auto-closes Connection, Statement, ResultSet
String url  = "jdbc:postgresql://localhost:5432/mydb";
String user = "admin";
String pass = System.getenv("DB_PASSWORD");

try (Connection conn = DriverManager.getConnection(url, user, pass);
     PreparedStatement ps = conn.prepareStatement(
         "SELECT id, name, email FROM users WHERE active = ? AND age > ?")) {

    ps.setBoolean(1, true);
    ps.setInt(2, 18);

    try (ResultSet rs = ps.executeQuery()) {
        while (rs.next()) {
            long   id    = rs.getLong("id");
            String name  = rs.getString("name");
            String email = rs.getString("email");
            System.out.println(id + " " + name + " " + email);
        }
    }
} catch (SQLException e) {
    throw new DataAccessException("Failed to fetch users", e);
}
```

# PREPAREDSTATEMENT — ALWAYS, NO EXCEPTIONS
```java
// SQL INJECTION — NEVER DO THIS
String name = request.getParam("name");
String sql  = "SELECT * FROM users WHERE name = '" + name + "'";
// Input: ' OR '1'='1  → SELECT * FROM users WHERE name = '' OR '1'='1'
// Returns all rows — or worse: drops tables with '; DROP TABLE users; --

// SAFE — PreparedStatement parameterizes values, never interprets them as SQL
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE name = ? AND dept = ?");
ps.setString(1, name);     // ✓ value is bound, never interpreted as SQL
ps.setString(2, dept);

// Insert
PreparedStatement ins = conn.prepareStatement(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)");
ins.setString(1, "Alice");
ins.setString(2, "alice@ex.com");
ins.setInt(3, 28);
int rowsAffected = ins.executeUpdate();

// Get generated keys
PreparedStatement ins = conn.prepareStatement(
    "INSERT INTO users (name) VALUES (?)",
    Statement.RETURN_GENERATED_KEYS);
ins.setString(1, "Alice");
ins.executeUpdate();
try (ResultSet keys = ins.getGeneratedKeys()) {
    if (keys.next()) {
        long newId = keys.getLong(1);
    }
}
```

# RESULTSET — READING DATA
```java
// Column by name (preferred — robust to column order changes)
rs.getLong("id")
rs.getString("email")
rs.getInt("age")
rs.getDouble("balance")
rs.getBoolean("active")
rs.getTimestamp("created_at").toLocalDateTime()
rs.getDate("birth_date").toLocalDate()
rs.getBigDecimal("price")
rs.getObject("column", MyType.class)   // Java 8+ typed getObject

// NULL handling — rs.getInt returns 0 if null, not null
int age = rs.getInt("age");
if (rs.wasNull()) {
    // handle null age
}

// Or use getObject
Integer age = (Integer) rs.getObject("age");  // returns null if DB null
```

# TRANSACTIONS
```java
try (Connection conn = dataSource.getConnection()) {
    conn.setAutoCommit(false);   // begin transaction

    try {
        PreparedStatement debit = conn.prepareStatement(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?");
        debit.setBigDecimal(1, amount);
        debit.setLong(2, fromId);
        debit.executeUpdate();

        PreparedStatement credit = conn.prepareStatement(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?");
        credit.setBigDecimal(1, amount);
        credit.setLong(2, toId);
        credit.executeUpdate();

        conn.commit();    // both succeed → commit
    } catch (SQLException e) {
        conn.rollback();  // either fails → rollback both
        throw new DataAccessException("Transfer failed", e);
    }
}

// Savepoints — partial rollback
Savepoint sp = conn.setSavepoint("step1");
try {
    // risky step
} catch (SQLException e) {
    conn.rollback(sp);   // roll back to savepoint, not entire transaction
}
```

# CONNECTION POOLING — HIKARICP (INDUSTRY STANDARD)
```xml
<!-- Maven dependency -->
<dependency>
    <groupId>com.zaxxer</groupId>
    <artifactId>HikariCP</artifactId>
    <version>5.1.0</version>
</dependency>
```

```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
config.setUsername("admin");
config.setPassword(System.getenv("DB_PASSWORD"));

// Pool sizing — start with (cores * 2) + 1
config.setMaximumPoolSize(10);
config.setMinimumIdle(5);
config.setConnectionTimeout(30_000);     // 30s — max wait for a connection
config.setIdleTimeout(600_000);          // 10min idle before close
config.setMaxLifetime(1_800_000);        // 30min — recycle connections
config.setKeepaliveTime(30_000);         // keep connections alive

// Validation query (auto-detected for popular DBs)
config.setConnectionTestQuery("SELECT 1");   // PostgreSQL/MySQL
config.setPoolName("MyPool");

DataSource dataSource = new HikariDataSource(config);

// Spring Boot auto-configures HikariCP — just set these in application.yml:
// spring.datasource.hikari.maximum-pool-size=10
// spring.datasource.hikari.connection-timeout=30000
```

# BATCH OPERATIONS — EFFICIENT BULK INSERT/UPDATE
```java
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(
         "INSERT INTO events (type, payload, created_at) VALUES (?, ?, ?)")) {

    conn.setAutoCommit(false);

    for (Event event : events) {
        ps.setString(1, event.getType());
        ps.setString(2, event.getPayload());
        ps.setTimestamp(3, Timestamp.from(event.getCreatedAt()));
        ps.addBatch();

        if (batchCount++ % 500 == 0) {
            ps.executeBatch();   // flush every 500 rows
            ps.clearBatch();
        }
    }

    ps.executeBatch();   // flush remaining
    conn.commit();
} catch (SQLException e) {
    conn.rollback();
    throw new DataAccessException("Batch insert failed", e);
}
```

# SPRING JDBCTEMPLATE — JDBC WITHOUT BOILERPLATE
```java
@Repository
public class UserRepository {

    private final JdbcTemplate jdbc;

    public UserRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    // Query — list
    public List<User> findAll() {
        return jdbc.query(
            "SELECT id, name, email FROM users",
            (rs, rowNum) -> new User(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email")
            )
        );
    }

    // Query — single row
    public Optional<User> findById(Long id) {
        try {
            User user = jdbc.queryForObject(
                "SELECT id, name, email FROM users WHERE id = ?",
                (rs, rn) -> new User(rs.getLong("id"), rs.getString("name"), rs.getString("email")),
                id
            );
            return Optional.ofNullable(user);
        } catch (EmptyResultDataAccessException e) {
            return Optional.empty();
        }
    }

    // Insert / Update
    public int save(User user) {
        return jdbc.update(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            user.getName(), user.getEmail()
        );
    }

    // Get generated key
    public long insert(User user) {
        KeyHolder holder = new GeneratedKeyHolder();
        jdbc.update(conn -> {
            PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, user.getName());
            ps.setString(2, user.getEmail());
            return ps;
        }, holder);
        return holder.getKey().longValue();
    }
}
```

# COMMON MISTAKES
```java
// 1 — SQL injection via string concat
"SELECT * FROM users WHERE name = '" + name + "'"   // ✗

// 2 — Not closing resources — connection pool exhaustion
Connection c = pool.getConnection();
// ... if exception thrown before close() — connection leaked forever
// FIX: always try-with-resources

// 3 — Fetching all columns with SELECT *
"SELECT * FROM large_table"   // ✗ — fetches unused columns, wastes memory
"SELECT id, name FROM users"  // ✓ — only what you need

// 4 — Not using batch for bulk inserts
for (Item i : items) {
    jdbc.update("INSERT ...", i.getName());  // ✗ N separate roundtrips
}
// FIX: use addBatch / executeBatch

// 5 — Not setting transaction isolation level
// Default is READ_COMMITTED in most DBs — fine for most apps
// Use SERIALIZABLE only if you need strict consistency (slower)
conn.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

# BEST PRACTICES CHECKLIST
```
[ ] Always use PreparedStatement — never string-concatenate SQL values
[ ] Use try-with-resources for Connection, Statement, ResultSet — no manual close
[ ] Use HikariCP — never create new Connection per request
[ ] Set pool size appropriately: (CPU cores * 2) + 1 is a good starting point
[ ] Wrap related SQL operations in explicit transactions
[ ] Use batch operations for bulk inserts/updates (hundreds+ rows)
[ ] Read columns by name (not index) — robust to schema changes
[ ] Handle NULL via rs.wasNull() or getObject() when column is nullable
[ ] Never log SQL with parameters concatenated — log query template only
[ ] Use JdbcTemplate in Spring — eliminates boilerplate, handles resource cleanup
```
