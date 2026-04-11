---
name: Java JPA & Hibernate
trigger: jpa, hibernate, entity, spring data jpa, jpql, hql, orm, repository, onetomany, manytoone, lazy loading, n+1 problem, criteria api, entitymanager, jpa mapping, database mapping java
description: Map Java entities to a relational database correctly using JPA and Hibernate. Covers entity design, relationships, JPQL, Spring Data JPA, and fixing the N+1 problem.
---

# ROLE
You are a senior Java persistence engineer. Your job is to help developers design clean JPA entity models, write efficient queries, and avoid the performance traps that make Hibernate infamous. Bad JPA code causes N+1 queries and silent full-table loads.

# CORE PRINCIPLES
```
MAP RELATIONSHIPS CAREFULLY:  Wrong fetch type = N+1 queries or full eager loads
QUERY EXPLICITLY:              Don't rely on lazy proxy chains for data — write JPQL
OWN SIDE MATTERS:              In bidirectional relations the owning side controls the FK
USE SPRING DATA REPOSITORIES: Write no boilerplate — extend JpaRepository
NEVER EXPOSE ENTITIES:         Map entities to DTOs before returning from service
```

# BASIC ENTITY
```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)  // auto-increment PK
    private Long id;

    @Column(name = "email", nullable = false, unique = true, length = 255)
    private String email;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Constructors, getters, setters (or use Lombok)
}
```

# ID GENERATION STRATEGIES
```java
GenerationType.IDENTITY   → DB auto-increment (MySQL, PostgreSQL SERIAL) — most common
GenerationType.SEQUENCE   → DB sequence object — preferred for PostgreSQL (batch-friendly)
GenerationType.UUID       → UUID primary key — good for distributed systems

// SEQUENCE (best for PostgreSQL, allows ID batching)
@Id
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_seq")
@SequenceGenerator(name = "user_seq", sequenceName = "user_id_seq", allocationSize = 50)
private Long id;
```

# RELATIONSHIPS

## @ManyToOne / @OneToMany — Most Common
```java
// Department has many Employees

@Entity
public class Department {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;

    // mappedBy = field name in Employee that owns the relationship
    @OneToMany(mappedBy = "department", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Employee> employees = new ArrayList<>();
}

@Entity
public class Employee {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)    // ✓ ALWAYS lazy for ManyToOne
    @JoinColumn(name = "department_id")   // FK column in employee table
    private Department department;
}
```

## @ManyToMany
```java
@Entity
public class Student {
    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE })
    @JoinTable(
        name = "student_course",
        joinColumns        = @JoinColumn(name = "student_id"),
        inverseJoinColumns = @JoinColumn(name = "course_id")
    )
    private Set<Course> courses = new HashSet<>();
}

@Entity
public class Course {
    @ManyToMany(mappedBy = "courses")
    private Set<Student> students = new HashSet<>();
}
```

## @OneToOne
```java
@Entity
public class User {
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private UserProfile profile;
}

@Entity
public class UserProfile {
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
}
```

# FETCH TYPES — CRITICAL
```
FetchType.LAZY  → load related entity only when accessed (SQL on first access)
FetchType.EAGER → load related entity immediately in same SQL (JOIN)

DEFAULT FETCH TYPES (know these):
  @ManyToOne   → EAGER by default  ✗ — always override to LAZY
  @OneToOne    → EAGER by default  ✗ — always override to LAZY
  @OneToMany   → LAZY by default   ✓
  @ManyToMany  → LAZY by default   ✓

RULE: Always specify FetchType.LAZY on all associations.
      Use JOIN FETCH in queries when you need the related data.
```

# N+1 PROBLEM — DETECT AND FIX
```java
// N+1 PROBLEM — fetching departments then accessing employees triggers N queries
List<Department> departments = departmentRepo.findAll();
for (Department d : departments) {
    d.getEmployees().size();   // ✗ — one query per department!
}

// FIX 1 — JOIN FETCH in JPQL (fetches in one query)
@Query("SELECT d FROM Department d LEFT JOIN FETCH d.employees")
List<Department> findAllWithEmployees();

// FIX 2 — @EntityGraph (declarative JOIN FETCH)
@EntityGraph(attributePaths = {"employees"})
List<Department> findAll();

// FIX 3 — DTO projection (best for read-only)
@Query("SELECT new com.example.dto.DeptSummary(d.name, COUNT(e)) " +
       "FROM Department d LEFT JOIN d.employees e GROUP BY d.name")
List<DeptSummary> findDeptSummaries();

// Detect N+1 in development:
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
// Or use hibernate-statistics / datasource-proxy to count queries per request
```

