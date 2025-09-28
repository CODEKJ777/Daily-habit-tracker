// Main Application Logic for AI Habit Tracker
// Configuration
const API_BASE = '/api';  // Use relative path for Flask
let habits = [];
let archivedHabits = [];
let tasks = [];

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    loadAIInsights();
    // Try to enable browser notifications
    initBrowserNotifications();
    
    // Add event listeners for modals
    setupModalEventListeners();
    
    // Add Enter key support for modal inputs
    document.getElementById('habitInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') saveHabit();
    });
    
    document.getElementById('taskInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') saveTask();
    });
});

// Modal setup
function setupModalEventListeners() {
    // Save habit button
    document.getElementById('btnSaveHabit')?.addEventListener('click', saveHabit);
    
    // Save task button
    document.getElementById('btnSaveTask')?.addEventListener('click', saveTask);
}

// Modal management
function showModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
    // Focus on input
    if (modalId === 'addHabitModal') {
        document.getElementById('habitInput').focus();
    } else if (modalId === 'addTaskModal') {
        document.getElementById('taskInput').focus();
    }
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    // Clear inputs
    if (modalId === 'addHabitModal') {
        document.getElementById('habitInput').value = '';
        document.getElementById('habitReminderTime').value = '';
        const habitEmailEl = document.getElementById('habitEmailNotification');
        if (habitEmailEl) habitEmailEl.checked = false;
    } else if (modalId === 'addTaskModal') {
        document.getElementById('taskInput').value = '';
        document.getElementById('taskReminderTime').value = '';
        const taskEmailEl = document.getElementById('taskEmailNotification');
        if (taskEmailEl) taskEmailEl.checked = false;
    }
}

// API Functions
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Error: ' + error.message, 'error');
        throw error;
    }
}

// Data Loading
async function loadData() {
    try {
        const [habitsData, archivedData, tasksData, statsData] = await Promise.all([
            apiCall('/habits'),
            apiCall('/habits/archived'),
            apiCall('/tasks'),
            apiCall('/stats')
        ]);
        
        habits = habitsData;
        archivedHabits = archivedData;
        tasks = tasksData;
        
        renderHabits();
        renderArchivedHabits();
        renderTasks();
        updateStats(statsData);

        // Schedule local reminders
        scheduleAllReminders();
    } catch (error) {
        console.error('Failed to load data:', error);
    }
}

// Habit Functions
async function saveHabit() {
    const input = document.getElementById('habitInput');
    const habitName = input.value.trim();
    
    if (!habitName) return;
    
    const habitReminderTime = document.getElementById('habitReminderTime').value;

    try {
        const newHabit = await apiCall('/habits', 'POST', {
            name: habitName,
            reminder_time: habitReminderTime || null, // Send null if empty
        });
        habits.unshift(newHabit);
        hideModal('addHabitModal');
        renderHabits();
        
        if (newHabit.motivation) {
            showNotification(newHabit.motivation, 'success');
        }

        // Schedule reminder for this habit if set
        if (newHabit.reminder_time) {
            scheduleLocalReminder(`Time for your habit: ${newHabit.name}`, newHabit.reminder_time);
        }
    } catch (error) {
        // Error already handled in apiCall
    }
}

function getHabitById(id){ return habits.find(h => h.id === id); }

async function editHabitPrompt(habitId) {
    const habit = getHabitById(habitId);
    const currentName = habit?.name || '';
    const currentTime = habit?.reminder_time || '';
    const name = prompt('Edit habit name:', currentName);
    if (name === null) return;
    const time = prompt('Edit reminder time (HH:MM) or leave blank:', currentTime || '');
    try {
        const payload = { name };
        if (time !== null) payload.reminder_time = time.trim() || null;
        const updated = await apiCall(`/habits/${habitId}`, 'PATCH', payload);
        const idx = habits.findIndex(h => h.id === habitId);
        if (idx !== -1) habits[idx] = { ...habits[idx], ...updated };
        renderHabits();
        loadData();
    } catch(e) {}
}

async function unarchiveHabit(habitId) {
    try {
        await apiCall(`/habits/${habitId}/unarchive`, 'POST');
        await loadData();
    } catch(e) {}
}

