// Admin Dashboard JavaScript

// Chart.js for charts (if you want to use it)
// You can include Chart.js from CDN or locally

// Simulate real-time data updates
class AdminDashboard {
    constructor() {
        this.init();
    }
    
    init() {
        this.initSearch();
        this.initFilters();
        this.initActivitySimulation();
        this.initCharts();
    }
    
    initSearch() {
        const searchInput = document.getElementById('searchUsers');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterUsers(e.target.value);
            });
        }
    }
    
    initFilters() {
        const roleFilter = document.getElementById('roleFilter');
        if (roleFilter) {
            roleFilter.addEventListener('change', (e) => {
                this.filterByRole(e.target.value);
            });
        }
        
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterByStatus(e.target.value);
            });
        }
    }
    
    filterUsers(searchTerm) {
        const rows = document.querySelectorAll('.user-table tbody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const username = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const email = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            
            if (username.includes(term) || email.includes(term)) {
                row.style.display = '';
                row.style.animation = 'slideIn 0.3s ease-out';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    filterByRole(role) {
        if (!role) return;
        
        const rows = document.querySelectorAll('.user-table tbody tr');
        
        rows.forEach(row => {
            const roleCell = row.querySelector('td:nth-child(4)');
            if (role === 'all' || roleCell.textContent.toLowerCase().includes(role)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    filterByStatus(status) {
        if (!status) return;
        
        const rows = document.querySelectorAll('.user-table tbody tr');
        
        rows.forEach(row => {
            const statusCell = row.querySelector('td:nth-child(5)');
            const isActive = statusCell.querySelector('.status-active') !== null;
            
            if (status === 'all' || 
                (status === 'active' && isActive) || 
                (status === 'inactive' && !isActive)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    initActivitySimulation() {
        // Simulate real-time activity updates
        setInterval(() => {
            this.addRandomActivity();
        }, 30000); // Add new activity every 30 seconds
    }
    
    addRandomActivity() {
        const activities = [
            { user: 'New User', action: 'registered', icon: 'user' },
            { user: 'Admin', action: 'updated settings', icon: 'admin' },
            { user: 'System', action: 'backup completed', icon: 'system' }
        ];
        
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        const activityList = document.querySelector('.activity-list');
        
        if (activityList) {
            const newActivity = document.createElement('div');
            newActivity.className = 'activity-item';
            newActivity.innerHTML = `
                <div class="activity-icon ${randomActivity.icon}">
                    ${randomActivity.icon === 'user' ? '👤' : randomActivity.icon === 'admin' ? '👑' : '⚙️'}
                </div>
                <div class="activity-content">
                    <div class="activity-text">${randomActivity.user} ${randomActivity.action}</div>
                    <div class="activity-time">Just now</div>
                </div>
            `;
            
            activityList.insertBefore(newActivity, activityList.firstChild);
            
            // Keep only last 10 activities
            while (activityList.children.length > 10) {
                activityList.removeChild(activityList.lastChild);
            }
        }
    }
    
    initCharts() {
        // Simple bar chart using CSS
        this.createRoleDistributionChart();
    }
    
    createRoleDistributionChart() {
        // Get role counts from the table
        const rows = document.querySelectorAll('.user-table tbody tr');
        let adminCount = 0, moderatorCount = 0, userCount = 0;
        
        rows.forEach(row => {
            const role = row.querySelector('td:nth-child(4)').textContent.trim().toLowerCase();
            if (role === 'admin') adminCount++;
            else if (role === 'moderator') moderatorCount++;
            else userCount++;
        });
        
        const total = adminCount + moderatorCount + userCount;
        
        // Update chart bars
        const adminBar = document.getElementById('admin-bar');
        const moderatorBar = document.getElementById('moderator-bar');
        const userBar = document.getElementById('user-bar');
        
        if (adminBar && moderatorBar && userBar) {
            adminBar.style.width = `${(adminCount / total) * 100}%`;
            moderatorBar.style.width = `${(moderatorCount / total) * 100}%`;
            userBar.style.width = `${(userCount / total) * 100}%`;
            
            adminBar.textContent = `${Math.round((adminCount / total) * 100)}%`;
            moderatorBar.textContent = `${Math.round((moderatorCount / total) * 100)}%`;
            userBar.textContent = `${Math.round((userCount / total) * 100)}%`;
        }
    }
    
    showNotification(message, type = 'success') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.style.animation = 'slideIn 0.3s ease-out';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new AdminDashboard();
    
    // Add click handlers for quick actions
    const quickActions = document.querySelectorAll('.quick-action-btn');
    quickActions.forEach(action => {
        action.addEventListener('click', (e) => {
            const actionText = action.querySelector('.quick-action-text').textContent;
            dashboard.showNotification(`${actionText} feature coming soon!`, 'info');
        });
    });
    
    // Add hover effect to table rows
    const tableRows = document.querySelectorAll('.user-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', () => {
            const username = row.querySelector('td:nth-child(2)').textContent;
            dashboard.showNotification(`Selected user: ${username}`, 'info');
        });
    });
    
    // Animate numbers
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(number => {
        const target = parseInt(number.textContent);
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                number.textContent = target;
                clearInterval(timer);
            } else {
                number.textContent = Math.floor(current);
            }
        }, 20);
    });
});