# Chapter 1: Understanding the Architecture

**Estimated Time**: 30-45 minutes
**Difficulty**: Beginner
**Goal**: Understand what we're building and why we're building it this way

---

## 🎯 What You'll Learn

- What a PDM (Product Data Management) system does
- Why we chose FastAPI + Vanilla JavaScript
- How the components talk to each other
- The role of Git in this application
- What "real-time" means for multi-user systems

## 📖 What is a PDM System?

### The Problem It Solves

Imagine you're working at a manufacturing company with 50 engineers. Everyone creates CAM files (like blueprints for CNC machines). Without a PDM system:

❌ **Chaos happens:**
- "Wait, which version is the latest?"
- "Who's editing this file right now?"
- "I just spent 3 hours updating a file someone else already updated!"
- "We accidentally manufactured using the old design!"

✅ **PDM System provides:**
- **Version Control**: Every change is tracked, you can go back in time
- **Check-out/Check-in**: Only one person can edit at a time (like library books)
- **Real-time Updates**: Everyone sees changes immediately
- **Audit Trail**: Who changed what, when, and why

### Real-World Analogy

Think of it like Google Docs for CAM files, but with stricter rules:
- **Google Docs**: Multiple people can edit simultaneously
- **Our PDM**: Only one person can "check out" and edit a file at a time
- **Why?**: CAM files are binary (not text), so we can't merge conflicts like code

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (Vanilla JavaScript + Tailwind CSS)       │   │
│  │  - UI Components (File cards, modals, buttons)      │   │
│  │  - State Management (Pub/Sub pattern)               │   │
│  │  - Real-time Updates (WebSocket connection)         │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/WebSocket
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER (Python)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                 │   │
│  │  - REST API Endpoints                                │   │
│  │  - WebSocket Handler                                 │   │
│  │  - Authentication (JWT tokens)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Service Layer                                       │   │
│  │  - GitRepository (talks to Git)                      │   │
│  │  - MetadataManager (file descriptions, locks)        │   │
│  │  - UserAuth (passwords, JWT tokens)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Git Commands
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL GIT REPOSITORY                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  .locks/          (who has what checked out)         │   │
│  │  .meta/           (file descriptions, revisions)      │   │
│  │  *.mcam, *.vnc    (actual CAM files)                 │   │
│  │  .link            (file references/shortcuts)         │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Git Push/Pull
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    GITLAB (REMOTE)                           │
│  - Single source of truth                                    │
│  - Git LFS stores large binary files                         │
│  - All users sync through here                               │
└─────────────────────────────────────────────────────────────┘
```

## 🧩 Component Breakdown

### 1. Frontend (What Users See)

**Technology**: Vanilla JavaScript (no React, Vue, or Angular)

**Why vanilla JavaScript?**
- ✅ **Faster**: No framework overhead
- ✅ **Easier to understand**: See exactly what happens
- ✅ **More control**: No "magic" happening behind the scenes
- ✅ **Smaller bundle**: Loads instantly

**Main Components**:
```
frontend/
├── index.html              (The single page the user sees)
├── js/
│   ├── main.js            (App entry point, sets up everything)
│   ├── state/
│   │   └── store.js       (Centralized state management)
│   ├── services/
│   │   ├── auth.js        (Login/logout)
│   │   ├── websocket.js   (Real-time connection)
│   │   └── api/
│   │       └── service.js (All API calls)
│   ├── components/
│   │   ├── FileCard.js    (Shows one file with buttons)
│   │   ├── Modal.js       (Popup dialogs)
│   │   └── ...            (More UI components)
│   └── utils/
│       └── helpers.js     (Utility functions)
```

### 2. Backend (The Server)

**Technology**: FastAPI (Modern Python web framework)

**Why FastAPI?**
- ✅ **Fast**: One of the fastest Python frameworks
- ✅ **Modern**: Built for async/await
- ✅ **Automatic Docs**: Generates API documentation automatically
- ✅ **Type Safety**: Uses Python type hints for validation

**Main Structure**:
```
backend/
├── main.py                    (App entry point)
├── app/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── files.py      (File operations: upload, download, checkout)
│   │   │   ├── auth.py       (Login, logout, password)
│   │   │   ├── admin.py      (Admin-only operations)
│   │   │   └── websocket.py  (Real-time updates)
│   │   └── dependencies.py   (Shared logic like "get current user")
│   ├── services/
│   │   ├── git_service.py    (All Git operations)
│   │   ├── lock_service.py   (File locking logic)
│   │   └── ...
│   ├── core/
│   │   ├── security.py       (JWT, passwords)
│   │   └── config.py         (App settings)
│   └── models/
│       └── schemas.py        (Data structures for API)
```

### 3. Data Layer (Git Repository)

**Why Git?**

Instead of a traditional database (like PostgreSQL), we use Git because:

✅ **Built-in Version Control**: Git already tracks changes perfectly
✅ **Branching/Merging**: Can create isolated workspaces
✅ **Distributed**: Each user has a full copy (backup!)
✅ **Audit Trail**: Git log shows who changed what
✅ **Industry Standard**: Engineers already understand it

**What's Stored in Git?**

```
repository/
├── .git/                      (Git's internals - don't touch!)
├── .locks/                    (JSON files: who has what checked out)
│   ├── 1234567_mcam.lock
│   └── 9876543_vnc.lock
├── .meta/                     (JSON files: descriptions, revisions)
│   ├── 1234567.mcam.json
│   └── 9876543.vnc.json
├── 1234567.mcam               (Actual CAM file)
├── 9876543.vnc                (Another CAM file)
└── 5555555.link               (JSON file pointing to another file)
```

## 🔄 Data Flow Example: Checking Out a File

Let's trace what happens when User A clicks "Checkout" on file `1234567.mcam`:

```
1. USER CLICKS BUTTON
   └─> Frontend: button click event fires