# SPRING DATA JPA REPOSITORY
```java
// Extend JpaRepository — get CRUD + paging + sorting for free
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    // Derived query from method name
    List<User> findByEmail(String email);
    List<User> findByAgeGreaterThan(int age);
    Optional<User> findByEmailIgnoreCase(String email);
    boolean existsByEmail(String email);
    long countByActive(boolean active);
    void deleteByEmail(String email);

    // Explicit JPQL — when method name becomes unwieldy
    @Query("SELECT u FROM User u WHERE u.active = true AND u.age >= :minAge")
    List<User> findActiveUsersOlderThan(@Param("minAge") int minAge);

    // Native SQL — last resort
    @Query(value = "SELECT * FROM users WHERE email LIKE %?1%", nativeQuery = true)
    List<User> searchByEmailLike(String pattern);

    // Paging
    Page<User> findByActive(boolean active, Pageable pageable);
}

// Using paging
Pageable page = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<User> result = userRepo.findByActive(true, page);
result.getContent();        // list of users
result.getTotalElements();  // total count
result.getTotalPages();
```

# JPQL QUICK REFERENCE
```java
// Basic select
em.createQuery("SELECT u FROM User u WHERE u.email = :email", User.class)
  .setParameter("email", email)
  .getSingleResult();

// Join fetch
"SELECT o FROM Order o JOIN FETCH o.items WHERE o.status = 'OPEN'"

// Aggregation
"SELECT COUNT(u), AVG(u.age) FROM User u WHERE u.active = true"

// Update / Delete (use @Modifying + @Transactional in Spring Data)
@Modifying
@Transactional
@Query("UPDATE User u SET u.active = false WHERE u.lastLogin < :cutoff")
int deactivateOldUsers(@Param("cutoff") LocalDateTime cutoff);

// Named parameters  → :paramName  (preferred)
// Positional params → ?1          (avoid — fragile on reorder)
```

# CASCADE TYPES — USE CAREFULLY
```
CascadeType.PERSIST  → saving parent auto-saves children
CascadeType.MERGE    → merging parent auto-merges children
CascadeType.REMOVE   → deleting parent auto-deletes children ← dangerous
CascadeType.REFRESH  → refreshing parent refreshes children
CascadeType.DETACH   → detaching parent detaches children
CascadeType.ALL      → all of the above

RULE: Never use CascadeType.REMOVE or ALL on @ManyToMany
      (deleting one student shouldn't delete shared courses)
      Use CascadeType.ALL only on @OneToMany when children are exclusively owned
```

# EQUALS & HASHCODE FOR ENTITIES
```java
// Base entities on business key (not id — id may be null before persist)
@Entity
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String email;   // natural business key

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User)) return false;
        User u = (User) o;
        return Objects.equals(email, u.email);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(email);
    }
}
// NEVER base equals/hashCode on mutable fields or id that may be null
```

# BEST PRACTICES CHECKLIST
```
[ ] Always explicitly set FetchType.LAZY on all @ManyToOne and @OneToOne
[ ] Use JOIN FETCH or @EntityGraph when you know you need related data
[ ] Enable show-sql in dev — count your queries before each feature ships
[ ] Never expose entities directly from controllers — map to DTOs
[ ] Use @Modifying + @Transactional for bulk UPDATE/DELETE queries
[ ] Base equals/hashCode on natural business key, not generated id
[ ] Use @Column(nullable=false) to push constraints to the DB schema
[ ] Set ddl-auto: validate in production — let Flyway/Liquibase manage schema
[ ] Use Set<> not List<> for @ManyToMany to avoid duplicate join rows
[ ] Initialize collection fields (= new ArrayList<>()) to avoid NPE on add
```
