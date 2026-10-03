// Global variables
let currentAppId = null;
let currentTicketId = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupNavigation();
    refreshDashboard();
    loadApplications();
    loadTickets();
    loadReminders();

    // Auto-refresh every 30 seconds
    setInterval(refreshDashboard, 30000);
    setInterval(loadTickets, 30000);
});

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const view = this.dataset.view;
            showView(view);

            // Update active nav item
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function showView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // Show selected view
    document.getElementById(viewName).classList.add('active');

    // Load data for the view
    if (viewName === 'dashboard') {
        refreshDashboard();
    } else if (viewName === 'applications') {
        loadApplications();
    } else if (viewName === 'tickets') {
        loadTickets();
    } else if (viewName === 'reminders') {
        loadReminders();
    }
}

// Dashboard
async function refreshDashboard() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();

        if (data.success) {
            updateDashboard(data);
            loadRecentApplications();
        }
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

function updateDashboard(stats) {
    document.getElementById('total-apps').textContent = stats.total;
    document.getElementById('pending-apps').textContent = stats.pending;
    document.getElementById('approved-apps').textContent = stats.approved;
    document.getElementById('rejected-apps').textContent = stats.rejected;
    document.getElementById('approval-rate').textContent = stats.approval_rate + '%';
    document.getElementById('review-time').textContent = stats.avg_review_time + ' hrs';
}

async function loadRecentApplications() {
    try {
        const response = await fetch('/api/applications?status=all');
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('recent-apps');
            const recent = data.data.slice(0, 5);

            if (recent.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No applications yet</p></div>';
                return;
            }

            container.innerHTML = recent.map(app => createAppCard(app)).join('');
        }
    } catch (error) {
        console.error('Error loading recent applications:', error);
    }
}

// Applications
async function loadApplications() {
    try {
        const status = document.getElementById('status-filter')?.value || 'all';
        const response = await fetch(`/api/applications?status=${status}`);
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('applications-container');

            if (data.data.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No applications found</p></div>';
                return;
            }

            container.innerHTML = data.data.map(app => createAppCard(app)).join('');
        }
    } catch (error) {
        console.error('Error loading applications:', error);
    }
}

function filterApplications() {
    loadApplications();
}

function createAppCard(app) {
    const submitted = new Date(app.submitted_at).toLocaleString();
    const statusClass = app.status.toLowerCase();

    let reviewed = 'N/A';
    if (app.reviewed_at) {
        reviewed = new Date(app.reviewed_at).toLocaleString();
    }

    return `
        <div class="app-card ${statusClass}">
            <div class="app-header">
                <div class="app-title">${escapeHtml(app.full_name)}</div>
                <span class="status-badge ${statusClass}">${app.status}</span>
            </div>
            <div class="app-meta">
                <div class="app-meta-item">
                    <div class="app-meta-label">Email</div>
                    <div class="app-meta-value">${escapeHtml(app.email)}</div>
                </div>
                <div class="app-meta-item">
                    <div class="app-meta-label">Username</div>
                    <div class="app-meta-value">@${escapeHtml(app.username)}</div>
                </div>
                <div class="app-meta-item">
                    <div class="app-meta-label">Submitted</div>
                    <div class="app-meta-value">${submitted}</div>
                </div>
                <div class="app-meta-item">
                    <div class="app-meta-label">Reviewed</div>
                    <div class="app-meta-value">${reviewed}</div>
                </div>
            </div>
            <div class="app-actions">
                <button class="btn-primary" onclick="viewApplicationDetails('${app.id}')">View Details</button>
                ${app.status === 'pending' ? `<button class="btn-secondary" onclick="openReviewModal('${app.id}')">Review</button>` : ''}
            </div>
        </div>
    `;
}

async function viewApplicationDetails(appId) {
    try {
        const response = await fetch(`/api/applications/${appId}`);
        const data = await response.json();

        if (data.success) {
            const app = data.data;
            const detailsHtml = `
                <div class="app-details-item">
                    <div class="app-details-label">Application ID:</div>
                    <div class="app-details-value"><code>${escapeHtml(app.id)}</code></div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Full Name:</div>
                    <div class="app-details-value">${escapeHtml(app.full_name)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Email:</div>
                    <div class="app-details-value">${escapeHtml(app.email)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Username:</div>
                    <div class="app-details-value">@${escapeHtml(app.username)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Why Join:</div>
                    <div class="app-details-value">${escapeHtml(app.reason)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Experience:</div>
                    <div class="app-details-value">${escapeHtml(app.experience)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Status:</div>
                    <div class="app-details-value"><span class="status-badge ${app.status}">${app.status}</span></div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Submitted At:</div>
                    <div class="app-details-value">${new Date(app.submitted_at).toLocaleString()}</div>
                </div>
                ${app.reviewed_at ? `
                    <div class="app-details-item">
                        <div class="app-details-label">Reviewed At:</div>
                        <div class="app-details-value">${new Date(app.reviewed_at).toLocaleString()}</div>
                    </div>
                    <div class="app-details-item">
                        <div class="app-details-label">Reviewer:</div>
                        <div class="app-details-value">${escapeHtml(app.reviewer_id || 'Unknown')}</div>
                    </div>
                    ${app.review_notes ? `
                        <div class="app-details-item">
                            <div class="app-details-label">Review Notes:</div>
                            <div class="app-details-value">${escapeHtml(app.review_notes)}</div>
                        </div>
                    ` : ''}
                ` : ''}
            `;

            alert(`Application Details:\n\n${JSON.stringify(app, null, 2)}`);
        }
    } catch (error) {
        console.error('Error loading application details:', error);
        alert('Error loading application details');
    }
}

