/**
 * Nature Unisex Salon - Public Master JavaScript
 * Handles navigation, interactive filters, gallery lightbox, and booking flow.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Sticky Navigation on Scroll
  const navbar = document.querySelector('.navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      navbar?.classList.add('scrolled');
    } else {
      navbar?.classList.remove('scrolled');
    }
  });

  // 2. Mobile Menu Drawer & Backdrop Toggle
  const mobileToggle = document.getElementById('mobileMenuToggle') || document.querySelector('.mobile-toggle');
  const navLinks = document.getElementById('navLinks') || document.querySelector('.nav-links');
  const navBackdrop = document.getElementById('navBackdrop') || document.querySelector('.nav-backdrop');

  function openMobileMenu() {
    if (!navLinks) return;
    navLinks.classList.add('active');
    navBackdrop?.classList.add('active');
    document.body.classList.add('nav-open');
    const icon = mobileToggle?.querySelector('i');
    if (icon) {
      icon.classList.remove('fa-bars');
      icon.classList.add('fa-xmark');
    }
  }

  function closeMobileMenu() {
    if (!navLinks) return;
    navLinks.classList.remove('active');
    navBackdrop?.classList.remove('active');
    document.body.classList.remove('nav-open');
    const icon = mobileToggle?.querySelector('i');
    if (icon) {
      icon.classList.remove('fa-xmark');
      icon.classList.add('fa-bars');
    }
  }

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (navLinks.classList.contains('active')) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });

    navBackdrop?.addEventListener('click', closeMobileMenu);

    // Close menu when clicking any nav link
    document.querySelectorAll('.nav-link, .nav-mobile-actions a').forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navLinks.classList.contains('active')) {
        closeMobileMenu();
      }
    });
  }

  // 3. Client-Side Service Catalog Filtering (Instant Filter)
  const filterButtons = document.querySelectorAll('.service-filter-btn');
  const serviceCards = document.querySelectorAll('.service-card-item');

  if (filterButtons.length > 0 && serviceCards.length > 0) {
    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const gender = btn.getAttribute('data-gender') || 'all';
        const category = btn.getAttribute('data-category') || 'all';

        serviceCards.forEach(card => {
          const cardGender = card.getAttribute('data-gender');
          const cardCat = card.getAttribute('data-category');

          const matchGender = (gender === 'all') || (cardGender === gender) || (cardGender === 'Unisex');
          const matchCat = (category === 'all') || (cardCat === category);

          if (matchGender && matchCat) {
            card.style.display = 'flex';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }

  // 4. Gallery Lightbox Modal
  const lightbox = document.getElementById('galleryLightbox');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxCaption = document.getElementById('lightboxCaption');
  const lightboxClose = document.querySelector('.lightbox-close');

  document.querySelectorAll('.gallery-card').forEach(item => {
    item.addEventListener('click', () => {
      const src = item.getAttribute('data-image');
      const caption = item.getAttribute('data-caption');
      if (lightbox && lightboxImg) {
        lightboxImg.src = src;
        if (lightboxCaption) lightboxCaption.textContent = caption || '';
        lightbox.classList.add('active');
      }
    });
  });

  if (lightboxClose) {
    lightboxClose.addEventListener('click', () => {
      lightbox.classList.remove('active');
    });
  }

  if (lightbox) {
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) {
        lightbox.classList.remove('active');
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightbox && lightbox.classList.contains('active')) {
      lightbox.classList.remove('active');
    }
  });

  // 5. Booking Form - Dynamic WhatsApp link generator helper
  const bookingForm = document.getElementById('appointmentBookingForm');
  const serviceSelect = document.getElementById('serviceSelect');
  const dateInput = document.getElementById('appointmentDate');
  const timeInput = document.getElementById('appointmentTime');
  const nameInput = document.getElementById('customerName');

  // Set minimum date for booking to today
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    if (!dateInput.value) {
      dateInput.value = today;
    }
  }

  // 6. Toast Notification auto-dismiss
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  });
});
