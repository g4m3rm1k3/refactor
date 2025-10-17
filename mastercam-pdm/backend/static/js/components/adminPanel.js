/**
 * Admin Panel - Complete Administration Interface
 * Combines config management, user management, and maintenance tools
 */

console.log('[AdminPanel] Loading adminPanel.js module...');

import { apiService } from '../api/service.js';
import { showNotification } from '../utils/helpers.js';
import { Modal } from './Modal.js';

console.log('[AdminPanel] Module loaded successfully!');

let currentModal = null;
let initialized = false;

/**
 * Show modal helper
 */
function showModal(content) {
  if (currentModal) {
    currentModal.close();
  }
  // If content is already a DOM element (like a div), use it directly
  // If it's a DocumentFragment (from template.content.cloneNode), extract firstElementChild
  const element = content instanceof Element ? content : (content.firstElementChild || content);
  currentModal = new Modal(element);
  currentModal.show();
}

/**
 * Close modal helper
 */
function closeModal() {
  if (currentModal) {
    currentModal.close();
    currentModal = null;
  }
}

/**
 * Initialize admin panel
 */
export function initAdminPanel() {
  console.log('[AdminPanel] initAdminPanel() called');

  // Listen for the custom event when admin tabs are created
  window.addEventListener('adminTabsReady', () => {
    console.log('[AdminPanel] adminTabsReady event received, attaching listeners...');
    setupAdminTabListeners();
  });

  // Also try to set up immediately in case tabs already exist
  setupAdminTabListeners();
}

/**
 * Set up event listeners for admin tabs
 */
function setupAdminTabListeners() {
  const adminTabButton = document.querySelector('#adminTab');
  const usersTabButton = document.querySelector('#usersTab');

  console.log('[AdminPanel] Admin tab button found:', !!adminTabButton);

  // Hide the Users tab - we'll manage users through Access tab instead
  if (usersTabButton) {
    usersTabButton.style.display = 'none';
    console.log('[AdminPanel] Users tab hidden (users managed in Access tab)');
  }

  if (adminTabButton && !adminTabButton.dataset.listenerAttached) {
    adminTabButton.addEventListener('click', () => {
      console.log('[AdminPanel] Admin tab clicked');

      // Always reload the config and re-attach listeners
      setTimeout(() => {
        // Re-attach event listeners each time (in case DOM was replaced)
        attachAdminEventListeners();

        // Load config (show toast only on first load)
        loadAdminConfig(!initialized);

        initialized = true;
      }, 200);
    });
    adminTabButton.dataset.listenerAttached = 'true';
    console.log('[AdminPanel] ✅ Admin tab click listener attached');
  }
}

/**
 * Helper to safely attach event listener (removes old ones first)
 */
function safeAttachListener(elementId, handler, description) {
  const element = document.getElementById(elementId);
  if (!element) return false;

  // Check if already attached to avoid duplicates
  if (element.dataset.handlerAttached === 'true') {
    return true;
  }

  element.addEventListener('click', handler);
  element.dataset.handlerAttached = 'true';
  console.log(`[Admin] ✅ ${description} attached`);
  return true;
}

/**
 * Attach all admin event listeners
 */
function attachAdminEventListeners() {
  console.log('[Admin] Attaching event listeners...');

  // Admin subtab switching
  const adminSubtabs = document.querySelectorAll('.admin-subtab');
  adminSubtabs.forEach(tab => {
    if (tab.dataset.handlerAttached === 'true') return;

    tab.addEventListener('click', () => switchAdminSubtab(tab.dataset.tab));
    tab.dataset.handlerAttached = 'true';
  });

  // Pattern management buttons
  safeAttachListener('addPatternBtn', () => showPatternModal(), 'Add Pattern button');

  // Repository management buttons
  safeAttachListener('addRepoBtn', () => showRepositoryModal(), 'Add Repository button');

  // User access management buttons
  safeAttachListener('addUserAccessBtn', () => showUserAccessModal(), 'Add User Access button');

  // Maintenance buttons
  safeAttachListener('createBackupBtn', handleCreateBackup, 'Create Backup button');
  safeAttachListener('cleanupLfsBtn', handleCleanupLFS, 'Cleanup LFS button');
  safeAttachListener('exportRepoBtn', handleExportRepo, 'Export Repo button');
  safeAttachListener('resetRepoBtn', handleResetRepo, 'Reset Repo button');
  safeAttachListener('reloadConfigBtn', () => loadAdminConfig(true), 'Reload Config button');

  console.log('[Admin] All event listeners attached successfully');
}

// ============================================================================
// ADMIN CONFIGURATION (Patterns, Repos, Access)
// ============================================================================

let currentConfig = null;

/**
 * Load admin configuration from API
 */
