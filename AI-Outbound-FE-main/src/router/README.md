# Role-Based Authorization Middleware

This directory contains router configurations and middleware for implementing role-based authorization in the application.

## Overview

The middleware-based approach centralizes authorization logic to ensure consistent enforcement of access controls across the application. This approach offers several benefits:

1. **Centralized logic**: Authorization rules are defined in one place
2. **DRY principle**: No duplicate role-checking code across components
3. **Security**: Routes are protected at the router level before components load
4. **Maintainability**: Changing authorization rules requires updates in only one place

## Components

### `middleware.tsx`

Contains reusable middleware components for protecting routes:

- `AuthMiddleware`: Generic middleware that checks authentication and optional role requirements
- `AdminMiddleware`: Pre-configured for admin-only routes
- `UserMiddleware`: Pre-configured for user-level access routes

### `useAuthorization.ts` hook

A custom hook that provides role-checking functions for use within components:

```tsx
const { hasRole, isAdmin, userRole } = useAuthorization();

// Usage examples
{isAdmin() && <AdminPanel />}
{hasRole('user') && <UserFeature />}
```

## Usage

### Protecting Routes

```tsx
<Route
  path="/admin"
  element={
    <AdminMiddleware>
      <DashboardLayout>
        <Outlet />
      </DashboardLayout>
    </AdminMiddleware>
  }
>
  <Route path="users" element={<User />} />
  <Route path="campaigns" element={<CampaignsAdmin />} />
</Route>
```

### Component-Level Authorization

```tsx
import useAuthorization from '../hooks/useAuthorization';

const MyComponent = () => {
  const { hasRole, isAdmin } = useAuthorization();
  
  return (
    <div>
      {isAdmin() && <AdminControls />}
      {hasRole(['user', 'agent']) && <UserControls />}
    </div>
  );
};
```

## Best Practices

1. Use router middleware for coarse-grained access control (page/route level)
2. Use the `useAuthorization` hook for fine-grained control within components
3. Avoid checking `user.role` directly; use the provided hooks and middleware
4. Keep authorization logic centralized and consistent 