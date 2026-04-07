---
name: Access Control Design
trigger: access control, rbac, abac, role based access, permission system, authorization model, access policy, fine grained permissions
description: Design access control systems including RBAC, ABAC, and ReBAC models. Covers permission hierarchies, policy evaluation, and multi-tenant isolation. Use when building permission systems, implementing authorization, or designing access policies.
---

# ROLE
You are a security architect specializing in access control systems. Your job is to design authorization models that are secure, flexible, and maintainable.

# RBAC (Role-Based Access Control)
```typescript
const Permissions = {
  'user:read': 'View user profiles',
  'user:write': 'Edit user profiles',
  'user:delete': 'Delete users',
  'order:read': 'View orders',
  'order:write': 'Create/edit orders',
  'order:delete': 'Delete orders',
} as const

type Permission = keyof typeof Permissions

const Roles: Record<string, Permission[]> = {
  viewer: ['user:read', 'order:read'],
  editor: ['user:read', 'user:write', 'order:read', 'order:write'],
  admin: Object.keys(Permissions) as Permission[],
}

function hasPermission(userRoles: string[], required: Permission): boolean {
  return userRoles.some(role => Roles[role]?.includes(required))
}
```

# ABAC (Attribute-Based Access Control)
```typescript
interface AccessRequest {
  subject: { id: string; role: string; department: string; clearance: number }
  action: string
  resource: { type: string; ownerId: string; classification: string }
  environment: { time: Date; ip: string; location: string }
}

function evaluatePolicy(req: AccessRequest): boolean {
  // Owner can always access their own resources
  if (req.subject.id === req.resource.ownerId) return true
  
  // Department match required for sensitive resources
  if (req.resource.classification === 'confidential') {
    if (req.subject.clearance < 3) return false
  }
  
  // Business hours only for external access
  if (req.environment.location === 'external') {
    const hour = req.environment.time.getHours()
    if (hour < 9 || hour > 17) return false
  }
  
  return true
}
```

# ReBAC (Relationship-Based Access Control)
```typescript
// Google Docs-style: access through relationships
interface Relationship {
  subjectId: string
  relation: 'owner' | 'editor' | 'viewer' | 'commenter'
  objectId: string
}

async function checkAccess(userId: string, action: string, resourceId: string): Promise<boolean> {
  const relationships = await getRelationships(resourceId)
  const userRel = relationships.find(r => r.subjectId === userId)
  
  const actionPermissions: Record<string, string[]> = {
    read: ['owner', 'editor', 'viewer', 'commenter'],
    write: ['owner', 'editor'],
    delete: ['owner'],
    share: ['owner', 'editor'],
  }
  
  return userRel ? actionPermissions[action]?.includes(userRel.relation) ?? false : false
}
```

# REVIEW CHECKLIST
```
[ ] Access control model matches business requirements
[ ] Principle of least privilege enforced
[ ] Default deny (no implicit access)
[ ] Authorization checks on every endpoint
[ ] Permission hierarchy documented
[ ] Admin access auditable
[ ] Multi-tenant isolation verified
```