2. FRONTEND SHOWS MODAL
   └─> User types: "Updating dimensions for client XYZ"

3. FRONTEND SENDS API REQUEST
   POST /files/1234567.mcam/checkout
   Body: { user: "john", message: "Updating dimensions for client XYZ" }

4. BACKEND RECEIVES REQUEST
   ├─> Validates JWT token (is user logged in?)
   ├─> Checks if file is already locked
   │   └─> If locked: Return error 409 "Already checked out"
   │   └─> If not locked: Continue...

5. CREATE LOCK FILE
   ├─> Write: .locks/1234567_mcam.lock
   │   {
   │     "file": "1234567.mcam",
   │     "user": "john",
   │     "timestamp": "2025-10-12T14:30:00Z",
   │     "message": "Updating dimensions for client XYZ"
   │   }

6. COMMIT TO GIT
   ├─> Stage: .locks/1234567_mcam.lock
   ├─> Commit: "CHECKOUT: 1234567.mcam by john - Updating dimensions..."
   ├─> Push: Send commit to GitLab

7. BROADCAST TO ALL USERS (via WebSocket)
   ├─> Send message: { type: "FILE_LIST_UPDATED" }
   ├─> All connected browsers receive it

8. EVERYONE'S FRONTEND REFRESHES
   ├─> User A sees: "You have this file checked out" (blue button)
   ├─> User B sees: "Locked by john - Updating dimensions..." (status button)

9. BACKEND RESPONDS TO USER A
   └─> { status: "success", message: "File checked out" }

10. FRONTEND SHOWS NOTIFICATION
    └─> Green toast: "Checked out 1234567.mcam"
```

**Time elapsed**: ~2-3 seconds

**Key Points**:
- ✅ Git ensures only one lock exists (atomic operations)
- ✅ WebSocket ensures everyone sees the update immediately
- ✅ Lock message helps team coordination
- ✅ Everything is tracked in Git history

## 💡 Key Architectural Decisions

### Decision 1: Why No Database?

**We could have used PostgreSQL/MySQL, but we chose Git instead.**

**Advantages**:
- ✅ Simpler deployment (one less service to manage)
- ✅ Built-in version control (don't need to build it)
- ✅ Every user has offline access (local Git repo)
- ✅ Easy backups (just clone the repo)

**Trade-offs**:
- ❌ Slower than database for queries (acceptable for 50 users)
- ❌ Can't do complex SQL queries (we don't need them)
- ❌ Git repo grows over time (solved with Git LFS)

### Decision 2: Why Vanilla JavaScript Instead of React?

**Advantages**:
- ✅ Faster load times (no framework to download)
- ✅ Easier to understand for new developers
- ✅ More direct control over DOM
- ✅ No build step needed (can edit and refresh)

**Trade-offs**:
- ❌ More boilerplate code (we write our own components)
- ❌ No built-in state management (we built our own)

### Decision 3: Why WebSockets for Real-time Updates?

**Alternatives Considered**:
- ❌ **Polling** (frontend asks "any updates?" every 5 seconds)
  - Wastes bandwidth, slower, more server load
- ❌ **Server-Sent Events** (server pushes to frontend)
  - One-way only, WebSocket is bidirectional
- ✅ **WebSockets** (persistent two-way connection)
  - Instant updates, efficient, bidirectional

### Decision 4: Why FastAPI Instead of Flask/Django?

**Advantages**:
- ✅ Modern async/await support (better for WebSockets)
- ✅ Automatic API documentation (OpenAPI/Swagger)
- ✅ Type validation (Pydantic models)
- ✅ Better performance than Flask
- ✅ Simpler than Django (no ORM needed)

## 🎓 Key Concepts Explained

### 1. REST API

**What it is**: A way for frontend and backend to communicate using HTTP

**Example**:
```
GET  /files              → Get list of all files
POST /files/upload       → Upload a new file
POST /files/123/checkout → Check out file 123
GET  /files/123/download → Download file 123
```

**Think of it as**: Restaurant menu - you order (request), kitchen prepares (server processes), waiter brings food (response)

### 2. WebSocket

**What it is**: A persistent, two-way connection between browser and server

**Difference from REST**:
- **REST**: You ask a question, get an answer, connection closes
- **WebSocket**: Phone call - connection stays open, both sides can talk anytime

**Why we need it**: So when User A checks out a file, User B's screen updates instantly

### 3. JWT (JSON Web Token)

**What it is**: A way to prove you're logged in without storing sessions

**How it works**:
```
1. User logs in with password
2. Server creates JWT: "eyJ0eXAiOiJKV1..." (encrypted info)
3. Browser stores JWT in cookie
4. Every request includes JWT
5. Server verifies JWT (if valid, user is authenticated)
```

**Benefit**: Server doesn't need to remember who's logged in (stateless)

### 4. State Management (Pub/Sub Pattern)

**Problem**: Multiple components need to know about the same data

**Solution**: Centralized state with subscriptions

```javascript
// Bad: Passing data everywhere
function FileCard(data) {
  function FileButtons(data) {
    function CheckoutButton(data) {
      // Data passed through 3 layers!
    }
  }
}

