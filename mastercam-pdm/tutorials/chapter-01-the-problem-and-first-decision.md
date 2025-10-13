# Chapter 1: The Problem & Our First Decision

**Time**: 20 minutes (reading, no coding yet)
**Goal**: Understand what we're building and make our first architectural decision

---

## 👋 Welcome! Let's Talk

Hey! So you want to build a file management system. Great! But before we write ANY code, let's talk about what we're actually trying to solve.

This is how real projects start - with a problem, not with code.

## 🤔 The Problem

**Imagine this scenario:**

You work at a manufacturing company. You have 50 engineers creating CAM files (these are instructions for CNC machines). Right now, everyone just saves files to a shared network drive:

```
\\shared-drive\cam-files\
├── part_1234.mcam
├── part_5678.mcam
├── part_1234_OLD.mcam
├── part_1234_FINAL.mcam
├── part_1234_FINAL_v2.mcam
└── part_1234_USE_THIS_ONE.mcam
```

**What's the problem?**

1. **No one knows which file is the latest**
   - Is it `part_1234.mcam` or `part_1234_USE_THIS_ONE.mcam`?

2. **People overwrite each other's work**
   - John edits `part_1234.mcam` from 9-10am
   - Sarah also edits `part_1234.mcam` from 9:30-11am
   - Sarah saves, and John's work is GONE

3. **No history**
   - "The version from last Tuesday was better, can we go back?"
   - "Who changed this and why?"

4. **No coordination**
   - You spend 3 hours updating a file
   - Come to find out someone else updated it yesterday
   - You just wasted 3 hours

**Sound familiar?** This is what happens without version control and coordination.

## 💡 What We Need to Build

We need a system where:

✅ Only ONE person can edit a file at a time (like checking out a library book)
✅ Every change is tracked (who, when, why)
✅ Everyone can see who's working on what
✅ Updates happen in real-time (no refreshing)
✅ Easy to go back to previous versions

**This is called a PDM system** (Product Data Management)

## 🎯 Our First Big Decision

Now, here's where software engineering gets interesting. There are MANY ways to build this. Let's think through our options like real engineers.

### Decision #1: How Do We Store Files?

**Option A: Database (PostgreSQL/MySQL)**
```
Files Table:
├── id: 1
├── filename: part_1234.mcam
├── content: [BLOB - binary data]
├── version: 5
├── uploaded_by: john
└── uploaded_at: 2025-10-12
```

**Pros:**
- ✅ Fast queries
- ✅ ACID guarantees (data integrity)
- ✅ Can do complex searches

**Cons:**
- ❌ Database gets HUGE with large files
- ❌ We have to BUILD version control ourselves
- ❌ Need to manage database backups
- ❌ One more service to deploy and maintain

---

**Option B: File System + Git**
```
Git Repository:
├── .git/ (version history)
├── part_1234.mcam
├── part_5678.mcam
└── .locks/
    └── part_1234.lock (who has it checked out)
```

**Pros:**
- ✅ Version control is FREE (Git does it)
- ✅ History/rollback built-in
- ✅ Engineers already understand Git
- ✅ Easy backups (just clone the repo)
- ✅ No database to manage

**Cons:**
- ❌ Slower for queries than database
- ❌ Git repo grows over time
- ❌ Can't do SQL-like queries

---

### 🤝 Let's Decide Together

**My Mentor Perspective:**

I've built both types of systems. Here's what I learned:

For a file management system with **50 users**, I'd choose **Option B (Git)**.

**Why?**

