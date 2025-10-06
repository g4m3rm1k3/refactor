// frontend/js/state/store.js

// The single source of truth for our application's state.
const _state = {
  currentUser: null,
  isAdmin: false,
  isAuthenticated: false, // <-- ADD THIS LINE
  groupedFiles: {},
  isConfigured: false,
  // We can add anything else our app needs to remember here.
};

// A list of all our "subscriber" functions.
const _listeners = [];

/**
 * The main engine of our store. It updates the state and notifies all subscribers.
 * This is the "publish" function.
 * @param {Object} partialState - An object with the parts of the state you want to change.
 */
export function setState(partialState) {
  // Merge the new state properties into our existing state object.
  Object.assign(_state, partialState);

  // Notify all listeners that the state has changed!
  // We pass them the new, complete state object.
  for (const listener of _listeners) {
    listener(_state);
  }
}

/**
 * Returns a copy of the current state.
 */
export function getState() {
  return { ..._state };
}

/**
 * Allows a function (like a UI component's render function) to "subscribe" to state updates.
 * @param {Function} listener - A function that will be called whenever the state changes.
 */
export function subscribe(listener) {
  _listeners.push(listener);
}
