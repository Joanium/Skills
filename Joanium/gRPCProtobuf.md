---
name: gRPC & Protocol Buffers
trigger: grpc, protobuf, proto file, grpc service, protocol buffers, grpc streaming, grpc vs rest, grpc gateway, unary rpc, server streaming, client streaming, bidirectional streaming, grpc interceptor, buf tool
description: Design and implement gRPC services with Protocol Buffers. Covers .proto schema design, service patterns (unary/streaming), code generation, error handling, interceptors, deadlines, and gRPC-Gateway for REST compatibility.
---

# ROLE
You are a distributed systems engineer who knows gRPC and Protocol Buffers deeply. You design schemas that are backwards-compatible, services that are resilient, and APIs that are fast. You default to gRPC when performance, streaming, or type-safety matters more than universal HTTP client compatibility.

# WHEN TO CHOOSE gRPC VS REST
```
Choose gRPC when:
  ✓ Service-to-service (internal microservices)
  ✓ Real-time bidirectional streaming (chat, telemetry)
  ✓ Strongly-typed contracts between teams
  ✓ High-throughput, low-latency (protobuf is ~10x smaller than JSON)
  ✓ Polyglot services (auto-generated clients for Go, Python, Java, etc.)

Choose REST when:
  ✓ Public-facing APIs (browser clients, third-party integrators)
  ✓ Simple CRUD with no streaming needs
  ✓ Team unfamiliar with protobuf toolchain
  ✓ Caching via HTTP semantics matters
```

# PROTO FILE DESIGN
```protobuf
// user.proto — well-structured proto file
syntax = "proto3";

package myapp.users.v1;            // versioned package
option go_package = "github.com/myorg/myapp/gen/users/v1;usersv1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/field_mask.proto";

// ─── Messages ───────────────────────────────────────────────────

message User {
  string id          = 1;           // field numbers: never change these once published
  string email       = 2;
  string name        = 3;
  UserRole role      = 4;
  google.protobuf.Timestamp created_at = 5;
  google.protobuf.Timestamp updated_at = 6;
  // reserved 7, 8;                 // if you remove fields, reserve the numbers
  // reserved "phone", "address";   // and the names — prevents accidental reuse
}

enum UserRole {
  USER_ROLE_UNSPECIFIED = 0;    // ALWAYS have a 0 value for enums
  USER_ROLE_MEMBER      = 1;
  USER_ROLE_ADMIN       = 2;
  USER_ROLE_SUPER_ADMIN = 3;
}

message CreateUserRequest {
  string email = 1;
  string name  = 2;
  UserRole role = 3;
}

message GetUserRequest {
  string id = 1;
}

message UpdateUserRequest {
  string id    = 1;
  string name  = 2;              // only send fields to update
  google.protobuf.FieldMask update_mask = 3;   // explicit field mask
}

message ListUsersRequest {
  int32  page_size   = 1;        // max 100
  string page_token  = 2;        // cursor-based pagination
  string filter      = 3;        // e.g., "role=admin"
}

message ListUsersResponse {
  repeated User users          = 1;
  string        next_page_token = 2;   // empty = last page
  int32         total_size      = 3;
}

// ─── Service ─────────────────────────────────────────────────────

service UserService {
  // Unary: single request → single response
  rpc GetUser(GetUserRequest)    returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(GetUserRequest) returns (google.protobuf.Empty);

  // Server streaming: single request → stream of responses
  rpc ListUsers(ListUsersRequest) returns (stream User);

  // Client streaming: stream of requests → single response
  rpc BatchCreateUsers(stream CreateUserRequest) returns (BatchCreateUsersResponse);

  // Bidirectional streaming
  rpc SyncUsers(stream SyncUserRequest) returns (stream SyncUserResponse);
}
```

# FIELD NUMBER RULES — CRITICAL
```
NEVER change a field number once released — it breaks binary compatibility
NEVER reuse a removed field number — use reserved instead
NEVER change a field type (int32 → int64 etc.) — wire format differs
ALWAYS start field numbers at 1 (1–15 use 1 byte, 16–2047 use 2 bytes)
ALWAYS use reserved for removed fields

Safe changes (backward compatible):
  ✓ Add new optional fields with new field numbers
  ✓ Add new RPC methods to a service
  ✓ Add new enum values
  ✓ Add new messages

Breaking changes (require new package version):
  ✗ Remove or rename fields (use reserved)
  ✗ Change field number
  ✗ Change field type
  ✗ Change from repeated to singular
```

# CODE GENERATION WITH BUF
```bash
# buf.yaml — in repo root
version: v2
modules:
  - path: proto
lint:
  use:
    - DEFAULT
breaking:
  use:
    - FILE   # detect breaking changes vs baseline

# buf.gen.yaml — code generation config
version: v2
plugins:
  - remote: buf.build/grpc/go
    out: gen/go
    opt:
      - paths=source_relative
  - remote: buf.build/protocolbuffers/go
    out: gen/go
    opt:
      - paths=source_relative
  - remote: buf.build/grpc/python
    out: gen/python

# Commands
buf generate                   # generate code
buf lint                       # lint proto files
buf breaking --against .git#branch=main   # detect breaking changes vs main
buf push                       # push to BSR (Buf Schema Registry)
```

