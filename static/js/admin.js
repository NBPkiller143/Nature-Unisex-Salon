/**
 * Nature Unisex Salon - Admin Dashboard JavaScript
 * Handles modals, quick status updates, service editing, and sidebar toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle & Backdrop
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const adminSidebar = document.getElementById('adminSidebar') || document.querySelector('.admin-sidebar');
  const adminBackdrop = document.getElementById('adminSidebarBackdrop');

  function openSidebar() {
    if (adminSidebar) adminSidebar.classList.add('open');
    if (adminBackdrop) adminBackdrop.classList.add('active');
  }

  function closeSidebar() {
    if (adminSidebar) adminSidebar.classList.remove('open');
    if (adminBackdrop) adminBackdrop.classList.remove('active');
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (adminSidebar && adminSidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', closeSidebar);
  }

  if (adminBackdrop) {
    adminBackdrop.addEventListener('click', closeSidebar);
  }

  // Close sidebar on link click on mobile
  document.querySelectorAll('.nav-item-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 992) {
        closeSidebar();
      }
    });
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && adminSidebar && adminSidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // 2. Generic Modal Open/Close handler
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  };

  // Close modals on backdrop click
  document.querySelectorAll('.admin-modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // 3. Appointment Status Modal Helper
  window.openStatusModal = function(id, customerName, currentStatus, currentNotes) {
    const form = document.getElementById('updateStatusForm');
    const title = document.getElementById('statusModalTitle');
    const statusSelect = document.getElementById('modalStatusSelect');
    const notesArea = document.getElementById('modalNotesArea');

    if (form) {
      form.action = `/admin/appointments/status/${id}`;
    }
    if (title) {
      title.textContent = `Update Appointment #${id} - ${customerName}`;
    }
    if (statusSelect) {
      statusSelect.value = currentStatus;
    }
    if (notesArea) {
      notesArea.value = currentNotes || '';
    }
    openModal('statusModal');
  };

  // 4. Service Edit Modal Helper
  window.openEditServiceModal = function(service) {
    const form = document.getElementById('editServiceForm');
    if (!form) return;

    form.action = `/admin/services/edit/${service.id}`;
    document.getElementById('edit_service_name').value = service.name || '';
    document.getElementById('edit_gender_target').value = service.gender_target || 'Unisex';
    document.getElementById('edit_category').value = service.category || 'Hair';
    document.getElementById('edit_price').value = service.price || 0;
    document.getElementById('edit_duration').value = service.duration_mins || 30;
    document.getElementById('edit_display_order').value = service.display_order || 0;
    document.getElementById('edit_description').value = service.description || '';
    document.getElementById('edit_is_active').checked = !!service.is_active;

    openModal('editServiceModal');
  };

  // 5. Image File Preview
  document.querySelectorAll('.image-upload-input').forEach(input => {
    input.addEventListener('change', function() {
      const previewId = this.getAttribute('data-preview-target');
      const previewImg = document.getElementById(previewId);
      if (previewImg && this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
          previewImg.src = e.target.result;
          previewImg.style.display = 'block';
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  });

  // 6. Admin Appointment Notifications & Live Real-Time Polling
  const notificationBellBtn = document.getElementById('notificationBellBtn');
  const notificationsDropdown = document.getElementById('notificationsDropdown');
  const notificationCountBadge = document.getElementById('notificationCountBadge');
  const sidebarAppointmentBadge = document.getElementById('sidebarAppointmentBadge');
  const notificationsHeaderCount = document.getElementById('notificationsHeaderCount');
  const notificationsDropdownList = document.getElementById('notificationsDropdownList');
  const clearAllNotificationsBtn = document.getElementById('clearAllNotificationsBtn');
  const adminToastContainer = document.getElementById('adminToastContainer');

  // Toggle dropdown on bell click
  if (notificationBellBtn && notificationsDropdown) {
    notificationBellBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      notificationsDropdown.classList.toggle('active');
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
      if (!notificationsDropdown.contains(e.target) && e.target !== notificationBellBtn) {
        notificationsDropdown.classList.remove('active');
      }
    });
  }

  // Update UI badge counts
  function updateBadgeCounts(count) {
    if (notificationCountBadge) {
      notificationCountBadge.textContent = count;
      notificationCountBadge.classList.toggle('is-hidden', count === 0);
      notificationCountBadge.style.display = count > 0 ? 'flex' : 'none';
    }
    if (sidebarAppointmentBadge) {
      sidebarAppointmentBadge.textContent = count;
      sidebarAppointmentBadge.classList.toggle('is-hidden', count === 0);
      sidebarAppointmentBadge.style.display = count > 0 ? 'inline-block' : 'none';
    }
    if (notificationsHeaderCount) {
      notificationsHeaderCount.textContent = count;
    }
    if (count === 0 && notificationsDropdownList) {
      notificationsDropdownList.innerHTML = `
        <div class="notifications-empty" id="notificationsEmptyState">
          <i class="fa-regular fa-bell-slash" style="font-size: 2rem; color: #94a3b8; margin-bottom: 0.5rem;"></i>
          <p style="margin: 0; font-size: 0.85rem; color: #64748b; font-weight: 500;">No new appointment notifications.</p>
          <span style="font-size: 0.75rem; color: #94a3b8;">You're all caught up! ✨</span>
        </div>
      `;
    }
  }

  // Clear single notification
  document.addEventListener('click', (e) => {
    const clearBtn = e.target.closest('.btn-clear-single');
    if (clearBtn) {
      const appointmentId = clearBtn.getAttribute('data-id');
      if (!appointmentId) return;

      const card = document.getElementById(`notif-item-${appointmentId}`) || clearBtn.closest('.notification-card');
      if (card) {
        card.style.opacity = '0.4';
        card.style.pointerEvents = 'none';
      }

      fetch(`/api/admin/appointments/${appointmentId}/clear-notification`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          if (card) card.remove();
          updateBadgeCounts(data.unread_count);
        }
      })
      .catch(err => console.debug('Clear notification error:', err));
    }
  });

  // Clear all notifications
  if (clearAllNotificationsBtn) {
    clearAllNotificationsBtn.addEventListener('click', () => {
      fetch('/api/admin/appointments/clear-all-notifications', {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          updateBadgeCounts(0);
        }
      })
      .catch(err => console.debug('Clear all notifications error:', err));
    });
  }

  // Subtle web audio chime for incoming appointments
  function playNotificationChime() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880.00, ctx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
    } catch(e) { }
  }

  // Show floating toast alert
  function showAppointmentToast(appointment) {
    if (!adminToastContainer) return;

    const toast = document.createElement('div');
    toast.className = 'admin-toast';
    toast.innerHTML = `
      <div class="admin-toast-icon">
        <i class="fa-solid fa-bell"></i>
      </div>
      <div class="admin-toast-content">
        <div class="admin-toast-title">
          <span>New Appointment Booked!</span>
          <span style="font-size: 0.72rem; color: var(--admin-gold);">${appointment.time || ''}</span>
        </div>
        <div class="admin-toast-body">
          <strong>${appointment.customer_name}</strong> • ${appointment.service_name}<br>
          <small><i class="fa-regular fa-calendar"></i> ${appointment.appointment_date} at ${appointment.appointment_time}</small>
        </div>
        <div class="admin-toast-actions">
          <a href="/admin/appointments" class="admin-toast-btn primary">
            <i class="fa-solid fa-calendar-check"></i> View
          </a>
          <button type="button" class="admin-toast-btn dismiss" data-toast-clear="${appointment.id}">
            <i class="fa-solid fa-check"></i> Clear
          </button>
        </div>
      </div>
    `;

    // Dismiss click
    toast.querySelector('[data-toast-clear]')?.addEventListener('click', () => {
      fetch(`/api/admin/appointments/${appointment.id}/clear-notification`, { method: 'POST' })
        .then(res => res.json())
        .then(data => { if (data.success) updateBadgeCounts(data.unread_count); });
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    });

    adminToastContainer.appendChild(toast);

    // Auto dismiss after 8 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
      }
    }, 8000);
  }

  // Real-time polling
  let lastKnownLatestId = parseInt(sessionStorage.getItem('last_seen_appointment_id') || '0', 10);

  function pollForAppointments() {
    fetch('/api/admin/appointments/poll')
      .then(res => res.json())
      .then(data => {
        if (!data || !data.success) return;

        // Check if there's a brand new appointment
        if (lastKnownLatestId > 0 && data.latest_id > lastKnownLatestId) {
          playNotificationChime();
          if (data.unread_appointments && data.unread_appointments.length > 0) {
            showAppointmentToast(data.unread_appointments[0]);
          }
        }
        
        lastKnownLatestId = data.latest_id;
        sessionStorage.setItem('last_seen_appointment_id', data.latest_id);

        // Update badges
        updateBadgeCounts(data.unread_count);

        // Update dropdown if unread items exist
        if (data.unread_count > 0 && data.unread_appointments && notificationsDropdownList) {
          notificationsDropdownList.innerHTML = data.unread_appointments.map(app => `
            <div class="notification-card" id="notif-item-${app.id}" data-id="${app.id}">
              <div class="notif-card-body">
                <div class="notif-card-title">
                  <strong>${app.customer_name}</strong>
                  <span class="notif-time">${app.created_at}</span>
                </div>
                <div class="notif-card-desc">
                  <i class="fa-solid fa-scissors text-gold" style="font-size: 0.78rem; margin-right: 0.25rem;"></i> ${app.service_name}
                </div>
                <div class="notif-card-meta">
                  <span><i class="fa-regular fa-calendar"></i> ${app.appointment_date} at ${app.appointment_time}</span>
                  <span><i class="fa-solid fa-phone"></i> ${app.phone}</span>
                </div>
              </div>
              <div class="notif-card-actions">
                <a href="/admin/appointments" class="notif-action-btn view" title="View in Appointments">
                  <i class="fa-solid fa-arrow-right"></i>
                </a>
                <button type="button" class="notif-action-btn clear btn-clear-single" data-id="${app.id}" title="Clear notification">
                  <i class="fa-solid fa-check"></i>
                </button>
              </div>
            </div>
          `).join('');
        }
      })
      .catch(err => console.debug('Poll check error:', err));
  }

  // Start polling every 8 seconds
  setInterval(pollForAppointments, 8000);
});
