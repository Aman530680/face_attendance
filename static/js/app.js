// Student view JavaScript
let statusCheckInterval;
let lastRecognitionTime = 0;

// Check system status and update UI
function checkStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateAttendanceStatus(data.attendance_status);
            updateStudentInfo(data.last_recognition);
            updateSystemMessage(data);
        })
        .catch(error => {
            console.error('Error checking status:', error);
            showSystemMessage('Connection error. Please check your network.');
        });
}

// Update attendance status display
function updateAttendanceStatus(attendanceStatus) {
    const statusElement = document.getElementById('attendance-status');
    const statusText = statusElement.querySelector('.status-text');
    const timeWindow = statusElement.querySelector('.time-window');
    
    if (attendanceStatus) {
        statusText.textContent = attendanceStatus.status;
        
        if (attendanceStatus.start_time && attendanceStatus.end_time) {
            timeWindow.textContent = `${attendanceStatus.start_time} - ${attendanceStatus.end_time}`;
        }
        
        // Update status class
        statusElement.className = attendanceStatus.status === 'OPEN' ? 'status-open' : 'status-closed';
    }
}

// Update student information display
function updateStudentInfo(lastRecognition) {
    const studentInfo = document.getElementById('student-info');
    const systemMessage = document.getElementById('system-message');
    
    if (lastRecognition && lastRecognition.student) {
        const student = lastRecognition.student;
        const attendanceResult = lastRecognition.attendance_result;
        
        // Show student info panel
        studentInfo.style.display = 'block';
        systemMessage.style.display = 'none';
        
        // Update student details
        document.getElementById('student-name').textContent = student.name || '--';
        document.getElementById('student-id').textContent = student.student_id || '--';
        document.getElementById('student-class').textContent = student.class || '--';
        document.getElementById('student-department').textContent = student.department || '--';
        document.getElementById('student-roll').textContent = student.roll_no || '--';
        
        // Update attendance status
        const attendanceToday = document.getElementById('attendance-today');
        if (student.attendance_today || (attendanceResult && attendanceResult.success)) {
            attendanceToday.textContent = 'Present';
            attendanceToday.className = 'status-badge status-present';
        } else {
            attendanceToday.textContent = 'Absent';
            attendanceToday.className = 'status-badge status-absent';
        }
        
        // Show attendance message
        const messageElement = document.getElementById('attendance-message');
        if (attendanceResult) {
            messageElement.textContent = attendanceResult.message;
            messageElement.className = attendanceResult.success ? 
                'attendance-message message-success' : 
                'attendance-message message-error';
            messageElement.style.display = 'block';
        } else {
            messageElement.style.display = 'none';
        }
        
        // Update last recognition time
        lastRecognitionTime = Date.now();
    } else {
        // Hide student info after 5 seconds of no recognition
        if (Date.now() - lastRecognitionTime > 5000) {
            studentInfo.style.display = 'none';
            systemMessage.style.display = 'block';
        }
    }
}

// Update system messages
function updateSystemMessage(data) {
    const systemMessage = document.getElementById('system-message');
    
    if (data.new_user_detected) {
        showSystemMessage('New user detected. Please wait for admin approval.', 'warning');
    } else if (data.current_state === 'registration') {
        showSystemMessage('Registration in progress. Please wait...', 'info');
    } else if (!data.camera_running) {
        showSystemMessage('Camera not available. Please check camera connection.', 'error');
    } else if (document.getElementById('student-info').style.display === 'none') {
        showSystemMessage('Please stand in front of the camera for face recognition');
    }
}

// Show system message
function showSystemMessage(message, type = 'info') {
    const systemMessage = document.getElementById('system-message');
    systemMessage.innerHTML = `<p class="message-${type}">${message}</p>`;
}

// Initialize the application
function initializeApp() {
    console.log('Face Recognition Attendance System - Student View');
    
    // Start status checking
    checkStatus();
    statusCheckInterval = setInterval(checkStatus, 2000);
    
    // Handle video feed errors
    const videoFeed = document.getElementById('video-feed');
    videoFeed.onerror = function() {
        showSystemMessage('Video feed unavailable. Please refresh the page.', 'error');
    };
    
    // Add click handler to refresh video feed
    videoFeed.onclick = function() {
        this.src = this.src; // Refresh the video feed
    };
}

// Cleanup function
function cleanup() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', initializeApp);
window.addEventListener('beforeunload', cleanup);

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, reduce update frequency
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = setInterval(checkStatus, 5000);
        }
    } else {
        // Page is visible, restore normal update frequency
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = setInterval(checkStatus, 2000);
        }
    }
});

// Utility functions
function formatTime(timeString) {
    if (!timeString) return '--:--';
    return timeString.substring(0, 5); // HH:MM format
}

function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showSystemMessage('An error occurred. Please refresh the page.', 'error');
});

// Network status monitoring
window.addEventListener('online', function() {
    showSystemMessage('Connection restored');
    checkStatus();
});

window.addEventListener('offline', function() {
    showSystemMessage('Connection lost. Please check your network.', 'error');
});