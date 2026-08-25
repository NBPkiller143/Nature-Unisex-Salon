/**
 * Nature Unisex Salon - Admin Dashboard JavaScript
 * Handles modals, quick status updates, service editing, and sidebar toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const adminSidebar = document.querySelector('.admin-sidebar');
  if (sidebarToggle && adminSidebar) {
    sidebarToggle.addEventListener('click', () => {
      adminSidebar.classList.toggle('open');
    });
  }

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
});