async function deleteHabitArchived(habitId) {
    if (!confirm('Delete this archived habit? This will remove its completion history.')) return;
    try {
        await apiCall(`/habits/${habitId}`, 'DELETE');
        archivedHabits = archivedHabits.filter(h => h.id !== habitId);
        renderArchivedHabits();
        loadData();
    } catch(e) {}
}

async function archiveHabit(habitId) {
    if (!confirm('Archive this habit? It will be hidden from the list.')) return;
    try {
        await apiCall(`/habits/${habitId}/archive`, 'POST');
        habits = habits.filter(h => h.id !== habitId);
        renderHabits();
        loadData();
    } catch(e) {}
}

async function deleteHabit(habitId) {
    if (!confirm('Delete this habit? This will remove its completion history.')) return;
    try {
        await apiCall(`/habits/${habitId}`, 'DELETE');
        // remove locally and re-render
        habits = habits.filter(h => h.id !== habitId);
        renderHabits();
        loadData();// refresh stats
    } catch (e) {
        // handled in apiCall
    }
}

async function uncompleteHabit(habitId) {
    try {
        const result = await apiCall(`/habits/${habitId}/uncomplete`, 'POST');
        const habit = habits.find(h => h.id === habitId);
        if (habit) {
            habit.done_today = false;
            habit.streak = result.new_streak ?? habit.streak;
            // last_done will refresh via loadData
        }
        renderHabits();
        loadData();
    } catch (e) {}
}

async function completeHabit(habitId) {
    try {
        const result = await apiCall(`/habits/${habitId}/complete`, 'POST');
        
        // Update habit in local data
        const habit = habits.find(h => h.id === habitId);
        if (habit) {
            habit.done_today = true;
            habit.streak = result.new_streak;
        }
        
        renderHabits();
        loadData(); // Refresh stats
        
        if (result.motivation) {
            showNotification(result.motivation, 'success');
        }
    } catch (error) {
        // Error already handled in apiCall
    }
}

