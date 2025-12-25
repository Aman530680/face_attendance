// Enhanced Admin Panel JavaScript
let statusCheckInterval;
let currentUsers = [];
let currentSchedules = [];

// Initialize admin panel
document.addEventListener('DOMContentLoaded', function() {
    loadSystemSettings();
    loadStatistics();
    loadUsers();
    loadSchedules();
    loadAttendanceRecords();
    
    // Start status checking
    statusCheckInterval = setInterval(checkSystemStatus, 3000);
    
    // Setup form handlers
    setupFormHandlers();
});

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'attendance') {
        loadAttendanceRecords();
    }
}

// System Settings
function loadSystemSettings() {
    fetch('/api/settings')
        .then(response => response.json())
        .then(data => {
            const cameraToggle = document.getElementById('camera-toggle');
            const captureMode = document.getElementById('capture-mode');
            
            if (data.camera_always_on) {
                cameraToggle.classList.add('active');
                document.getElementById('camera-status').textContent = 'ON';
            } else {
                cameraToggle.classList.remove('active');
                document.getElementById('camera-status').textContent = 'OFF';
            }
            
            captureMode.value = data.capture_mode || 'continuous';
        })
        .catch(error => console.error('Error loading settings:', error));
}

function saveSystemSettings() {
    const cameraAlwaysOn = document.getElementById('camera-toggle').classList.contains('active');
    const captureMode = document.getElementById('capture-mode').value;
    
    const settings = {
        camera_always_on: cameraAlwaysOn,
        capture_mode: captureMode
    };
    
    fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Settings saved successfully!');
        } else {
            alert('Failed to save settings');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        alert('Error saving settings');
    });
}

// Camera toggle
document.getElementById('camera-toggle').addEventListener('click', function() {
    const isActive = this.classList.contains('active');
    const action = isActive ? 'stop' : 'start';
    
    fetch('/api/camera/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            this.classList.toggle('active');
            document.getElementById('camera-status').textContent = isActive ? 'OFF' : 'ON';
        } else {
            alert('Failed to control camera: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error controlling camera:', error);
        alert('Error controlling camera');
    });
});

// Statistics
function loadStatistics() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-users').textContent = data.registered_users || 0;
            document.getElementById('active-schedules').textContent = data.active_schedules || 0;
            document.getElementById('camera-status-stat').textContent = data.camera_running ? 'ON' : 'OFF';
        })
        .catch(error => console.error('Error loading statistics:', error));
    
    // Load today's attendance count
    const today = new Date().toISOString().split('T')[0];
    fetch(`/api/attendance?date=${today}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('today-attendance').textContent = data.length || 0;
        })
        .catch(error => console.error('Error loading attendance count:', error));
}

function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update registration panel
            const registrationPanel = document.getElementById('registration-panel');
            if (data.new_user_detected) {
                registrationPanel.style.display = 'block';
            } else {
                registrationPanel.style.display = 'none';
            }
            
            // Update camera status
            document.getElementById('camera-status-stat').textContent = data.camera_running ? 'ON' : 'OFF';
        })
        .catch(error => console.error('Error checking status:', error));
}

// User Management
function loadUsers() {
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            currentUsers = data;
            displayUsers(data);
            updateUserFilter(data);
        })
        .catch(error => console.error('Error loading users:', error));
}

function displayUsers(users) {
    const usersGrid = document.getElementById('users-grid');
    
    if (users.length === 0) {
        usersGrid.innerHTML = '<p>No users registered yet.</p>';
        return;
    }
    
    usersGrid.innerHTML = users.map(user => `
        <div class="user-card">
            <h4>${user.name}</h4>
            <p><strong>ID:</strong> ${user.user_id}</p>
            <p><strong>Role:</strong> ${user.role}</p>
            <p><strong>Department:</strong> ${user.department || 'N/A'}</p>
            <p><strong>Class:</strong> ${user.class_section || 'N/A'}</p>
            <p><strong>Phone:</strong> ${user.phone || 'N/A'}</p>
            <p><strong>Email:</strong> ${user.email || 'N/A'}</p>
            <p><strong>Status:</strong> <span class="status-badge status-${user.status}">${user.status}</span></p>
            <div class="form-actions">
                <button class="btn btn-primary" onclick="editUser('${user.user_id}')">Edit</button>
                <button class="btn btn-danger" onclick="deleteUser('${user.user_id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function updateUserFilter(users) {
    const userFilter = document.getElementById('user-filter');
    userFilter.innerHTML = '<option value="">All Users</option>' +
        users.map(user => `<option value="${user.user_id}">${user.name} (${user.user_id})</option>`).join('');
}