export async function loadAdminConfig(showToast = true) {
  console.log('[Admin] Loading configuration...');

  try {
    const config = await apiService.getAdminConfig();
    currentConfig = config;
    console.log('[Admin] Configuration loaded:', config);

    // Update config info section
    updateConfigInfo(config);

    // Load each section
    loadPatterns(config.filename_patterns || []);
    loadRepositories(config.repositories || []);
    loadUserAccess(config.user_access || []);

    if (showToast) {
      showNotification('Admin configuration loaded successfully', 'success');
    }
  } catch (error) {
    console.error('[Admin] Failed to load config:', error);

    // Show graceful fallback
    const patternsListEl = document.getElementById('patternsList');
    const repositoriesListEl = document.getElementById('repositoriesList');
    const userAccessListEl = document.getElementById('userAccessList');

    if (patternsListEl) {
      patternsListEl.innerHTML = `
        <div class="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <p class="text-sm"><i class="fa-solid fa-exclamation-triangle mr-2"></i>
          <strong>Configuration not yet initialized.</strong></p>
          <p class="text-sm mt-2">Using default settings. Click "Add Pattern" to customize.</p>
        </div>
      `;
    }

    if (repositoriesListEl) {
      repositoriesListEl.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          <i class="fa-solid fa-info-circle text-3xl mb-2"></i>
          <p>Using default repository configuration</p>
        </div>
      `;
    }

    if (userAccessListEl) {
      userAccessListEl.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          <i class="fa-solid fa-info-circle text-3xl mb-2"></i>
          <p>All users have access to all repositories (default)</p>
        </div>
      `;
    }
  }
}

/**
 * Update configuration info display
 */
function updateConfigInfo(config) {
  const versionEl = document.getElementById('configVersion');
  const updatedByEl = document.getElementById('configUpdatedBy');
  const updatedAtEl = document.getElementById('configUpdatedAt');
  const pollingEl = document.getElementById('configPolling');

  if (versionEl) versionEl.textContent = config.version || '1.0.0';
  if (updatedByEl) updatedByEl.textContent = config.last_updated_by || 'N/A';
  if (updatedAtEl) {
    updatedAtEl.textContent = config.last_updated_at
      ? new Date(config.last_updated_at).toLocaleString()
      : 'N/A';
  }
  if (pollingEl) pollingEl.textContent = config.polling_interval_seconds || 30;
}

/**
 * Switch between admin subtabs
 */
function switchAdminSubtab(tabName) {
  console.log(`[Admin] Switching to ${tabName} tab`);

  // Update button states
  document.querySelectorAll('.admin-subtab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabName);
  });

  // Update content visibility
  document.querySelectorAll('.admin-subtab-content').forEach(content => {
    content.classList.add('hidden');
  });

  const contentMap = {
    patterns: 'adminPatterns',
    repositories: 'adminRepositories',
    access: 'adminAccess',
    maintenance: 'adminMaintenance'
  };

  const targetContent = document.getElementById(contentMap[tabName]);
  if (targetContent) {
    targetContent.classList.remove('hidden');
  }
}

/**
 * Load and display filename patterns
 */
