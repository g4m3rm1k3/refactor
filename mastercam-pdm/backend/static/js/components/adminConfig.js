/**
 * Admin Configuration Component
 * Handles the admin configuration UI for patterns, repositories, and user access
 */

import { apiService } from '../api/service.js';
import { showNotification } from '../utils/helpers.js';
import { Modal } from './Modal.js';

let currentConfig = null;
let currentModal = null;

/**
 * Show modal helper
 */
function showModal(content) {
  if (currentModal) {
    currentModal.close();
  }
  currentModal = new Modal(content.firstElementChild || content);
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

let initialized = false;

/**
 * Attach event listeners to admin buttons
 * Called after the admin panel is visible
 */
function attachAdminEventListeners() {
  // Admin subtab switching
  const adminSubtabs = document.querySelectorAll('.admin-subtab');
  adminSubtabs.forEach(tab => {
    tab.addEventListener('click', () => switchAdminSubtab(tab.dataset.tab));
  });

  // Pattern/Repo/Access button handlers
  const addPatternBtn = document.getElementById('addPatternBtn');
  const addRepoBtn = document.getElementById('addRepoBtn');
  const addUserAccessBtn = document.getElementById('addUserAccessBtn');
  const reloadConfigBtn = document.getElementById('reloadConfigBtn');

  if (addPatternBtn) addPatternBtn.addEventListener('click', () => showPatternModal());
  if (addRepoBtn) addRepoBtn.addEventListener('click', () => showRepositoryModal());
  if (addUserAccessBtn) addUserAccessBtn.addEventListener('click', () => showUserAccessModal());
  if (reloadConfigBtn) reloadConfigBtn.addEventListener('click', loadAdminConfig);

  // Maintenance button handlers
  const createBackupBtn = document.getElementById('createBackupBtn');
  const cleanupLfsBtn = document.getElementById('cleanupLfsBtn');
  const exportRepoBtn = document.getElementById('exportRepoBtn');
  const resetRepoBtn = document.getElementById('resetRepoBtn');

  if (createBackupBtn) {
    createBackupBtn.addEventListener('click', handleCreateBackup);
    console.log('✅ Backup button handler attached');
  }
  if (cleanupLfsBtn) {
    cleanupLfsBtn.addEventListener('click', handleCleanupLFS);
    console.log('✅ Cleanup button handler attached');
  }
  if (exportRepoBtn) {
    exportRepoBtn.addEventListener('click', handleExportRepo);
    console.log('✅ Export button handler attached');
  }
  if (resetRepoBtn) {
    resetRepoBtn.addEventListener('click', handleResetRepo);
    console.log('✅ Reset button handler attached');
  }
}

/**
 * Initialize admin configuration UI
 * This is called on page load to set up event listeners
 */
export function initAdminConfig() {
  // Listen for when admin tab is opened
  const adminTabButton = document.querySelector('[data-config-tab="admin"]');
  if (adminTabButton) {
    adminTabButton.addEventListener('click', () => {
      // Load config and attach handlers when admin tab is first opened
      if (!initialized) {
        setTimeout(() => {
          attachAdminEventListeners();
          loadAdminConfig();
        }, 150); // Small delay to ensure DOM is ready
        initialized = true;
      }
    });
  }
}

// ============================================================================
// Maintenance Functions (imported from existing admin endpoints)
// ============================================================================

async function handleCreateBackup() {
  if (!confirm('Create a backup of the entire repository?\n\nThis may take a few minutes depending on repository size.')) {
    return;
  }

  try {
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
 * Switch between admin subtabs
 */
function switchAdminSubtab(tabName) {
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
 * Load admin configuration from API
 */
export async function loadAdminConfig() {
  try {
    const config = await apiService.getAdminConfig();
    currentConfig = config;

    // Update maintenance info
    updateConfigInfo(config);

    // Load each section
    loadPatterns(config.filename_patterns || []);
    loadRepositories(config.repositories || []);
    loadUserAccess(config.user_access || []);

  } catch (error) {
    console.error('Failed to load admin config:', error);

    // Show user-friendly error with default config info
    const patternsListEl = document.getElementById('patternsList');
    const repositoriesListEl = document.getElementById('repositoriesList');
    const userAccessListEl = document.getElementById('userAccessList');

    if (patternsListEl) {
      patternsListEl.innerHTML = `
        <div class="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <p class="text-sm"><i class="fa-solid fa-exclamation-triangle mr-2"></i>
          <strong>Configuration not yet initialized.</strong></p>
          <p class="text-sm mt-2">The admin configuration system will use default settings until first configured.</p>
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
 * Update configuration info in maintenance tab
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
 * Load and display filename patterns
 */
function loadPatterns(patterns) {
  const container = document.getElementById('patternsList');

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
          <h5 class="font-semibold text-lg">${escapeHtml(repo.name)}</h5>
          <p class="text-xs text-gray-500 font-mono">${escapeHtml(repo.id)}</p>
          ${repo.description ? `<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${escapeHtml(repo.description)}</p>` : ''}
        </div>
        <button class="btn btn-danger text-sm ml-2" onclick="window.deleteRepository('${escapeHtml(repo.id)}')">
          <i class="fa-solid fa-trash"></i>
        </button>
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
 * Load and display user access
 */
function loadUserAccess(userAccess) {
  const container = document.getElementById('userAccessList');

  if (!userAccess || userAccess.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-500">
        <i class="fa-solid fa-inbox text-3xl mb-2"></i>
        <p>No user access configured. All users can access all repositories.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = userAccess.map(access => `
    <div class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div class="flex justify-between items-start mb-2">
        <div class="flex-grow">
          <h5 class="font-semibold text-lg">
            <i class="fa-solid fa-user mr-2"></i>${escapeHtml(access.username)}
          </h5>
          ${access.default_repository_id ? `<p class="text-xs text-gray-500">Default: ${escapeHtml(access.default_repository_id)}</p>` : ''}
        </div>
        <button class="btn btn-danger text-sm ml-2" onclick="window.deleteUserAccess('${escapeHtml(access.username)}')">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
      <div class="mt-2">
        <strong class="text-xs">Accessible Repositories:</strong>
        <div class="flex flex-wrap gap-1 mt-1">
          ${access.repository_ids?.map(id => `<span class="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded text-xs">${escapeHtml(id)}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * Show modal to add/edit filename pattern
 */
function showPatternModal(pattern = null) {
  const template = document.getElementById('template-pattern-modal');
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
 * Show modal to add/edit repository
 */
async function showRepositoryModal(repo = null) {
  const template = document.getElementById('template-repository-modal');
  const modal = template.content.cloneNode(true);

  // Populate pattern dropdown
  const patternSelect = modal.querySelector('#repoPatternId');
  if (currentConfig && currentConfig.filename_patterns) {
    currentConfig.filename_patterns.forEach(pattern => {
      const option = document.createElement('option');
      option.value = pattern.name;
      option.textContent = pattern.name;
      patternSelect.appendChild(option);
    });
  }

  // Fill form if editing
  if (repo) {
    modal.querySelector('#repositoryModalTitle').textContent = 'Edit Repository';
    modal.querySelector('#repoId').value = repo.id;
    modal.querySelector('#repoId').readOnly = true;
    modal.querySelector('#repoName').value = repo.name;
    modal.querySelector('#repoGitlabUrl').value = repo.gitlab_url;
    modal.querySelector('#repoProjectId').value = repo.project_id;
    modal.querySelector('#repoBranch').value = repo.branch;
    modal.querySelector('#repoPatternId').value = repo.filename_pattern_id;
    modal.querySelector('#repoDescription').value = repo.description || '';

    // Update checkboxes
    modal.querySelectorAll('.file-type-checkbox').forEach(checkbox => {
      checkbox.checked = repo.allowed_file_types?.includes(checkbox.value) || false;
    });
  }

  const form = modal.querySelector('#repositoryForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveRepository(form, repo);
  });

  showModal(modal);
}

/**
 * Save repository configuration
 */
async function saveRepository(form, existingRepo) {
  const checkedFileTypes = Array.from(form.querySelectorAll('.file-type-checkbox:checked')).map(cb => cb.value);

  const data = {
    id: form.querySelector('#repoId').value,
    name: form.querySelector('#repoName').value,
    gitlab_url: form.querySelector('#repoGitlabUrl').value,
    project_id: form.querySelector('#repoProjectId').value,
    branch: form.querySelector('#repoBranch').value,
    allowed_file_types: checkedFileTypes,
    filename_pattern_id: form.querySelector('#repoPatternId').value,
    description: form.querySelector('#repoDescription').value || null
  };

  try {
    await apiService.addRepository(data);
    showNotification(`Repository "${data.name}" saved successfully`, 'success');
    closeModal();
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to save repository:', error);
    showNotification(error.message || 'Failed to save repository', 'error');
  }
}

/**
 * Show modal to add/edit user access
 */
async function showUserAccessModal(userAccess = null) {
  const template = document.getElementById('template-user-access-modal');
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
 * Save user access configuration
 */
async function saveUserAccess(form, existingAccess) {
  const checkedRepos = Array.from(form.querySelectorAll('.repo-checkbox:checked')).map(cb => cb.value);

  if (checkedRepos.length === 0) {
    showNotification('Please select at least one repository', 'error');
    return;
  }

  const data = {
    username: form.querySelector('#accessUsername').value,
    repository_ids: checkedRepos,
    default_repository_id: form.querySelector('#defaultRepoId').value || null
  };

  try {
    await apiService.updateUserAccess(data);
    showNotification(`User access for "${data.username}" saved successfully`, 'success');
    closeModal();
    loadAdminConfig();
  } catch (error) {
    console.error('Failed to save user access:', error);
    showNotification(error.message || 'Failed to save user access', 'error');
  }
}

/**
 * Delete filename pattern
 */
window.deletePattern = async function(patternName) {
  if (!confirm(`Are you sure you want to delete the pattern "${patternName}"?\n\nNOTE: You cannot delete a pattern if it's in use by any repository, or if it's the last pattern.\nAdd a replacement pattern first if needed.`)) {
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

/**
 * Delete repository
 */
window.deleteRepository = async function(repoId) {
  if (!confirm(`Are you sure you want to delete the repository "${repoId}"?\n\nNOTE: You cannot delete a repository if it's the last one, or if users have it as their default.\nAdd a replacement repository first if needed.`)) {
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

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