function showAddUserModal() {
    document.getElementById('add-user-modal').style.display = 'block';
}

function editUser(userId) {
    const user = currentUsers.find(u => u.user_id === userId);
    if (!user) return;
    
    // Fill form with user data
    const form = document.getElementById('add-user-form');
    form.elements.name.value = user.name;
    form.elements.user_id.value = user.user_id;
    form.elements.user_id.readOnly = true; // Don't allow changing user ID
    form.elements.role.value = user.role;
    form.elements.department.value = user.department || '';
    form.elements.class_section.value = user.class_section || '';
    form.elements.phone.value = user.phone || '';
    form.elements.email.value = user.email || '';
    
    // Change form action to update
    form.dataset.action = 'update';
    form.dataset.userId = userId;
    
    document.querySelector('#add-user-modal h2').textContent = 'Edit User';
    document.getElementById('add-user-modal').style.display = 'block';
}

function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    fetch(`/api/users/${userId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('User deleted successfully!');
            loadUsers();
            loadStatistics();
        } else {
            alert('Failed to delete user: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        alert('Error deleting user');
    });
}

// Schedule Management
function loadSchedules() {
    fetch('/api/schedules')
        .then(response => response.json())
        .then(data => {
            currentSchedules = data;
            displaySchedules(data);
        })
        .catch(error => console.error('Error loading schedules:', error));
}

function displaySchedules(schedules) {
    const schedulesList = document.getElementById('schedules-list');
    
    if (schedules.length === 0) {
        schedulesList.innerHTML = '<p>No schedules configured yet.</p>';
        return;
    }
    
    schedulesList.innerHTML = schedules.map(schedule => `
        <div class="schedule-card">
            <h4>${schedule.name}</h4>
            <p><strong>Type:</strong> ${schedule.schedule_type}</p>
            <p><strong>Time:</strong> ${schedule.start_time || 'N/A'} - ${schedule.end_time || 'N/A'}</p>
            <p><strong>Days:</strong> ${formatDaysOfWeek(schedule.days_of_week)}</p>
            <p><strong>Interval:</strong> ${schedule.interval_minutes} minutes</p>
            <p><strong>Status:</strong> <span class="status-badge status-${schedule.is_active ? 'active' : 'inactive'}">${schedule.is_active ? 'Active' : 'Inactive'}</span></p>
            <div class="form-actions">
                <button class="btn btn-primary" onclick="editSchedule(${schedule.id})">Edit</button>
                <button class="btn btn-danger" onclick="deleteSchedule(${schedule.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function formatDaysOfWeek(days) {
    if (!days || !Array.isArray(days)) return 'All days';
    
    const dayNames = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.map(day => dayNames[parseInt(day)]).join(', ');
}

function showAddScheduleModal() {
    document.getElementById('add-schedule-modal').style.display = 'block';
}

function toggleScheduleFields(scheduleType) {
    const intervalField = document.getElementById('interval-field');
    if (scheduleType === 'recurring') {
        intervalField.style.display = 'block';
    } else {
        intervalField.style.display = 'none';
    }
}