function loadPatterns(patterns) {
  const container = document.getElementById('patternsList');
  if (!container) return;

  if (!patterns || patterns.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-500">
        <i class="fa-solid fa-inbox text-3xl mb-2"></i>
        <p>No patterns defined. Click "Add Pattern" to create one.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = patterns.map(pattern => `
    <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div class="flex justify-between items-start mb-2">
        <div class="flex-grow">
          <h5 class="font-semibold text-lg">${escapeHtml(pattern.name)}</h5>
          <p class="text-sm text-gray-600 dark:text-gray-400">${escapeHtml(pattern.description)}</p>
        </div>
        <button class="btn btn-danger text-sm ml-2" onclick="window.deletePattern('${escapeHtml(pattern.name)}')">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs mt-3">
        <div>
          <strong>Link Pattern:</strong>
          <code class="block mt-1 p-2 bg-gray-100 dark:bg-gray-700 rounded">${escapeHtml(pattern.link_pattern)}</code>
        </div>
        <div>
          <strong>File Pattern:</strong>
          <code class="block mt-1 p-2 bg-gray-100 dark:bg-gray-700 rounded">${escapeHtml(pattern.file_pattern)}</code>
        </div>
        <div>
          <strong>Max Length:</strong> ${pattern.max_stem_length}
        </div>
        <div>
          <strong>Valid Examples:</strong> ${pattern.example_valid?.join(', ') || 'N/A'}
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * Load and display repositories
 */
function loadRepositories(repositories) {
  const container = document.getElementById('repositoriesList');
  if (!container) return;

  if (!repositories || repositories.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-500">
        <i class="fa-solid fa-inbox text-3xl mb-2"></i>
        <p>No repositories configured. Click "Add Repository" to create one.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = repositories.map(repo => `
    <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div class="flex justify-between items-start mb-2">
        <div class="flex-grow">
          <h5 class="font-semibold text-lg">
            ${escapeHtml(repo.name)}
            ${repo.id === 'main' ? '<span class="ml-2 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">MAIN REPO</span>' : ''}
          </h5>
          <p class="text-xs text-gray-500 font-mono">${escapeHtml(repo.id)}</p>
          ${repo.description ? `<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${escapeHtml(repo.description)}</p>` : ''}
        </div>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-sm" onclick="window.editRepository('${escapeHtml(repo.id)}')">
            <i class="fa-solid fa-pen-to-square"></i> Edit
          </button>
          ${repo.id !== 'main' ? `<button class="btn btn-danger text-sm" onclick="window.deleteRepository('${escapeHtml(repo.id)}')">
            <i class="fa-solid fa-trash"></i>
          </button>` : ''}
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs mt-3">
        <div><strong>GitLab URL:</strong> ${escapeHtml(repo.gitlab_url)}</div>
        <div><strong>Project ID:</strong> ${escapeHtml(repo.project_id)}</div>
        <div><strong>Branch:</strong> ${escapeHtml(repo.branch)}</div>
        <div><strong>Pattern:</strong> ${escapeHtml(repo.filename_pattern_id)}</div>
        <div class="md:col-span-2">
          <strong>File Types:</strong>
          ${repo.allowed_file_types?.map(type => `<span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded mr-1">${type}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * Edit repository (global function for onclick handler)
 */
window.editRepository = async function(repoId) {
  if (!currentConfig || !currentConfig.repositories) {
    showNotification('Configuration not loaded', 'error');
    return;
  }

  const repo = currentConfig.repositories.find(r => r.id === repoId);
  if (!repo) {
    showNotification(`Repository "${repoId}" not found`, 'error');
    return;
  }

  showRepositoryModal(repo);
};

/**
 * Load and display user access (integrated with GitLab users)
 */
async function loadUserAccess(userAccess) {
  const container = document.getElementById('userAccessList');
  if (!container) {
    console.log('[Admin] userAccessList container not found');
    return;
  }

  console.log('[Admin] Loading user access list...');

  try {
    // Fetch GitLab users to show in the list
    const response = await fetch('/gitlab/users', { credentials: 'include' });
    console.log('[Admin] GitLab users response status:', response.status);

    const gitlabUsers = response.ok ? await response.json() : [];
    console.log('[Admin] GitLab users loaded:', gitlabUsers.length, gitlabUsers);

    if (gitlabUsers.length === 0) {
      console.log('[Admin] No users found, showing empty state');
      container.innerHTML = `
        <div class="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <p class="text-sm"><i class="fa-solid fa-info-circle mr-2"></i>
          <strong>No GitLab users connected yet.</strong></p>
          <p class="text-sm mt-2">Users will appear here when they authenticate with their GitLab token.</p>
        </div>
      `;
      return;
    }

    console.log('[Admin] Rendering', gitlabUsers.length, 'users');

    // Merge GitLab users with access config
    container.innerHTML = gitlabUsers.map(user => {
      const userAccessConfig = userAccess?.find(a => a.username === user.username);
      const repos = userAccessConfig?.repository_ids || user.repository_access || ['main'];
      const defaultRepo = userAccessConfig?.default_repository_id || 'main';

      return `
      <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-start mb-2">
          <div class="flex-grow">
            <h5 class="font-semibold text-lg">
              <i class="fa-brands fa-gitlab mr-2 text-orange-500"></i>${escapeHtml(user.username)}
              ${user.is_admin ? '<span class="ml-2 text-xs bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 px-2 py-1 rounded">ADMIN</span>' : ''}
            </h5>
            ${user.display_name ? `<p class="text-xs text-gray-600 dark:text-gray-400">${escapeHtml(user.display_name)}</p>` : ''}
            <p class="text-xs text-gray-500">Default: ${escapeHtml(defaultRepo)}</p>
          </div>
          <button class="btn btn-secondary text-sm ml-2" onclick="window.showUserAccessModal('${escapeHtml(user.username)}', ${JSON.stringify(repos).replace(/"/g, '&quot;')}, '${escapeHtml(defaultRepo)}')">
            <i class="fa-solid fa-pen-to-square"></i> Edit Access
          </button>
        </div>
        <div class="mt-2">
          <strong class="text-xs">Accessible Repositories:</strong>
          <div class="flex flex-wrap gap-1 mt-1">
            ${repos.map(id => `<span class="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded text-xs">${escapeHtml(id)}</span>`).join('')}
          </div>
        </div>
      </div>
    `;
    }).join('');
  } catch (error) {
    console.error('Failed to load users for access tab:', error);
    container.innerHTML = `
      <div class="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg p-4">
        <p class="text-sm"><i class="fa-solid fa-exclamation-triangle mr-2"></i>
        <strong>Failed to load users:</strong> ${error.message}</p>
      </div>
    `;
  }
}

// ============================================================================
// PATTERN MANAGEMENT
// ============================================================================

/**
 * Show modal to add/edit filename pattern
 */
function showPatternModal(pattern = null) {
  const template = document.getElementById('template-pattern-modal');
  if (!template) {
    showNotification('Pattern modal template not found', 'error');
    return;
  }

  const modal = template.content.cloneNode(true);

  // Fill form if editing
  if (pattern) {
    modal.querySelector('#patternModalTitle').textContent = 'Edit Filename Pattern';
    modal.querySelector('#patternName').value = pattern.name;
    modal.querySelector('#patternName').readOnly = true;
    modal.querySelector('#patternDescription').value = pattern.description;
    modal.querySelector('#linkPattern').value = pattern.link_pattern;
    modal.querySelector('#filePattern').value = pattern.file_pattern;
    modal.querySelector('#maxStemLength').value = pattern.max_stem_length;
    modal.querySelector('#exampleValid').value = pattern.example_valid?.join(', ') || '';
    modal.querySelector('#exampleInvalid').value = pattern.example_invalid?.join(', ') || '';
  }

  const form = modal.querySelector('#patternForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await savePattern(form, pattern);
  });

  showModal(modal);
}

/**
 * Save filename pattern
 */
async function savePattern(form, existingPattern) {
  const data = {
    name: form.querySelector('#patternName').value,
    description: form.querySelector('#patternDescription').value,
    link_pattern: form.querySelector('#linkPattern').value,
    file_pattern: form.querySelector('#filePattern').value,
    max_stem_length: parseInt(form.querySelector('#maxStemLength').value),
    example_valid: form.querySelector('#exampleValid').value.split(',').map(s => s.trim()).filter(Boolean),
    example_invalid: form.querySelector('#exampleInvalid').value.split(',').map(s => s.trim()).filter(Boolean)
  };

  try {
    await apiService.addFilenamePattern(data);
    showNotification(`Pattern "${data.name}" saved successfully`, 'success');
    closeModal();
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to save pattern:', error);
    showNotification(error.message || 'Failed to save pattern', 'error');
  }
}

/**
 * Delete filename pattern
 */
window.deletePattern = async function(patternName) {
  if (!confirm(`Are you sure you want to delete the pattern "${patternName}"?\n\nNOTE: You cannot delete a pattern if it's in use by any repository, or if it's the last pattern.`)) {
    return;
  }

  try {
    const response = await fetch(`/admin/config/patterns/${encodeURIComponent(patternName)}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to delete pattern');
    }

    showNotification(data.message || `Pattern "${patternName}" deleted`, 'success');
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to delete pattern:', error);
    showNotification(error.message || 'Failed to delete pattern', 'error');
  }
};

