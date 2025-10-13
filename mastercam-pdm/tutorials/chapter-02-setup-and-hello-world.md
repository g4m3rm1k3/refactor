# Chapter 2: Setup & Hello World

**Time**: 45-60 minutes
**Goal**: Install tools, write your first API endpoint, see it work in browser

---

## 👋 Let's Get Coding!

Alright, enough talking - let's write some code! But first, we need to set up our workspace.

**Today's Goal**: By the end of this chapter, you'll have a working API that responds "Hello World" when you visit it in your browser.

## 🛠️ What We Need (And Why)

### Tool #1: Python

**What**: Programming language for our backend
**Why**: FastAPI (our framework) is written in Python
**Version**: 3.8 or higher

**Check if you have it:**
```bash
python --version
```
Should show: `Python 3.8.x` or higher

**Don't have it?** Download from [python.org](https://python.org)

---

### Tool #2: pip

**What**: Python's package installer (like an app store for Python libraries)
**Why**: We'll install FastAPI and other libraries with it
**Good news**: Comes with Python automatically!

**Check if you have it:**
```bash
pip --version
```

---

### Tool #3: Git

**What**: Version control system
**Why**: Our entire data storage strategy relies on Git!

**Check if you have it:**
```bash
git --version
```

**Don't have it?** Download from [git-scm.com](https://git-scm.com)

---

### Tool #4: Code Editor