1. **We get SO much for free**
   - Version control (don't have to build it)
   - Merge/branch capability (future feature)
   - Audit trail (git log shows everything)
   - Backups (every clone is a backup)

2. **Simpler deployment**
   - One less service (no database server)
   - Less infrastructure to manage
   - Easier for engineers to understand

3. **Trade-offs are acceptable**
   - Slower queries? With 50 users and hundreds of files, it's fast enough
   - Repo grows? We'll use Git LFS (Large File Storage) for big files
   - Can't do SQL? We don't need complex queries for this use case

**When would I choose a database?**
- If we had 10,000 users
- If we needed complex reporting/analytics
- If we had millions of small files
- If files changed constantly (Git commits would be overwhelming)

**For our use case**: Git wins.

### Decision #2: Where Does Git Repo Live?

**Option A: On the Server**
```
Server has ONE git repo
All users read/write to it
```
**Pros:** ✅ Simple
**Cons:** ❌ Slow (server is bottleneck), ❌ No offline access

---

**Option B: Everyone Has a Copy**
```
Each user has a local git repo
Changes sync through GitLab/GitHub
```
**Pros:** ✅ Fast (local operations), ✅ Offline access, ✅ Distributed
**Cons:** ❌ Slightly more complex

**We'll choose B** because speed matters, and Git is designed for this.

### Decision #3: What About Large Binary Files?

CAM files can be 200MB+. Git is slow with large binary files.

**Solution: Git LFS**

Git LFS (Large File Storage) is a Git extension that:
- Stores large files separately
- Keeps tiny "pointer files" in Git
- Downloads files only when needed

```
Without LFS:
└── part_1234.mcam (200MB stored in .git/objects)
    └── .git folder grows to 2GB with 10 files!

With LFS:
└── part_1234.mcam (100 byte pointer file)
    └── Actual 200MB file stored on GitLab's LFS server
    └── .git folder stays small!
```

**We'll use Git LFS** for all `.mcam`, `.vnc`, and `.emcam` files.

## 🏗️ High-Level Plan

Based on our decisions, here's what we're building:

```
User's Browser (Frontend)
        ↕
    REST API
        ↕
   Backend Server (FastAPI)
        ↕
   Local Git Repo
        ↕
   GitLab (Remote)
```

**Data Flow Example:**

```
User clicks "Checkout file 1234"
    ↓
Frontend sends: POST /files/1234/checkout
    ↓
Backend:
  1. Creates .locks/1234.lock file
  2. Commits to Git: "CHECKOUT: 1234 by john"
  3. Pushes to GitLab
    ↓
GitLab has the lock now
    ↓
Backend broadcasts "file list changed" via WebSocket
    ↓
All users' browsers refresh
    ↓
Everyone sees: "1234 locked by john"
```

## 🎓 Key Concepts You Just Learned

### 1. Engineering Decision-Making

Notice we didn't just pick the "best" technology. We:
1. Listed options
2. Identified pros/cons
3. Considered our specific needs (50 users, large files, version control)
4. Chose the option that fits OUR use case

**This is engineering thinking**: There's no "best" - only "best for this situation."

### 2. Trade-offs Are Normal

Every decision has trade-offs:
- Git is slower than a database ➜ But we get version control free
- Git LFS adds complexity ➜ But it solves the large file problem

**Good engineers**: Recognize trade-offs and choose consciously
**Bad engineers**: Don't realize there are trade-offs

### 3. Start with Simple Decisions

We made 3 big decisions:
1. Git instead of database
2. Distributed Git repos
3. Git LFS for large files

We didn't decide:
- What frontend framework? (we'll discuss later)
- What authentication system? (we'll discuss when we need it)
- What hosting provider? (we'll discuss when we deploy)

**Don't make decisions before you need to.** Make them when the problem is in front of you.

## 🤔 Think About This

Before moving to Chapter 2, consider:

**Question 1**: "Why not just use Google Drive or Dropbox?"

<details>
<summary>My Answer</summary>

Good question! They're great for documents, but:
- ❌ No checkout/checkin (anyone can edit anytime → conflicts)
- ❌ Version history is limited (not full Git history)
- ❌ No API for custom workflows
- ❌ Can't customize permissions precisely
- ❌ Costs add up with 50 users and large files

We need more control for engineering files.
</details>

**Question 2**: "If Git is slow with 10,000 users, when do we switch to a database?"

<details>
<summary>My Answer</summary>

**Red flags that you need a database:**
1. Queries are taking >5 seconds
2. Git repo is >10GB even with LFS
3. Users complaining about speed
4. Need complex reports/analytics

**How to switch:**
1. Keep Git for version control
2. Add database for metadata (file info, locks)
3. Sync Git commits → database
4. API reads from database (fast queries)
5. API writes to both Git and database

This is called a **hybrid approach** - best of both worlds!
</details>

**Question 3**: "What if two users click checkout at the EXACT same time?"

<details>
<summary>My Answer</summary>

Great question! This is a **race condition**.

**Git saves us:**
```
User A: Creates lock file, pushes to GitLab ✓
User B: Creates lock file, tries to push...
        GitLab says "ERROR: Someone pushed first!"
        Backend sees error, rolls back User B's lock
        User B gets error: "Already checked out"
```

Git's push operation is **atomic** - only one succeeds.

We'll handle this properly in the code later!
</details>

## 📝 Chapter Summary

**What We Decided:**
1. ✅ Use Git instead of a database (version control is free)
2. ✅ Store Git repo locally, sync through GitLab (distributed = fast)
3. ✅ Use Git LFS for large binary files (keeps repo small)

**What We Learned:**
1. Make decisions based on requirements, not trends
2. Every choice has trade-offs - choose consciously
3. Don't over-plan - decide when needed

**Engineering Mindset:**
- Think through options before coding
- Consider the scale (50 users, not 50,000)
- Simple solutions are often better than complex ones

## 🚀 Next: Let's Set Up

In **Chapter 2**, we'll:
- Install Python, Git, Git LFS
- Create a GitLab account and repository
- Set up our project folder
- **Write our first line of code** (a simple API endpoint)

**Ready to code?** Let's get your environment set up →

---

**💭 Mentor Note:**

> "Notice we didn't write ANY code yet. That's on purpose. The best code is code you don't have to write because you chose the right architecture. We just saved ourselves weeks of work by choosing Git instead of building version control from scratch."
>
> "In Chapter 2, we'll set up the basics. Then in Chapter 3, we'll write our first endpoint. I promise we'll code soon - but these foundational decisions matter!"

**Enjoy the process. Building software is about solving problems, not just writing code.**