// ============================================================================
// REPOSITORY MANAGEMENT
// ============================================================================

/**
 * Show modal to add/edit repository
 */
async function showRepositoryModal(repo = null) {
  // Create modal dynamically with file extension management
  const content = document.createElement('div');
  content.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-2xl max-h-[85vh] overflow-y-auto';

  // Get pattern options
  let patternOptions = '<option value="">Select a pattern...</option>';
  if (currentConfig && currentConfig.filename_patterns) {
    patternOptions += currentConfig.filename_patterns.map(pattern =>
      `<option value="${escapeHtml(pattern.name)}" ${repo && repo.filename_pattern_id === pattern.name ? 'selected' : ''}>
        ${escapeHtml(pattern.name)}
      </option>`
    ).join('');
  }

  // Default file types
  const defaultExtensions = repo?.allowed_file_types || ['.mcam', '.vnc', '.emcam', '.link'];

  content.innerHTML = `
    <form id="repositoryForm">
      <h3 class="text-xl font-semibold mb-4">
        <i class="fa-solid fa-database mr-2"></i>${repo ? 'Edit Repository' : 'Add Repository'}
      </h3>
      <div class="space-y-4">
        <div>
          <label for="repoId" class="block text-sm font-medium mb-1">
            Repository ID <span class="text-red-500">*</span>
          </label>
          <input type="text" id="repoId" required class="input-field"
            placeholder="e.g., main, legacy, projects2025"
            value="${repo ? escapeHtml(repo.id) : ''}"
            ${repo ? 'readonly' : ''} />
          <p class="text-xs text-gray-500 mt-1">Unique identifier (lowercase, no spaces)</p>
        </div>
        <div>
          <label for="repoName" class="block text-sm font-medium mb-1">
            Display Name <span class="text-red-500">*</span>
          </label>
          <input type="text" id="repoName" required class="input-field"
            placeholder="e.g., Main Repository"
            value="${repo ? escapeHtml(repo.name) : ''}" />
        </div>
        <div>
          <label for="repoGitlabUrl" class="block text-sm font-medium mb-1">
            GitLab URL <span class="text-red-500">*</span>
          </label>
          <input type="url" id="repoGitlabUrl" required class="input-field"
            placeholder="https://gitlab.com/group/project"
            value="${repo ? escapeHtml(repo.gitlab_url) : ''}" />
        </div>
        <div>
          <label for="repoProjectId" class="block text-sm font-medium mb-1">
            Project ID <span class="text-red-500">*</span>
          </label>
          <input type="text" id="repoProjectId" required class="input-field"
            placeholder="e.g., 74609002"
            value="${repo ? escapeHtml(repo.project_id) : ''}" />
        </div>
        <div>
          <label for="repoBranch" class="block text-sm font-medium mb-1">
            Branch <span class="text-red-500">*</span>
          </label>
          <input type="text" id="repoBranch" required class="input-field"
            value="${repo ? escapeHtml(repo.branch) : 'main'}" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">
            Allowed File Extensions <span class="text-red-500">*</span>
          </label>
          <div id="extensionsList" class="flex flex-wrap gap-2 mb-2 min-h-[2rem] border border-gray-300 dark:border-gray-600 rounded-lg p-2">
            ${defaultExtensions.map(ext => `
              <span class="inline-flex items-center bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-sm">
                ${escapeHtml(ext)}
                <button type="button" class="ml-2 text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-100"
                  onclick="this.parentElement.remove()">
                  <i class="fa-solid fa-times"></i>
                </button>
              </span>
            `).join('')}
          </div>
          <div class="flex gap-2">
            <input type="text" id="newExtension" class="input-field flex-grow"
              placeholder="e.g., .mcam-x or .custom" />
            <button type="button" id="addExtensionBtn" class="btn btn-secondary whitespace-nowrap">
              <i class="fa-solid fa-plus mr-1"></i>Add Extension
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1">Extensions must start with a dot (e.g., .mcam)</p>
        </div>
        <div>
          <label for="repoPatternId" class="block text-sm font-medium mb-1">
            Filename Pattern <span class="text-red-500">*</span>
          </label>
          <select id="repoPatternId" required class="input-field">
            ${patternOptions}
          </select>
        </div>
        <div>
          <label for="repoDescription" class="block text-sm font-medium mb-1">
            Description
          </label>
          <textarea id="repoDescription" rows="2" class="input-field"
            placeholder="Optional repository description">${repo ? escapeHtml(repo.description || '') : ''}</textarea>
        </div>
      </div>
      <div class="flex justify-end space-x-3 mt-6">
        <button type="button" class="btn btn-secondary" data-action="close">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Repository</button>
      </div>
    </form>
  `;

  // Attach add extension handler
  const addExtBtn = content.querySelector('#addExtensionBtn');
  const newExtInput = content.querySelector('#newExtension');
  const extensionsList = content.querySelector('#extensionsList');

  addExtBtn.addEventListener('click', () => {
    const extension = newExtInput.value.trim();

    // Validation
    if (!extension) {
      showNotification('Please enter a file extension', 'error');
      return;
    }

    if (!extension.startsWith('.')) {
      showNotification('Extension must start with a dot (e.g., .mcam)', 'error');
      return;
    }

    if (extension.length < 2) {
      showNotification('Extension too short', 'error');
      return;
    }

    // Check if already exists
    const existing = Array.from(extensionsList.querySelectorAll('span')).map(span =>
      span.textContent.trim().replace('×', '').trim()
    );
    if (existing.includes(extension)) {
      showNotification(`Extension ${extension} already added`, 'error');
      return;
    }

    // Add the extension badge
    const badge = document.createElement('span');
    badge.className = 'inline-flex items-center bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-sm';
    badge.innerHTML = `
      ${escapeHtml(extension)}
      <button type="button" class="ml-2 text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-100">
        <i class="fa-solid fa-times"></i>
      </button>
    `;
    badge.querySelector('button').addEventListener('click', () => badge.remove());

    extensionsList.appendChild(badge);
    newExtInput.value = '';
    newExtInput.focus();
  });

  // Allow Enter key to add extension
  newExtInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addExtBtn.click();
    }
  });

  const form = content.querySelector('#repositoryForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveRepository(form, repo);
  });

  showModal(content);
}