// Review Modal
async function openReviewModal(appId) {
    try {
        const response = await fetch(`/api/applications/${appId}`);
        const data = await response.json();

        if (data.success) {
            currentAppId = appId;
            const app = data.data;

            const detailsHtml = `
                <div class="app-details-item">
                    <div class="app-details-label">Name:</div>
                    <div class="app-details-value">${escapeHtml(app.full_name)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Email:</div>
                    <div class="app-details-value">${escapeHtml(app.email)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Why Join:</div>
                    <div class="app-details-value">${escapeHtml(app.reason)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Experience:</div>
                    <div class="app-details-value">${escapeHtml(app.experience)}</div>
                </div>
            `;

            document.getElementById('application-details').innerHTML = detailsHtml;
            document.getElementById('review-notes').value = '';
            document.getElementById('reviewer-name').value = 'Admin';
            document.querySelector('input[name="decision"][value="approved"]').checked = true;

            document.getElementById('review-modal').classList.add('show');
        }
    } catch (error) {
        console.error('Error opening review modal:', error);
    }
}

function closeModal() {
    document.getElementById('review-modal').classList.remove('show');
    currentAppId = null;
}

async function submitReview() {
    if (!currentAppId) return;

    const decision = document.querySelector('input[name="decision"]:checked').value;
    const notes = document.getElementById('review-notes').value;
    const reviewer = document.getElementById('reviewer-name').value;

    try {
        const response = await fetch(`/api/applications/${currentAppId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                decision,
                notes,
                reviewer
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Application ${decision}!`);
            closeModal();
            loadApplications();
            refreshDashboard();
        } else {
            alert('Error submitting review: ' + data.error);
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        alert('Error submitting review');
    }
}