function renderHabits() {
    const container = document.getElementById('habits-list');
    if (!container) return;
    
    if (habits.length === 0) {
        container.innerHTML = `
            <div class="empty-state text-center py-8">
                <i data-lucide="target" class="w-16 h-16 text-gray-300 mx-auto mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No habits yet!</h3>
                <p class="text-gray-500">Add your first habit to start building an amazing routine</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = habits.map(habit => `
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h3 class="font-medium text-gray-900">${habit.name}</h3>
                    <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                        <span class="flex items-center space-x-1">
                            <i data-lucide="flame" class="w-4 h-4 text-orange-500"></i>
                            <span>${habit.streak} day${habit.streak !== 1 ? 's' : ''} streak</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <i data-lucide="calendar" class="w-4 h-4 text-blue-500"></i>
                            <span>${habit.last_done ? `Last: ${habit.last_done}` : 'Never done'}</span>
                        </span>
                        ${habit.reminder_time ? `
                        <span class="flex items-center space-x-1">
                            <i data-lucide="bell" class="w-4 h-4 text-blue-500"></i>
                            <span>${habit.reminder_time}</span>
                        </span>
                        ` : ''}
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    ${habit.done_today ? 
                        `<button onclick="uncompleteHabit(${habit.id})" class="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Undo</button>` :
                        `<button onclick="completeHabit(${habit.id})" class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                            Mark Done
                        </button>`
                    }
                    <button onclick="editHabitPrompt(${habit.id})" class="bg-amber-600 hover:bg-amber-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Edit</button>
                    <button onclick="archiveHabit(${habit.id})" class="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Archive</button>
                    <button onclick="deleteHabit(${habit.id})" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
    
    // Recreate Lucide icons
    lucide.createIcons();
}

function renderArchivedHabits() {
    const container = document.getElementById('archived-list');
    if (!container) return;

    if (!archivedHabits || archivedHabits.length === 0) {
        container.innerHTML = `
            <div class="empty-state text-center py-8">
                <i data-lucide="archive" class="w-16 h-16 text-gray-300 mx-auto mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No archived habits</h3>
                <p class="text-gray-500">Archived habits will appear here. You can unarchive or delete them.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = archivedHabits.map(habit => `
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h3 class="font-medium text-gray-900">${habit.name}</h3>
                    <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                        <span class="flex items-center space-x-1">
                            <i data-lucide="flame" class="w-4 h-4 text-orange-500"></i>
                            <span>${habit.streak} day${habit.streak !== 1 ? 's' : ''} streak</span>
                        </span>
                        ${habit.last_done ? `
                        <span class="flex items-center space-x-1">
                            <i data-lucide="calendar" class="w-4 h-4 text-blue-500"></i>
                            <span>Last: ${habit.last_done}</span>
                        </span>` : ''}
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="unarchiveHabit(${habit.id})" class="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Unarchive</button>
                    <button onclick="deleteHabitArchived(${habit.id})" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">Delete</button>
                </div>
            </div>
        </div>
    `).join('');

    lucide.createIcons();
}

// Task Functions
async function saveTask() {
    const input = document.getElementById('taskInput');
    const taskName = input.value.trim();
    
    if (!taskName) return;

    const taskReminderTime = document.getElementById('taskReminderTime').value;
    
    try {
        const newTask = await apiCall('/tasks', 'POST', {
            name: taskName,
            reminder_time: taskReminderTime || null,
        });
        tasks.unshift(newTask);
        hideModal('addTaskModal');
        renderTasks();
        loadData(); // Refresh stats

        // Schedule reminder for this task if set
        if (newTask.reminder_time) {
            scheduleLocalReminder(`Don't forget your task: ${newTask.name}`, newTask.reminder_time);
        }
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function deleteTask(taskId) {
    if (!confirm('Delete this task?')) return;
    try {
        await apiCall(`/tasks/${taskId}`, 'DELETE');
        tasks = tasks.filter(t => t.id !== taskId);
        renderTasks();
        loadData();
    } catch (e) {}
}

async function completeTask(taskId) {
    try {
        await apiCall(`/tasks/${taskId}/complete`, 'POST');
        
        // Update task in local data
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            task.done = true;
        }
        
        renderTasks();
        loadData(); // Refresh stats
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function uncompleteTask(taskId) {
    try {
        await apiCall(`/tasks/${taskId}/uncomplete`, 'POST');
        
        // Update task in local data
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            task.done = false;
        }
        
        renderTasks();
        loadData(); // Refresh stats
    } catch (error) {
        // Error already handled in apiCall
    }
}

function renderTasks() {
    const container = document.getElementById('tasks-list');
    if (!container) return;
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state text-center py-8">
                <i data-lucide="check-square" class="w-16 h-16 text-gray-300 mx-auto mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No tasks for today!</h3>
                <p class="text-gray-500">Add some tasks to stay productive</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h3 class="font-medium text-gray-900 ${task.done ? 'line-through text-gray-500' : ''}">${task.name}</h3>
                    <div class="flex items-center space-x-2 mt-2 text-sm text-gray-600">
                        <span class="flex items-center space-x-1">
                            <i data-lucide="calendar" class="w-4 h-4 text-blue-500"></i>
                            <span>${task.date}</span>
                        </span>
                        ${task.reminder_time ? `
                        <span class="flex items-center space-x-1">
                            <i data-lucide="bell" class="w-4 h-4 text-blue-500"></i>
                            <span>${task.reminder_time}</span>
                        </span>
                        ` : ''}
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    ${task.done ? 
                        `<button onclick="uncompleteTask(${task.id})" class="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">
                            Undo
                        </button>` :
                        `<button onclick="completeTask(${task.id})" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">
                            Complete
                        </button>`
                    }
                    <button onclick="deleteTask(${task.id})" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    // Recreate Lucide icons
    lucide.createIcons();
}

// Stats Functions
function updateStats(stats) {
    if (!stats) return;
    
    // Update sidebar stats
    const habitsEl = document.getElementById('statHabits');
    const tasksEl = document.getElementById('statTasks');
    const bestStreakEl = document.getElementById('statBestStreak');
    
    if (habitsEl) habitsEl.textContent = `${stats.habits.done_today}/${stats.habits.total}`;
    if (tasksEl) tasksEl.textContent = `${stats.tasks.done_today}/${stats.tasks.total_today}`;
    if (bestStreakEl) bestStreakEl.textContent = `${stats.streaks.best_streak} days`;
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Browser Notification helpers
let notificationTimers = new Map(); // Track active timers

function initBrowserNotifications() {
    if (!('Notification' in window)) return;
    
    // Check if user has disabled notifications in our app
    const notificationsEnabled = localStorage.getItem('notificationsEnabled') !== 'false';
    
    if (notificationsEnabled && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'denied') {
                showNotification('Notifications blocked. Enable them in browser settings for reminders.', 'error');
            }
        });
    }
    
    updateNotificationIcon();
}