/**
 * Save repository configuration
 */
async function saveRepository(form, existingRepo) {
  // Collect file extensions from badges
  const extensionsList = form.querySelector('#extensionsList');
  const extensions = Array.from(extensionsList.querySelectorAll('span')).map(span => {
    // Extract text without the × button
    const text = span.textContent.trim();
    return text.replace('×', '').trim();
  }).filter(Boolean);

  // Validation
  if (extensions.length === 0) {
    showNotification('Please add at least one file extension', 'error');
    return;
  }

  const data = {
    id: form.querySelector('#repoId').value,
    name: form.querySelector('#repoName').value,
    gitlab_url: form.querySelector('#repoGitlabUrl').value,
    project_id: form.querySelector('#repoProjectId').value,
    branch: form.querySelector('#repoBranch').value,
    allowed_file_types: extensions,
    filename_pattern_id: form.querySelector('#repoPatternId').value,
    description: form.querySelector('#repoDescription').value || null
  };

  try {
    await apiService.addRepository(data);
    showNotification(`Repository "${data.name}" saved successfully`, 'success');
    closeModal();
    loadAdminConfig(false);
  } catch (error) {
    console.error('Failed to save repository:', error);
    showNotification(error.message || 'Failed to save repository', 'error');
  }
}

/**
 * Delete repository
 */