function editSchedule(scheduleId) {
    const schedule = currentSchedules.find(s => s.id === scheduleId);
    if (!schedule) return;
    
    // Fill form with schedule data
    const form = document.getElementById('add-schedule-form');
    form.elements.name.value = schedule.name;
    form.elements.schedule_type.value = schedule.schedule_type;
    form.elements.start_time.value = schedule.start_time || '';
    form.elements.end_time.value = schedule.end_time || '';
    form.elements.interval_minutes.value = schedule.interval_minutes || 60;
    
    // Set days checkboxes
    const dayCheckboxes = form.querySelectorAll('input[name="days"]');
    dayCheckboxes.forEach(cb => cb.checked = false);
    if (schedule.days_of_week) {
        schedule.days_of_week.forEach(day => {
            const checkbox = form.querySelector(`input[name="days"][value="${day}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
    
    // Change form action to update
    form.dataset.action = 'update';
    form.dataset.scheduleId = scheduleId;
    
    document.querySelector('#add-schedule-modal h2').textContent = 'Edit Schedule';
    toggleScheduleFields(schedule.schedule_type);
    document.getElementById('add-schedule-modal').style.display = 'block';
}

function deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    
    fetch(`/api/schedules/${scheduleId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Schedule deleted successfully!');
            loadSchedules();
            loadStatistics();
        } else {
            alert('Failed to delete schedule: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting schedule:', error);
        alert('Error deleting schedule');
    });
}

// Attendance Records
function loadAttendanceRecords() {
    const dateFilter = document.getElementById('date-filter').value;
    const userFilter = document.getElementById('user-filter').value;
    
    let url = '/api/attendance?';
    if (dateFilter) url += `date=${dateFilter}&`;
    if (userFilter) url += `user_id=${userFilter}&`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayAttendanceRecords(data);
        })
        .catch(error => console.error('Error loading attendance records:', error));
}

function displayAttendanceRecords(records) {
    const tbody = document.getElementById('attendance-tbody');
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No attendance records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = records.map(record => `
        <tr>
            <td>${record.date}</td>
            <td>${record.time}</td>
            <td>${record.user_id}</td>
            <td>${record.name}</td>
            <td>${record.role}</td>
            <td>${record.department || 'N/A'}</td>
            <td>${record.schedule_name || 'Default'}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteAttendanceRecord(${record.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function clearAttendanceFilters() {
    document.getElementById('date-filter').value = '';
    document.getElementById('user-filter').value = '';
    loadAttendanceRecords();
}

function deleteAttendanceRecord(recordId) {
    if (!confirm('Are you sure you want to delete this attendance record?')) return;
    
    fetch(`/api/attendance/${recordId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Attendance record deleted successfully!');
            loadAttendanceRecords();
            loadStatistics();
        } else {
            alert('Failed to delete record: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting record:', error);
        alert('Error deleting record');
    });
}

// Form Handlers
function setupFormHandlers() {
    // Registration form
    document.getElementById('registration-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('User registered successfully!');
                this.reset();
                loadUsers();
                loadStatistics();
            } else {
                alert('Registration failed: ' + result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Registration failed');
        });
    });
    
    // Add/Edit user form
    document.getElementById('add-user-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        const isUpdate = this.dataset.action === 'update';
        const url = isUpdate ? `/api/users/${this.dataset.userId}` : '/api/users';
        const method = isUpdate ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert(`User ${isUpdate ? 'updated' : 'added'} successfully!`);
                closeModal('add-user-modal');
                loadUsers();
                loadStatistics();
            } else {
                alert(`Failed to ${isUpdate ? 'update' : 'add'} user: ` + result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to ${isUpdate ? 'update' : 'add'} user`);
        });
    });
    
    // Add/Edit schedule form
    document.getElementById('add-schedule-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        // Get selected days
        const selectedDays = Array.from(this.querySelectorAll('input[name="days"]:checked'))
            .map(cb => cb.value);
        data.days_of_week = selectedDays;
        
        const isUpdate = this.dataset.action === 'update';
        const url = isUpdate ? `/api/schedules/${this.dataset.scheduleId}` : '/api/schedules';
        const method = isUpdate ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert(`Schedule ${isUpdate ? 'updated' : 'created'} successfully!`);
                closeModal('add-schedule-modal');
                loadSchedules();
                loadStatistics();
            } else {
                alert(`Failed to ${isUpdate ? 'update' : 'create'} schedule: ` + result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to ${isUpdate ? 'update' : 'create'} schedule`);
        });
    });
}

// Modal Management
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    
    // Reset form if it's a form modal
    if (modalId === 'add-user-modal') {
        const form = document.getElementById('add-user-form');
        form.reset();
        form.elements.user_id.readOnly = false;
        delete form.dataset.action;
        delete form.dataset.userId;
        document.querySelector('#add-user-modal h2').textContent = 'Add New User';
    } else if (modalId === 'add-schedule-modal') {
        const form = document.getElementById('add-schedule-form');
        form.reset();
        delete form.dataset.action;
        delete form.dataset.scheduleId;
        document.querySelector('#add-schedule-modal h2').textContent = 'Add New Schedule';
    }
}

// Utility Functions
function clearRegistrationForm() {
    document.getElementById('registration-form').reset();
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
});