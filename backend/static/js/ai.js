// AI Integration for Habit Tracker Frontend
// AI-specific functionality and API calls

// AI Service Functions
async function loadAIInsights() {
    try {
        // Load daily greeting first
        const greeting = await apiCall('/ai/greeting');
        const greetingEl = document.getElementById('aiGreeting');
        if (greetingEl) {
            greetingEl.innerHTML = `💡 ${greeting.message}`;
        }
        
        // Load additional insights with delays for better UX
        setTimeout(async () => {
            try {
                const insights = await apiCall('/ai/insights');
                const insightsEl = document.getElementById('aiInsights');
                if (insightsEl) {
                    insightsEl.innerHTML = `📊 ${insights.message}`;
                }
            } catch (e) {
                console.log('AI insights not available');
                // Fallback message
                const insightsEl = document.getElementById('aiInsights');
                if (insightsEl) {
                    insightsEl.innerHTML = '📊 Great habits take time to build. Focus on consistency over perfection!';
                }
            }
        }, 1000);
        
        setTimeout(async () => {
            try {
                const suggestion = await apiCall('/ai/suggest');
                const suggestionEl = document.getElementById('suggestedHabitTitle');
                const descEl = document.getElementById('suggestedHabitDesc');
                if (suggestionEl && descEl) {
                    suggestionEl.textContent = 'AI Suggestion';
                    descEl.textContent = suggestion.message;
                }
            } catch (e) {
                console.log('AI suggestions not available');
                // Fallback suggestion
                const suggestionEl = document.getElementById('suggestedHabitTitle');
                const descEl = document.getElementById('suggestedHabitDesc');
                if (suggestionEl && descEl) {
                    suggestionEl.textContent = 'Evening Reflection';
                    descEl.textContent = 'Take 5 minutes before bed to reflect on your day and plan tomorrow\'s priorities.';
                }
            }
        }, 2000);
        
        // Load task prioritization
        setTimeout(async () => {
            try {
                const priorities = await apiCall('/ai/prioritize');
                updateTaskPriorities(priorities.message);
            } catch (e) {
                console.log('AI prioritization not available');
                updateTaskPriorities('Focus on your most important task first - you\'ve got this! 📋');
            }
        }, 3000);
        
    } catch (error) {
        // Fallback if AI service is completely unavailable
        const greetingEl = document.getElementById('aiGreeting');
        if (greetingEl) {
            greetingEl.innerHTML = '🌟 Ready to build some amazing habits today?';
        }
        console.log('AI service unavailable, using fallbacks');
    }
}

// Update task priorities display
function updateTaskPriorities(message) {
    const container = document.getElementById('taskPriorities');
    if (!container) return;
    
    // For now, show a simple message. In the future, this could parse structured data
    container.innerHTML = `
        <div class="text-gray-700 leading-relaxed">
            <p>${message}</p>
        </div>
    `;
}

// Get AI motivation for specific contexts
async function getAIMotivation(context = 'general') {
    try {
        // This would be a future enhancement - contextual AI messages
        const response = await apiCall('/ai/motivate', 'POST', { context });
        return response.message;
    } catch (error) {
        // Fallback motivational messages
        const fallbackMessages = {
            'new_habit': 'Great choice! Start small and stay consistent - you\'ve got this! 🌟',
            'habit_completed': 'Awesome work! Every day you stick to your habits, you\'re becoming stronger! 💪',
            'task_completed': 'Task completed! You\'re making great progress today! ✨',
            'streak_broken': 'No worries! Every expert was once a beginner. Tomorrow is a fresh start! 🌅',
            'general': 'Small consistent actions lead to remarkable results. Keep going! 🚀'
        };
        return fallbackMessages[context] || fallbackMessages['general'];
    }
}

// AI-powered habit suggestions
async function getSmartHabitSuggestion() {
    try {
        const suggestion = await apiCall('/ai/suggest');
        return suggestion.message;
    } catch (error) {
        const fallbackSuggestions = [
            'Try "Drink water when you wake up" - a simple morning kickstart!',
            'Consider "5-minute meditation" - great for mental clarity.',
            'How about "Write 3 things you\'re grateful for" - boosts positivity!',
            'Try "Take a 10-minute walk" - easy exercise to start with.',
            'Consider "Read 10 pages of a book" - knowledge building made simple.'
        ];
        
        const randomIndex = Math.floor(Math.random() * fallbackSuggestions.length);
        return fallbackSuggestions[randomIndex];
    }
}

// AI task prioritization
async function getTaskPrioritization() {
    try {
        const priorities = await apiCall('/ai/prioritize');
        return priorities.message;
    } catch (error) {
        return 'Focus on your most important task first - you\'ve got this! 📋';
    }
}

// Refresh AI insights (useful for manual refresh)
async function refreshAIInsights() {
    // Show loading state
    const greetingEl = document.getElementById('aiGreeting');
    const insightsEl = document.getElementById('aiInsights');
    const suggestionEl = document.getElementById('suggestedHabitTitle');
    const descEl = document.getElementById('suggestedHabitDesc');
    
    if (greetingEl) greetingEl.innerHTML = '🔄 Refreshing insights...';
    if (insightsEl) insightsEl.innerHTML = '🔄 Loading...';
    if (suggestionEl) suggestionEl.textContent = '🔄 Thinking...';
    if (descEl) descEl.textContent = 'AI is analyzing your patterns...';
    
    // Reload all insights
    await loadAIInsights();
}

// Handle suggested habit addition
async function addSuggestedHabit() {
    try {
        const suggestionEl = document.getElementById('suggestedHabitTitle');
        const descEl = document.getElementById('suggestedHabitDesc');
        
        if (suggestionEl && descEl) {
            const habitName = suggestionEl.textContent;
            if (habitName && habitName !== '🔄 Thinking...' && habitName !== 'Loading suggestion...') {
                // Add the suggested habit
                const newHabit = await apiCall('/habits', 'POST', { name: habitName });
                habits.unshift(newHabit);
                renderHabits();
                
                // Show success message
                showNotification(`Added suggested habit: ${habitName}`, 'success');
                
                // Refresh AI insights to get a new suggestion
                setTimeout(() => {
                    loadAIInsights();
                }, 1000);
            }
        }
    } catch (error) {
        console.error('Failed to add suggested habit:', error);
        showNotification('Failed to add suggested habit', 'error');
    }
}

// Initialize AI features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for suggested habit button
    const btnAddSuggestedHabit = document.getElementById('btnAddSuggestedHabit');
    if (btnAddSuggestedHabit) {
        btnAddSuggestedHabit.addEventListener('click', addSuggestedHabit);
    }
});

// Make functions globally available
window.loadAIInsights = loadAIInsights;
window.refreshAIInsights = refreshAIInsights;
window.getAIMotivation = getAIMotivation;
window.getSmartHabitSuggestion = getSmartHabitSuggestion;
window.getTaskPrioritization = getTaskPrioritization;
window.addSuggestedHabit = addSuggestedHabit;