function scheduleLocalReminder(label, timeHHMM) {
    // Schedules a one-shot reminder for today at HH:MM using setTimeout
    if (!timeHHMM) return;
    
    // Check if notifications are enabled by user
    if (localStorage.getItem('notificationsEnabled') === 'false') return;
    
    const [hh, mm] = timeHHMM.split(':').map(Number);
    const now = new Date();
    const target = new Date();
    target.setHours(hh, mm, 0, 0);
    let delayMs = target.getTime() - now.getTime();
    if (delayMs < 0) {
        // if time already passed, schedule for tomorrow
        target.setDate(target.getDate() + 1);
        delayMs = target.getTime() - now.getTime();
    }
    
    // Clear any existing timer for this reminder
    const timerKey = `${label}-${timeHHMM}`;
    if (notificationTimers.has(timerKey)) {
        clearTimeout(notificationTimers.get(timerKey));
    }
    
    const timerId = setTimeout(() => {
        // Show browser notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Reminder', { 
                body: label,
                icon: '/static/favicon.ico', // Optional: add favicon
                tag: timerKey // Prevent duplicate notifications
            });
        }
        
        // Always show in-app notification
        showNotification(label, 'info');
        
        // Re-schedule for tomorrow
        scheduleLocalReminder(label, timeHHMM);
    }, Math.min(delayMs, 2147483647)); // cap to max setTimeout
    
    notificationTimers.set(timerKey, timerId);
}

function scheduleAllReminders() {
    if (!Array.isArray(habits) || !Array.isArray(tasks)) return;
    
    // Clear all existing timers first
    notificationTimers.forEach(timerId => clearTimeout(timerId));
    notificationTimers.clear();
    
    habits.forEach(h => {
        if (h.reminder_time) scheduleLocalReminder(`Time for your habit: ${h.name}`, h.reminder_time);
    });
    tasks.forEach(t => {
        if (t.reminder_time && !t.done) scheduleLocalReminder(`Don't forget your task: ${t.name}`, t.reminder_time);
    });
}

function updateNotificationIcon() {
    const icon = document.getElementById('notificationIcon');
    if (!icon) return;
    
    const notificationsEnabled = localStorage.getItem('notificationsEnabled') !== 'false';
    const permission = Notification.permission;
    
    if (!notificationsEnabled || permission === 'denied') {
        icon.setAttribute('data-lucide', 'bell-off');
    } else if (permission === 'granted') {
        icon.setAttribute('data-lucide', 'bell');
    } else {
        icon.setAttribute('data-lucide', 'bell');
    }
    
    lucide.createIcons();
}

function toggleNotifications() {
    const current = localStorage.getItem('notificationsEnabled') !== 'false';
    const newValue = !current;
    localStorage.setItem('notificationsEnabled', newValue.toString());
    
    if (newValue && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                scheduleAllReminders(); // Re-schedule all reminders
            } else if (permission === 'denied') {
                showNotification('Notifications blocked. Enable them in browser settings.', 'error');
            }
        });
    } else if (!newValue) {
        // Clear all timers when disabling
        notificationTimers.forEach(timerId => clearTimeout(timerId));
        notificationTimers.clear();
    }
    
    updateNotificationIcon();
    showNotification(
        newValue ? 'Notifications enabled' : 'Notifications disabled', 
        'info'
    );
}

// Make functions globally available
window.addHabit = () => showModal('addHabitModal');
window.addTask = () => showModal('addTaskModal');
window.completeHabit = completeHabit;
window.uncompleteHabit = uncompleteHabit;
window.editHabitPrompt = editHabitPrompt;
window.archiveHabit = archiveHabit;
window.unarchiveHabit = unarchiveHabit;
window.deleteHabitArchived = deleteHabitArchived;
window.deleteHabit = deleteHabit;
window.completeTask = completeTask;
window.uncompleteTask = uncompleteTask;
window.deleteTask = deleteTask;
window.showModal = showModal;
window.hideModal = hideModal;
window.toggleNotifications = toggleNotifications;