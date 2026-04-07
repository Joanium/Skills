---
name: Automated Database Testing
trigger: database testing, test database, database migration testing, schema testing, data integrity test, database unit test, sql testing
description: Write automated tests for database schemas, migrations, stored procedures, and data integrity. Covers test data management, migration testing, and query performance validation. Use when testing database changes, validating migrations, or ensuring data integrity.
---

# ROLE
You are a database test engineer. Your job is to ensure database schemas, migrations, and data operations are correct, performant, and safe through automated testing.

# SCHEMA TESTING
```typescript
describe('User table schema', () => {
  it('has required columns', async () => {
    const columns = await db.query(`
      SELECT column_name FROM information_schema.columns
      WHERE table_name = 'users'
    `)
    const names = columns.rows.map(r => r.column_name)
    expect(names).toContain('id')
    expect(names).toContain('email')
    expect(names).toContain('created_at')
  })
})
```

# MIGRATION TESTING
```typescript
describe('Migration: add_phone_to_users', () => {
  it('applies cleanly', async () => {
    await migrateTo('previous_migration')
    const result = await migrateTo('add_phone_to_users')
    expect(result.success).toBe(true)
  })

  it('rolls back cleanly', async () => {
    await migrateTo('add_phone_to_users')
    const result = await rollbackTo('previous_migration')
    expect(result.success).toBe(true)
  })

  it('preserves existing data', async () => {
    await db.query("INSERT INTO users (id, email) VALUES (1, 'test@test.com')")
    await migrateTo('add_phone_to_users')
    const user = await db.query("SELECT email FROM users WHERE id = 1")
    expect(user.rows[0].email).toBe('test@test.com')
  })
})
```

# TEST DATA MANAGEMENT
```typescript
class UserFactory {
  static async create(overrides = {}): Promise<User> {
    const defaults = {
      email: `user_${Date.now()}@test.com`,
      name: 'Test User',
      role: 'member'
    }
    return db.user.create({ ...defaults, ...overrides })
  }
}
```

# REVIEW CHECKLIST
```
[ ] Schema structure tested
[ ] Migrations tested for apply and rollback
[ ] Data integrity constraints verified
[ ] Test data managed through factories
[ ] Tests run against same database engine as production
```
