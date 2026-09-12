# AGENTS.md

## Project context

This is a hackathon project.

Goal:
Build a simple working MVP quickly.

The application allows users to store and manage their medical history.

Priorities:
1. Working functionality
2. Simple architecture
3. Fast implementation
4. Readable code
5. Avoid unnecessary complexity

---

## General rules

Before making changes:

1. Inspect the existing codebase and related files.
2. Reuse existing components, models and utilities whenever possible.
3. Follow the current project architecture and coding style.
4. Prefer the smallest change that solves the task.

Do not:

- rewrite unrelated code
- introduce unnecessary abstractions
- add dependencies unless clearly needed
- rename files or public interfaces without a reason
- change working functionality unrelated to the task
- overengineer solutions

This is a hackathon MVP. Prefer simple working solutions over production-grade complexity.

---

## Working with existing code

Before implementing a feature:

- Find the files related to the task.
- Understand how similar functionality is implemented.
- Reuse existing patterns.
- Check existing database models, schemas, API routes and frontend components before creating new ones.

Do not create duplicate implementations.

---

## Backend

Follow the existing backend architecture.

Prefer:

route/controller
→ service/business logic
→ database/model

Keep API handlers small.

Use existing:
- database session
- models
- schemas
- utilities

Do not create new architectural layers unless necessary.

---

## Database

Before modifying the database:

- inspect existing models
- inspect relationships
- reuse existing tables where appropriate

Do not change the database schema unless the task requires it.

Keep the hackathon data model simple.

---

## Frontend

Reuse existing components and styles.

Do not introduce a new UI framework.

Keep UI functionality simple and usable.

Avoid unnecessary animations or complex state management.

---

## API

Preserve existing API contracts unless the task explicitly requires a change.

Use consistent:
- endpoint naming
- HTTP status codes
- request/response schemas
- error handling

---

## Scope control

Only modify files necessary for the current task.

If a task can be solved with a small local change, do not refactor the surrounding system.

If you discover unrelated problems, mention them in the summary instead of fixing them automatically.

---

## Verification

After implementing a task:

1. Check the changed code for obvious errors.
2. Run relevant tests if available.
3. Run lint/typecheck if configured.
4. Verify imports and references.
5. Make sure existing functionality is not obviously broken.

Do not claim tests passed unless they were actually executed.

---

## Final response

After completing a task, provide a short summary:

- what was changed
- which files were changed
- how to test it
- any known limitations or issues

Keep the response concise.