# SERVER IMPLEMENTATION (Go)
```go
type userServiceServer struct {
    pb.UnimplementedUserServiceServer   // always embed this — forward compat
    db *Database
}

// Unary RPC
func (s *userServiceServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    // Validate
    if req.Id == "" {
        return nil, status.Error(codes.InvalidArgument, "id is required")
    }
    
    // Check context (deadline/cancellation propagated automatically)
    if ctx.Err() != nil {
        return nil, status.Error(codes.Canceled, "request canceled")
    }
    
    user, err := s.db.GetUser(ctx, req.Id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, status.Errorf(codes.NotFound, "user %q not found", req.Id)
        }
        return nil, status.Errorf(codes.Internal, "failed to get user: %v", err)
    }
    
    return toProtoUser(user), nil
}

// Server streaming
func (s *userServiceServer) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
    users, err := s.db.ListUsers(stream.Context(), req)
    if err != nil {
        return status.Errorf(codes.Internal, "failed to list users: %v", err)
    }
    
    for _, user := range users {
        if err := stream.Send(toProtoUser(user)); err != nil {
            return err   // client disconnected
        }
    }
    return nil
}

// Start server
func main() {
    lis, _ := net.Listen("tcp", ":50051")
    
    s := grpc.NewServer(
        grpc.ChainUnaryInterceptor(
            loggingInterceptor,
            authInterceptor,
            recoveryInterceptor,
        ),
        grpc.MaxRecvMsgSize(10 * 1024 * 1024),   // 10 MB max request
    )
    
    pb.RegisterUserServiceServer(s, &userServiceServer{db: db})
    reflection.Register(s)   // enable grpcurl reflection in dev
    
    s.Serve(lis)
}
```

# ERROR CODES — USE PRECISELY
```
codes.OK                   → success (don't return explicitly, just return nil)
codes.InvalidArgument      → bad request (client error — validation failed)
codes.NotFound             → resource not found
codes.AlreadyExists        → resource already exists (create conflict)
codes.PermissionDenied     → authenticated but not authorized
codes.Unauthenticated      → missing or invalid credentials
codes.ResourceExhausted    → rate limit / quota exceeded
codes.FailedPrecondition   → operation not valid in current state
codes.Aborted              → concurrency conflict (optimistic locking)
codes.Unavailable          → service temporarily down (retry)
codes.DeadlineExceeded     → timeout
codes.Internal             → unexpected server error (don't expose internals)
codes.Unimplemented        → RPC not implemented yet

Rich error details (via google.rpc.Status):
  st, _ := status.New(codes.InvalidArgument, "validation failed").
    WithDetails(&errdetails.BadRequest{
      FieldViolations: []*errdetails.BadRequest_FieldViolation{
        {Field: "email", Description: "must be a valid email address"},
      },
    })
  return nil, st.Err()
```

# INTERCEPTORS (MIDDLEWARE)
```go
// Logging interceptor
func loggingInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    log.Printf("method=%s duration=%s err=%v", info.FullMethod, time.Since(start), err)
    return resp, err
}

// Auth interceptor — extract and validate JWT
func authInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }
    tokens := md.Get("authorization")
    if len(tokens) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing authorization header")
    }
    claims, err := validateJWT(tokens[0])
    if err != nil {
        return nil, status.Error(codes.Unauthenticated, "invalid token")
    }
    ctx = context.WithValue(ctx, userClaimsKey, claims)
    return handler(ctx, req)
}
```

# DEADLINES & CANCELLATION
```go
// Client: always set a deadline
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: "usr_123"})

// Server: propagate context to all downstream calls
func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    // This respects the client's deadline automatically
    user, err := s.db.GetUser(ctx, req.Id)   // pass ctx here
    ...
}

// Why deadlines matter:
// Without deadline: client waits forever on hung service → cascading failures
// With deadline: client fails fast, circuit breaker can trip, retries are bounded
```

# GRPC-GATEWAY (REST COMPATIBILITY)
```protobuf
import "google/api/annotations.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (User) {
    option (google.api.http) = {
      get: "/v1/users/{id}"     // expose as REST GET /v1/users/{id}
    };
  }
  rpc CreateUser(CreateUserRequest) returns (User) {
    option (google.api.http) = {
      post: "/v1/users"
      body: "*"
    };
  }
}
// grpc-gateway generates a reverse proxy that translates REST → gRPC
// Run both gRPC (port 50051) and HTTP (port 8080) from the same server
```

# PRODUCTION CHECKLIST
```
[ ] All fields use reserved when removed
[ ] Field numbers never reused
[ ] buf lint passing with no warnings
[ ] buf breaking check in CI (no accidental breaking changes)
[ ] All RPCs have deadlines set on client side
[ ] Server interceptors: logging, auth, panic recovery, metrics
[ ] TLS enabled (not plaintext in production)
[ ] reflection.Register for dev/staging (disable in prod)
[ ] Max message size configured (default 4 MB is often too small)
[ ] Health check service registered (grpc.health.v1.Health)
[ ] Retry policy configured on client channel
```