window.deleteRepository = async function(repoId) {
  if (!confirm(`Are you sure you want to delete the repository "${repoId}"?\n\nNOTE: You cannot delete a repository if it's the last one, or if users have it as their default.`)) {
    return;
  }

  try {
    const response = await fetch(`/admin/config/repositories/${encodeURIComponent(repoId)}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to delete repository');
    }

    showNotification(data.message || `Repository "${repoId}" deleted`, 'success');
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to delete repository:', error);
    showNotification(error.message || 'Failed to delete repository', 'error');
  }
};

// ============================================================================
// USER ACCESS MANAGEMENT
// ============================================================================

/**
 * Show modal to edit user access with repository checkboxes
 */
window.showUserAccessModal = async function(username, currentRepos = [], defaultRepo = 'main') {
  if (!currentConfig || !currentConfig.repositories) {
    showNotification('Please load configuration first', 'error');
    return;
  }

  // Create modal content dynamically
  const content = document.createElement('div');
  content.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-lg max-h-[85vh] overflow-y-auto';

  // Generate repository checkboxes
  const repoCheckboxes = currentConfig.repositories.map(repo => `
    <label class="flex items-center p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded">
      <input type="checkbox" class="repo-checkbox mr-3" value="${escapeHtml(repo.id)}"
        ${currentRepos.includes(repo.id) ? 'checked' : ''}>
      <div class="flex-grow">
        <span class="font-medium">${escapeHtml(repo.name)}</span>
        <span class="text-xs text-gray-500 ml-2">(${escapeHtml(repo.id)})</span>
      </div>
    </label>
  `).join('');

  // Generate default repo dropdown
  const repoOptions = currentConfig.repositories.map(repo => `
    <option value="${escapeHtml(repo.id)}" ${repo.id === defaultRepo ? 'selected' : ''}>
      ${escapeHtml(repo.name)}
    </option>
  `).join('');

  content.innerHTML = `
    <form id="userAccessForm">
      <h3 class="text-xl font-semibold mb-4">
        <i class="fa-solid fa-user-lock mr-2"></i>Edit Repository Access
      </h3>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1">
            User
          </label>
          <input type="text" value="${escapeHtml(username)}" readonly
            class="input-field bg-gray-100 dark:bg-gray-700 cursor-not-allowed" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">
            Accessible Repositories <span class="text-red-500">*</span>
          </label>
          <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-2 max-h-60 overflow-y-auto space-y-1">
            ${repoCheckboxes}
          </div>
          <p class="text-xs text-gray-500 mt-1">Select which repositories this user can access</p>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">
            Default Repository
          </label>
          <select id="defaultRepoId" class="input-field">
            ${repoOptions}
          </select>
          <p class="text-xs text-gray-500 mt-1">Repository to open by default</p>
        </div>
      </div>
      <div class="flex justify-end space-x-3 mt-6">
        <button type="button" class="btn btn-secondary" data-action="close">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Access</button>
      </div>
    </form>
  `;

  const form = content.querySelector('#userAccessForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveUserAccess(username, form);
  });

  showModal(content);
};

/**
 * Save user access configuration (updated version)
 */
async function saveUserAccess(username, form) {
  const checkedRepos = Array.from(form.querySelectorAll('.repo-checkbox:checked')).map(cb => cb.value);

  if (checkedRepos.length === 0) {
    showNotification('Please select at least one repository', 'error');
    return;
  }

  const data = {
    username: username,
    repository_ids: checkedRepos,
    default_repository_id: form.querySelector('#defaultRepoId').value || null
  };

  try {
    await apiService.updateUserAccess(data);
    showNotification(`Repository access updated for ${username}`, 'success');
    closeModal();
    loadAdminConfig(false);
  } catch (error) {
    console.error('Failed to save user access:', error);
    showNotification(error.message || 'Failed to save user access', 'error');
  }
}

// Remove old function below
/**
 * OLD Show modal to add/edit user access (DEPRECATED)
 */
async function _OLD_showUserAccessModal(userAccess = null) {
  const template = document.getElementById('template-user-access-modal');
  if (!template) {
    showNotification('User access modal template not found', 'error');
    return;
  }

  const modal = template.content.cloneNode(true);

  // Populate repository checkboxes
  const checkboxContainer = modal.querySelector('#repositoryCheckboxes');
  const defaultSelect = modal.querySelector('#defaultRepoId');

  if (currentConfig && currentConfig.repositories) {
    checkboxContainer.innerHTML = currentConfig.repositories.map(repo => `
      <label class="flex items-center">
        <input type="checkbox" class="repo-checkbox mr-2" value="${escapeHtml(repo.id)}"
          ${userAccess?.repository_ids?.includes(repo.id) ? 'checked' : ''}>
        <span>${escapeHtml(repo.name)} <span class="text-xs text-gray-500">(${escapeHtml(repo.id)})</span></span>
      </label>
    `).join('');

    // Populate default dropdown
    currentConfig.repositories.forEach(repo => {
      const option = document.createElement('option');
      option.value = repo.id;
      option.textContent = repo.name;
      defaultSelect.appendChild(option);
    });
  }

  // Fill form if editing
  if (userAccess) {
    modal.querySelector('#userAccessModalTitle').textContent = 'Edit User Access';
    modal.querySelector('#accessUsername').value = userAccess.username;
    modal.querySelector('#accessUsername').readOnly = true;
    modal.querySelector('#defaultRepoId').value = userAccess.default_repository_id || '';
  }

  const form = modal.querySelector('#userAccessForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveUserAccess(form, userAccess);
  });

  showModal(modal);
}

/**
 * Delete user access
 */
window.deleteUserAccess = async function(username) {
  if (!confirm(`Are you sure you want to remove access configuration for "${username}"?\n\nUser will revert to having access to all repositories.`)) {
    return;
  }

  try {
    await apiService.deleteUserAccess(username);
    showNotification(`Access configuration for "${username}" removed`, 'success');
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to delete user access:', error);
    showNotification(error.message || 'Failed to delete user access', 'error');
  }
};

// ============================================================================
// USER MANAGEMENT (Original Admin Features)
// ============================================================================

/**
 * Load GitLab users list (auto-discovered users)
 */
async function loadUsers() {
  const container = document.getElementById('usersContent');
  if (!container) return;

  container.innerHTML = '<div class="text-center py-8"><i class="fa-solid fa-spinner fa-spin text-2xl"></i><p class="mt-2">Loading GitLab users...</p></div>';

  try {
    const response = await fetch('/gitlab/users', {
      credentials: 'include'
    });

    const users = await response.json();

    if (!response.ok) {
      throw new Error('Failed to load GitLab users');
    }

    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h4 class="text-lg font-semibold">
            <i class="fa-brands fa-gitlab mr-2"></i>GitLab Users
          </h4>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <i class="fa-solid fa-info-circle"></i> Users automatically discovered from GitLab connections
          </div>
        </div>
        <div class="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-3 text-sm">
          <strong>Auto-Discovery:</strong> Users appear here when they first connect with their GitLab token.
          All users connect to the <strong>main</strong> repository by default.
        </div>
        <div class="space-y-3" id="usersList">
          ${users.length === 0 ? '<p class="text-center text-gray-500 py-8">No users have connected yet</p>' : ''}
        </div>
      </div>
    `;

    // Render each user
    const usersList = document.getElementById('usersList');
    if (users.length > 0) {
      usersList.innerHTML = users.map(user => {
        const firstSeen = new Date(user.first_seen);
        const lastSeen = new Date(user.last_seen);
        const isRecent = (Date.now() - firstSeen.getTime()) < (24 * 60 * 60 * 1000); // Within 24 hours

        return `
        <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div class="flex justify-between items-start">
            <div class="flex-grow">
              <h5 class="font-semibold text-lg">
                <i class="fa-brands fa-gitlab mr-2 text-orange-500"></i>${escapeHtml(user.username)}
                ${user.is_admin ? '<span class="ml-2 text-xs bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 px-2 py-1 rounded">ADMIN</span>' : ''}
                ${isRecent ? '<span class="ml-2 text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded">NEW</span>' : ''}
              </h5>
              ${user.display_name ? `<p class="text-sm text-gray-700 dark:text-gray-300">${escapeHtml(user.display_name)}</p>` : ''}
              ${user.email ? `<p class="text-xs text-gray-500"><i class="fa-solid fa-envelope mr-1"></i>${escapeHtml(user.email)}</p>` : ''}
              <div class="flex gap-4 mt-2 text-xs text-gray-600 dark:text-gray-400">
                <span><i class="fa-solid fa-calendar-plus mr-1"></i>First: ${formatRelativeTime(firstSeen)}</span>
                <span><i class="fa-solid fa-clock mr-1"></i>Last: ${formatRelativeTime(lastSeen)}</span>
              </div>
              <div class="mt-2">
                <strong class="text-xs">Repositories:</strong>
                <div class="flex flex-wrap gap-1 mt-1">
                  ${user.repository_access.map(repo => `<span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs">${escapeHtml(repo)}</span>`).join('')}
                </div>
              </div>
            </div>
            <div class="flex flex-col space-y-2">
              <button class="btn btn-secondary text-sm" onclick="window.assignRepositories('${escapeHtml(user.username)}')">
                <i class="fa-solid fa-database"></i> Assign Repos
              </button>
              ${!user.is_admin ? `<button class="btn btn-secondary text-sm" onclick="window.makeAdmin('${escapeHtml(user.username)}')">
                <i class="fa-solid fa-shield-halved"></i> Make Admin
              </button>` : ''}
            </div>
          </div>
        </div>
      `;
      }).join('');
    }
  } catch (error) {
    console.error('Failed to load GitLab users:', error);
    container.innerHTML = `
      <div class="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg p-4">
        <p class="text-sm"><i class="fa-solid fa-exclamation-triangle mr-2"></i>
        <strong>Failed to load GitLab users:</strong> ${error.message}</p>
      </div>
    `;
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

/**
 * Assign repositories to a GitLab user
 */
window.assignRepositories = async function(username) {
  // TODO: Create modal to select repositories
  // For now, use prompt
  const repoList = prompt(`Enter comma-separated repository IDs for ${username}:\n(e.g., main,legacy,projects2025)`);

  if (!repoList) return;

  const repository_ids = repoList.split(',').map(s => s.trim()).filter(Boolean);

  if (repository_ids.length === 0) {
    showNotification('Please enter at least one repository ID', 'error');
    return;
  }

  try {
    const response = await fetch(`/gitlab/users/${encodeURIComponent(username)}/repositories`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ repository_ids })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to update repositories');
    }

    showNotification(data.message || 'Repositories updated successfully', 'success');
    loadUsers();
  } catch (error) {
    console.error('Failed to update repositories:', error);
    showNotification(error.message || 'Failed to update repositories', 'error');
  }
};

/**
 * Make a user an admin
 */
window.makeAdmin = async function(username) {
  if (!confirm(`Grant admin privileges to ${username}?`)) {
    return;
  }

  try {
    const response = await fetch(`/gitlab/users/${encodeURIComponent(username)}/admin`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ is_admin: true })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to update admin status');
    }

    showNotification(data.message || 'Admin privileges granted', 'success');
    loadUsers();
  } catch (error) {
    console.error('Failed to update admin status:', error);
    showNotification(error.message || 'Failed to update admin status', 'error');
  }
};

/**
 * Show create user modal (DEPRECATED - now using GitLab auto-discovery)
 */
function showCreateUserModal() {
  const content = document.createElement('div');
  content.innerHTML = `
    <div class="panel-bg rounded-xl shadow-lg p-6 w-full max-w-lg">
      <form id="createUserForm">
        <h3 class="text-xl font-semibold mb-4">
          <i class="fa-solid fa-user-plus mr-2"></i>Create New User
        </h3>
        <div class="space-y-4">
          <div>
            <label for="newUsername" class="block text-sm font-medium mb-1">
              Username <span class="text-red-500">*</span>
            </label>
            <input type="text" id="newUsername" name="username" required class="input-field" />
          </div>
          <div>
            <label for="newPassword" class="block text-sm font-medium mb-1">
              Password <span class="text-red-500">*</span>
            </label>
            <input type="password" id="newPassword" name="password" required minlength="8" class="input-field" />
          </div>
          <div>
            <label class="flex items-center">
              <input type="checkbox" id="newIsAdmin" name="is_admin" class="mr-2" />
              <span>Grant admin privileges</span>
            </label>
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button type="button" class="btn btn-secondary" data-action="close">Cancel</button>
          <button type="submit" class="btn btn-primary">Create User</button>
        </div>
      </form>
    </div>
  `;

  const form = content.querySelector('#createUserForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await createUser(new FormData(form));
  });

  showModal(content);
}

/**
 * Create new user
 */
async function createUser(formData) {
  try {
    const response = await fetch('/admin/users/create', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to create user');
    }

    showNotification(data.message || 'User created successfully', 'success');
    closeModal();
    loadUsers();
  } catch (error) {
    console.error('Failed to create user:', error);
    showNotification(error.message || 'Failed to create user', 'error');
  }
}

/**
 * Reset user password
 */
window.resetUserPassword = async function(username) {
  const newPassword = prompt(`Enter new password for ${username}:\n\n(Minimum 8 characters)`);

  if (!newPassword) return;

  if (newPassword.length < 8) {
    showNotification('Password must be at least 8 characters', 'error');
    return;
  }

  try {
    const formData = new FormData();
    formData.append('new_password', newPassword);

    const response = await fetch(`/admin/users/${encodeURIComponent(username)}/reset-password`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to reset password');
    }

    showNotification(data.message || 'Password reset successfully', 'success');
  } catch (error) {
    console.error('Failed to reset password:', error);
    showNotification(error.message || 'Failed to reset password', 'error');
  }
};

/**
 * Delete user
 */
window.deleteUser = async function(username) {
  if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis action cannot be undone.`)) {
    return;
  }

  try {
    const response = await fetch(`/admin/users/${encodeURIComponent(username)}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to delete user');
    }

    showNotification(data.message || 'User deleted successfully', 'success');
    loadUsers();
  } catch (error) {
    console.error('Failed to delete user:', error);
    showNotification(error.message || 'Failed to delete user', 'error');
  }
};

// ============================================================================
// MAINTENANCE TOOLS (Original Admin Features)
// ============================================================================

async function handleCreateBackup() {
  if (!confirm('Create a backup of the entire repository?\n\nThis may take a few minutes depending on repository size.')) {
    return;
  }

  try {
    showNotification('Creating backup...', 'info');

    const response = await fetch('/admin/create_backup', {
      method: 'POST',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Backup failed');
    }

    showNotification(`Backup created successfully!\n${data.backup_path || ''}`, 'success');
  } catch (error) {
    console.error('Backup failed:', error);
    showNotification(`Backup failed: ${error.message}`, 'error');
  }
}

async function handleCleanupLFS() {
  if (!confirm('Clean up old LFS files?\n\nThis will remove unreferenced LFS objects to free disk space.')) {
    return;
  }

  try {
    showNotification('Cleaning up LFS files...', 'info');

    const response = await fetch('/admin/cleanup_lfs', {
      method: 'POST',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Cleanup failed');
    }

    showNotification('LFS cleanup completed successfully', 'success');
  } catch (error) {
    console.error('LFS cleanup failed:', error);
    showNotification(`Cleanup failed: ${error.message}`, 'error');
  }
}

async function handleExportRepo() {
  if (!confirm('Export repository as ZIP?\n\nThis will download all files (excluding .git folder).')) {
    return;
  }

  try {
    showNotification('Preparing export... This may take a moment.', 'info');

    const response = await fetch('/admin/export_repository', {
      method: 'POST',
      credentials: 'include'
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Export failed');
    }

    // Download the ZIP file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'mastercam_export.zip';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    showNotification('Repository exported successfully', 'success');
  } catch (error) {
    console.error('Export failed:', error);
    showNotification(`Export failed: ${error.message}`, 'error');
  }
}

async function handleResetRepo() {
  const confirmation = prompt(
    'DANGER: Reset repository to match GitLab exactly?\n\n' +
    'This will DELETE ALL LOCAL CHANGES!\n\n' +
    'Type "RESET" to confirm:'
  );

  if (confirmation !== 'RESET') {
    return;
  }

  try {
    showNotification('Resetting repository... Please wait.', 'info');

    const response = await fetch('/admin/reset_repository', {
      method: 'POST',
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Reset failed');
    }

    showNotification('Repository reset successfully. Reloading page...', 'success');

    // Reload the page after reset
    setTimeout(() => {
      window.location.reload();
    }, 2000);
  } catch (error) {
    console.error('Repository reset failed:', error);
    showNotification(`Reset failed: ${error.message}`, 'error');
  }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
