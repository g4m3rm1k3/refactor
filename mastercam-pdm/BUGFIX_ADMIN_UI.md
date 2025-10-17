# Admin UI Bug Fix

## Issue
The admin configuration UI was throwing a 404 error:
```
GET http://localhost:8001/static/js/services/ui.js net::ERR_ABORTED 404 (Not Found)
```

## Root Cause
The `adminConfig.js` file was importing from a non-existent `ui.js` file:
```javascript
import { showNotification, showModal, closeModal } from '../services/ui.js';
```

The project doesn't have a `services/ui.js` file. The UI utilities are actually in:
- `utils/helpers.js` - Contains `showNotification()`
- `components/Modal.js` - Contains `Modal` class

## Fix Applied

Updated [adminConfig.js](backend/static/js/components/adminConfig.js):

**Before:**
```javascript
import { showNotification, showModal, closeModal } from '../services/ui.js';
```

**After:**
```javascript
import { showNotification } from '../utils/helpers.js';
import { Modal } from './Modal.js';

let currentModal = null;

function showModal(content) {
  if (currentModal) {
    currentModal.close();
  }
  currentModal = new Modal(content.firstElementChild || content);
  currentModal.show();
}

function closeModal() {
  if (currentModal) {
    currentModal.close();
    currentModal = null;
  }
}
```

## Status
✅ **FIXED** - The admin UI should now load without errors.

## Testing
1. Start the application: `python run.py`
2. Login as admin
3. Click Settings (⚙️) → Admin tab (🛡️)
4. Verify no console errors
5. Try adding a pattern/repository to verify modals work

## Files Modified
- [backend/static/js/components/adminConfig.js](backend/static/js/components/adminConfig.js)