**What**: Where you write code
**Recommendation**: VS Code ([code.visualstudio.com](https://code.visualstudio.com))
**Why VS Code?**: Free, popular, great extensions

**Alternatives**: Any text editor works (Sublime, Atom, even Notepad++!)

---

## 📁 Creating Our Project Folder

Let's start simple. We'll create ONE folder, ONE file.

**Open your terminal** (Command Prompt on Windows, Terminal on Mac/Linux)

```bash
# Create a folder for our project
mkdir pdm-tutorial
cd pdm-tutorial
```

**What we have so far:**
```
pdm-tutorial/
└── (empty)
```

## 🐍 Installing FastAPI

**Now let's install FastAPI:**

```bash
pip install fastapi uvicorn
```

**What did we just install?**

1. **fastapi** - The web framework (handles requests, routing, etc.)
2. **uvicorn** - The web server (actually runs our code)

**Think of it like:**
- FastAPI = The restaurant menu and kitchen
- Uvicorn = The restaurant building itself

**This will take 30 seconds to install...**

## 📝 Our First File: main.py

Let's create ONE file and write our first API.

**Create a file called `main.py` in your `pdm-tutorial` folder:**

```bash
# Create the file (or just create it in your code editor)
touch main.py
```

**Now open `main.py` in your code editor and type this:**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello World"}
```

**That's it. 6 lines. Let's understand each one:**

---

### Line 1: Importing FastAPI
```python
from fastapi import FastAPI
```
**What**: Importing the FastAPI class
**English**: "Hey Python, go get the FastAPI tool from the fastapi library"
**Why**: We need FastAPI to build our web API

---

### Line 3: Creating an App
```python
app = FastAPI()
```
**What**: Creating a FastAPI application instance
**English**: "Create a new web application and call it 'app'"
**Why**: This `app` is the foundation - everything we build goes on this

**Analogy**: Think of this as creating your restaurant. The building is ready, now we add menu items.

---

### Line 5: Creating an Endpoint (The Interesting Part!)
```python
@app.get("/")
```
**What**: A decorator that creates an endpoint
**English**: "When someone visits the root URL (/), run the function below"

**Let's break this down:**
- `@app` - We're adding to our app
- `.get` - This handles GET requests (the browser's default when you visit a URL)
- `("/")` - The path/route (/ means the root, like visiting example.com/)

**Analogy**: This is like adding a menu item. "When someone orders '/breakfast', call the breakfast chef."

---

### Line 6-7: The Function
```python
def hello():
    return {"message": "Hello World"}
```
**What**: A normal Python function
**English**: "When called, return a dictionary with a message"

**Important**: FastAPI automatically converts this dictionary to JSON!

**JSON Output:**
```json
{
  "message": "Hello World"
}
```

---

## 🚀 Running Our API

**Let's see it work!**

In your terminal (make sure you're in the `pdm-tutorial` folder):

```bash
uvicorn main:app --reload
```

**What does this mean?**
- `uvicorn` - Run the web server
- `main` - Look in the `main.py` file
- `:app` - Use the `app` variable from that file
- `--reload` - Restart automatically when we change code (VERY useful!)

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**🎉 IT'S ALIVE!**

## 🌐 Testing in Your Browser

**Open your browser and go to:**
```
http://localhost:8000
```

**You should see:**
```json
{
  "message": "Hello World"
}
```

**CONGRATULATIONS!** You just built and ran a web API!

---

## 🎓 Let's Understand What Just Happened

### The Journey of a Request

```
1. Browser
   └─> "Hey, I want to visit http://localhost:8000"

2. Operating System
   └─> "OK, localhost means this computer, port 8000"

3. Uvicorn (Web Server)
   └─> "I'm listening on port 8000. Got a request!"
   └─> "It's a GET request to path '/'"

4. FastAPI
   └─> "I have a function for GET /"
   └─> "Let me run the hello() function"

5. hello() function
   └─> "I return {'message': 'Hello World'}"

6. FastAPI
   └─> "Convert to JSON, add headers"

7. Uvicorn
   └─> "Send response back to browser"

8. Browser
   └─> "Got JSON! Display it!"
```

**Time elapsed**: ~5 milliseconds

### Key Concepts

**1. HTTP Methods**
- `GET` - Retrieve data (like viewing a webpage)
- `POST` - Send data (like submitting a form)
- `DELETE` - Remove data
- `PUT` - Update data

For now, we only used `GET`.

**2. Endpoints/Routes**
`/` is an endpoint. We can have many:
```python
@app.get("/")          # http://localhost:8000/
@app.get("/files")     # http://localhost:8000/files
@app.get("/users")     # http://localhost:8000/users
```

**3. JSON**
JavaScript Object Notation - a way to send data as text:
```python
# Python Dictionary
{"message": "Hello"}

# Becomes JSON (text)
'{"message":"Hello"}'
```

Browsers and JavaScript love JSON!

## 🧪 Let's Experiment!

**Try changing the message:**

```python
def hello():
    return {"message": "Welcome to my PDM system!"}
```

**Save the file. Notice:**
- The terminal shows "Reloading..."
- Your change is live!

**Refresh your browser** - you'll see the new message!

**Try adding more data:**

```python
def hello():
    return {
        "message": "Hello World",
        "version": "1.0",
        "status": "running"
    }
```

**Refresh browser:**
```json
{
  "message": "Hello World",
  "version": "1.0",
  "status": "running"
}
```

Cool, right?

## 🎯 Let's Add Another Endpoint

**Add this to your `main.py` (below the first function):**

```python
@app.get("/ping")
def ping():
    return {"status": "alive"}
```

**Your full file now:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello World"}

@app.get("/ping")
def ping():
    return {"status": "alive"}
```

**Save and visit:**
```
http://localhost:8000/ping
```

**You'll see:**
```json
{
  "status": "alive"
}
```

**You just created your second API endpoint!**

## 🎁 Bonus: Auto-Generated Docs

FastAPI gives you free API documentation!

**Visit:**
```
http://localhost:8000/docs
```

**You'll see:**
- Interactive API documentation
- All your endpoints listed
- Ability to test them right there!

**This is called Swagger UI** - it's automatically generated from your code!

**Try it:**
1. Click on "GET /"
2. Click "Try it out"
3. Click "Execute"
4. See the response!

**THIS IS AMAZING for testing APIs without writing frontend code!**

## 🐛 Common Errors & Solutions

### Error 1: "Address already in use"
```
ERROR:    [Errno 48] Address already in use
```
**Cause**: Something else is using port 8000
**Solution**: Use a different port:
```bash
uvicorn main:app --reload --port 8001
```

---

### Error 2: "ModuleNotFoundError: No module named 'fastapi'"
```
ModuleNotFoundError: No module named 'fastapi'
```
**Cause**: FastAPI not installed
**Solution**: Run:
```bash
pip install fastapi uvicorn
```

---

### Error 3: "Cannot find 'app' in 'main'"
```
ERROR:    Error loading ASGI app. Import string "main:app" doesn't point to an ASGI application.
```
**Cause**: Typo in filename or variable name
**Solution**:
- Make sure file is named `main.py`
- Make sure you have `app = FastAPI()` in the file

---

## 📚 What We've Learned

**Concepts:**
- ✅ HTTP requests/responses
- ✅ JSON format
- ✅ API endpoints/routes
- ✅ Decorators (`@app.get`)
- ✅ Auto-reload for development

**Skills:**
- ✅ Install Python packages
- ✅ Create a FastAPI application
- ✅ Define API endpoints
- ✅ Run a web server
- ✅ Test APIs in browser

**Files created:**
```
pdm-tutorial/
└── main.py (11 lines)
```

## 🎯 Challenge (Optional)

Try adding these endpoints yourself:

**1. Info Endpoint:**
```python
@app.get("/info")
def info():
    return {
        "app_name": "PDM System",
        "created_by": "Your Name",
        "purpose": "Learning full-stack development"
    }
```

**2. Time Endpoint:**
```python
from datetime import datetime

@app.get("/time")
def current_time():
    return {
        "current_time": datetime.now().isoformat()
    }
```

Test them at:
- http://localhost:8000/info
- http://localhost:8000/time

## 🚀 Next Steps

In **Chapter 3**, we'll:
- Actually list files from a folder
- Start building toward our PDM system
- Learn about **path parameters** (like `/files/1234`)
- Return real data, not just static messages

**You now have a working API!** Everything else builds on this foundation.

---

**💭 Mentor Note:**

> "Notice how simple this was? Six lines of code, and you have a working web API. That's the power of good frameworks.
>
> "But don't let the simplicity fool you - you just learned:
> - Client-server architecture
> - HTTP protocol basics
> - JSON data format
> - API endpoint creation
>
> "These concepts power EVERY web application on the internet.
>
> "In the next chapter, we'll make this do something useful - listing actual files from a folder. That's when things get real!"

**Great work! Take a break, then let's list some files** →