// Reminders
async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('reminders-container');

            if (data.reminders.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✅</div><p>No pending applications to review</p></div>';
                return;
            }

            container.innerHTML = data.reminders.map((reminder, index) => `
                <div class="reminder-card">
                    <div class="reminder-info">
                        <div class="reminder-item">
                            <div class="reminder-label">Applicant</div>
                            <div class="reminder-value">${escapeHtml(reminder.applicant)}</div>
                        </div>
                        <div class="reminder-item">
                            <div class="reminder-label">Email</div>
                            <div class="reminder-value">${escapeHtml(reminder.email)}</div>
                        </div>
                        <div class="reminder-item">
                            <div class="reminder-label">Pending For</div>
                            <div class="reminder-value">${reminder.hours_pending} hours</div>
                        </div>
                        <div class="reminder-item">
                            <div class="reminder-label">Submitted</div>
                            <div class="reminder-value">${new Date(reminder.submitted_at).toLocaleString()}</div>
                        </div>
                    </div>
                    <div class="app-actions">
                        <button class="btn-primary" onclick="openReviewModal('${reminder.id}')">Review Now</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

async function scheduleReminder() {
    try {
        const hours = parseInt(document.getElementById('reminder-hours').value) || 24;
        const response = await fetch('/api/reminders/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ hours })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error scheduling reminder:', error);
        alert('Error scheduling reminder');
    }
}

function updateReminderSchedule() {
    scheduleReminder();
}

// Tickets
async function loadTickets() {
    try {
        const status = document.getElementById('ticket-status-filter')?.value || 'all';
        const response = await fetch(`/api/tickets?status=${status}`);
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('tickets-container');

            if (data.data.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No tickets found</p></div>';
                return;
            }

            container.innerHTML = data.data.map(ticket => createTicketCard(ticket)).join('');
        }
    } catch (error) {
        console.error('Error loading tickets:', error);
    }
}

function filterTickets() {
    loadTickets();
}

function createTicketCard(ticket) {
    const created = new Date(ticket.created_at).toLocaleString();
    const statusClass = ticket.status.toLowerCase().replace('_', '-');
    const priorityClass = ticket.priority.toLowerCase();

    const priorityEmoji = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴',
        'urgent': '⚫'
    }[ticket.priority] || '🟡';

    const statusEmoji = {
        'open': '🟢',
        'in_progress': '🔵',
        'closed': '⚫'
    }[ticket.status] || '⚫';

    return `
        <div class="ticket-card ${statusClass}">
            <div class="ticket-header">
                <div class="ticket-title">
                    <span class="ticket-icon">🎫</span> ${escapeHtml(ticket.title)}
                </div>
                <div class="ticket-badges">
                    <span class="status-badge ${statusClass}">${statusEmoji} ${ticket.status.replace('_', ' ')}</span>
                    <span class="priority-badge priority-${priorityClass}">${priorityEmoji} ${ticket.priority}</span>
                </div>
            </div>
            <div class="ticket-meta">
                <div class="ticket-meta-item">
                    <div class="ticket-meta-label">ID</div>
                    <div class="ticket-meta-value"><code>${ticket.id}</code></div>
                </div>
                <div class="ticket-meta-item">
                    <div class="ticket-meta-label">Category</div>
                    <div class="ticket-meta-value">${ticket.category.charAt(0).toUpperCase() + ticket.category.slice(1)}</div>
                </div>
                <div class="ticket-meta-item">
                    <div class="ticket-meta-label">Created</div>
                    <div class="ticket-meta-value">${created}</div>
                </div>
                <div class="ticket-meta-item">
                    <div class="ticket-meta-label">Comments</div>
                    <div class="ticket-meta-value">${ticket.comments ? ticket.comments.length : 0}</div>
                </div>
            </div>
            <div class="ticket-description">${escapeHtml(ticket.description.substring(0, 150))}${ticket.description.length > 150 ? '...' : ''}</div>
            <div class="ticket-actions">
                <button class="btn-primary" onclick="openTicketModal('${ticket.id}')">View & Edit</button>
            </div>
        </div>
    `;
}

async function openTicketModal(ticketId) {
    try {
        const response = await fetch(`/api/tickets/${ticketId}`);
        const data = await response.json();

        if (data.success) {
            currentTicketId = ticketId;
            const ticket = data.data;

            const detailsHtml = `
                <div class="app-details-item">
                    <div class="app-details-label">Title:</div>
                    <div class="app-details-value">${escapeHtml(ticket.title)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">ID:</div>
                    <div class="app-details-value"><code>${ticket.id}</code></div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Category:</div>
                    <div class="app-details-value">${ticket.category}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Description:</div>
                    <div class="app-details-value">${escapeHtml(ticket.description)}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Created:</div>
                    <div class="app-details-value">${new Date(ticket.created_at).toLocaleString()}</div>
                </div>
                <div class="app-details-item">
                    <div class="app-details-label">Updated:</div>
                    <div class="app-details-value">${new Date(ticket.updated_at).toLocaleString()}</div>
                </div>
                ${ticket.assigned_to ? `
                    <div class="app-details-item">
                        <div class="app-details-label">Assigned To:</div>
                        <div class="app-details-value">User #${ticket.assigned_to}</div>
                    </div>
                ` : ''}
            `;

            document.getElementById('ticket-details').innerHTML = detailsHtml;
            document.getElementById('ticket-status').value = ticket.status;
            document.getElementById('ticket-priority').value = ticket.priority;
            document.getElementById('ticket-comment').value = '';

            document.getElementById('ticket-modal').classList.add('show');
        }
    } catch (error) {
        console.error('Error opening ticket modal:', error);
    }
}

function closeTicketModal() {
    document.getElementById('ticket-modal').classList.remove('show');
    currentTicketId = null;
}

async function updateTicket() {
    if (!currentTicketId) return;

    const status = document.getElementById('ticket-status').value;
    const priority = document.getElementById('ticket-priority').value;
    const comment = document.getElementById('ticket-comment').value;

    try {
        const updateResponse = await fetch(`/api/tickets/${currentTicketId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status, priority })
        });

        const updateData = await updateResponse.json();

        if (!updateData.success) {
            alert('Error updating ticket: ' + updateData.error);
            return;
        }

        if (comment.trim()) {
            await fetch(`/api/tickets/${currentTicketId}/comment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: 'Admin',
                    user_id: 0,
                    content: comment
                })
            });
        }

        alert('Ticket updated successfully!');
        closeTicketModal();
        loadTickets();
    } catch (error) {
        console.error('Error updating ticket:', error);
        alert('Error updating ticket');
    }
}

// Export
function exportCSV() {
    window.location.href = '/api/export/csv';
}

function exportExcel() {
    window.location.href = '/api/export/excel';
}

// Utility
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const reviewModal = document.getElementById('review-modal');
    const ticketModal = document.getElementById('ticket-modal');

    if (event.target === reviewModal) {
        closeModal();
    }
    if (event.target === ticketModal) {
        closeTicketModal();
    }
}