// Good: Subscribe to central state
state.subscribe((newState) => {
  // Any component can react to state changes
  renderFileList(newState.files);
});
```

### 5. Git LFS (Large File Storage)

**Problem**: Git is slow with large binary files

**Solution**: Git LFS stores files separately

```
Without LFS:
├── .git/objects/      (Full file stored here - repo grows huge!)
└── file.mcam          (200 MB CAM file)

With LFS:
├── .git/lfs/          (File stored here)
├── file.mcam          (Pointer file, only 100 bytes!)
│   "version https://git-lfs.github.com/spec/v1
│    oid sha256:abc123...
│    size 200000000"
```

**Benefit**: Git repo stays small, files only downloaded when needed

## 🧪 Understanding Multi-User Concurrency

**Challenge**: What if two users try to checkout the same file at the same time?

### Race Condition Example:

```
Time    User A                           User B
----    ------                           ------
10:00   Clicks "Checkout"
10:00   Backend checks: file unlocked ✓
10:00                                    Clicks "Checkout"
10:00                                    Backend checks: file unlocked ✓
10:01   Creates lock file
10:01                                    Creates lock file (CONFLICT!)
```

### Our Solution: Git as a Lock Manager

```python
# Atomic operation using Git
def create_lock(filename, user):
    # 1. Pull latest changes (get any new locks)
    git pull

    # 2. Check if lock exists
    if lock_file_exists(filename):
        raise "Already locked!"

    # 3. Create lock file
    write_lock_file(filename, user)

    # 4. Commit and push
    git add .locks/filename.lock
    git commit -m "CHECKOUT by {user}"
    git push  # This will FAIL if someone else pushed first!

    # 5. If push fails, rollback and retry
```

**Why this works**: Git's push operation is atomic - only one user's push succeeds

## 📊 Performance Considerations

**Q: Can this handle 50 concurrent users?**

**A: Yes!** Here's why:

| Operation | Time | Bottleneck |
|-----------|------|------------|
| List files | ~100ms | Git operation |
| Checkout | ~2s | Git push to GitLab |
| Download | ~5-10s | File size (LFS) |
| Real-time update | <100ms | WebSocket (instant) |

**Optimizations**:
- ✅ File list is cached (only re-fetched on Git changes)
- ✅ LFS files download on-demand (not all at once)
- ✅ WebSocket reduces polling (efficient network usage)
- ✅ Frontend state prevents unnecessary API calls

## 🎯 Chapter Summary

You've learned:

✅ **What** we're building: A multi-user PDM system for CAM files
✅ **Why** we made key architectural choices (Git instead of DB, vanilla JS, FastAPI)
✅ **How** components talk to each other (REST API, WebSocket, Git)
✅ **What** problems we're solving (version control, checkout/checkin, real-time updates)
✅ **How** we handle concurrency (Git as lock manager)

## 🤔 Knowledge Check

Before moving to Chapter 2, make sure you can answer:

1. What's the difference between REST API and WebSocket?
2. Why do we use Git instead of a traditional database?
3. What prevents two users from checking out the same file simultaneously?
4. What is Git LFS and why do we need it?
5. How does a JWT token work for authentication?

## 🚀 Next Steps

In **Chapter 2: Setting Up Your Development Environment**, you'll:
- Install Python, Git, and necessary tools
- Create a GitLab account and repository
- Set up your project folder structure
- Run your first FastAPI "Hello World"

**Ready?** Let's set up your development environment! →

---

**💡 Pro Tip**: If any concept is unclear, don't worry! It will make more sense as you code along. Sometimes understanding comes from doing, not just reading.
