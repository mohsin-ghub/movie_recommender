// Minimal loading spinner and toast notification system

// Show loading spinner overlay
function showLoading() {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner" role="status" aria-live="polite" aria-label="Loading"></div>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

// Hide loading spinner overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

// Toast notification
function showToast(message, type = 'info') {
    let toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('tabindex', '0');
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('show');
        toast.focus();
    }, 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// Dark/Light mode toggle logic
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
}

// Toggle login/signup containers
function toggleLoginSignup() {
    const showSignupBtn = document.getElementById('show-signup');
    const showLoginBtn = document.getElementById('show-login');
    const loginContainer = document.getElementById('login-container');
    const signupContainer = document.getElementById('signup-container');
    if (showSignupBtn && showLoginBtn && loginContainer && signupContainer) {
        showSignupBtn.onclick = function() {
            loginContainer.style.display = 'none';
            signupContainer.style.display = 'flex';
        };
        showLoginBtn.onclick = function() {
            signupContainer.style.display = 'none';
            loginContainer.style.display = 'flex';
        };
    }
}

// Forgot password modal
function showForgotPasswordModal() {
    const forgotBtn = document.getElementById('forgot-password-btn');
    const forgotModal = document.getElementById('forgot-password-modal');
    const closeForgot = document.getElementById('close-forgot-modal');
    if (forgotBtn && forgotModal) {
        forgotBtn.onclick = function() {
            forgotModal.style.display = 'flex';
        };
    }
    if (closeForgot && forgotModal) {
        closeForgot.onclick = function() {
            forgotModal.style.display = 'none';
        };
    }
}

// Password strength meter
function checkPasswordStrength() {
    const signupPassword = document.getElementById('signup-password');
    const strengthDiv = document.getElementById('password-strength');
    if (signupPassword && strengthDiv) {
        signupPassword.addEventListener('input', function() {
            const val = signupPassword.value;
            let score = 0;
            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[a-z]/.test(val)) score++;
            if (/\d/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;
            let msg = '';
            let color = '';
            if (val.length === 0) {
                msg = '';
            } else if (score <= 2) {
                msg = 'Weak'; color = '#e53935';
            } else if (score === 3 || score === 4) {
                msg = 'Medium'; color = '#f4d47c';
            } else if (score === 5) {
                msg = 'Strong'; color = '#4caf50';
            }
            strengthDiv.textContent = msg;
            strengthDiv.style.color = color;
        });
    }
}

// Show/hide password toggle
function togglePassword(id, btn) {
    const input = document.getElementById(id);
    const svg = btn.querySelector('svg');
    if (input) {
        if (input.type === 'password') {
            input.type = 'text';
            // Change to eye-off icon
            if (svg) {
                svg.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/><line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>';
            }
        } else {
            input.type = 'password';
            // Change to eye icon
            if (svg) {
                svg.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>';
            }
        }
    }
}

// Attach to form submit for loading
window.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.movie-form');
    if (form) {
        form.addEventListener('submit', function() {
            showLoading();
        });
    }
    // Hide loading on page load (in case)
    hideLoading();

    // Show toasts for flashed messages
    const flashEls = document.querySelectorAll('.flash-message');
    flashEls.forEach(el => {
        const type = el.classList.contains('flash-error') ? 'error' : (el.classList.contains('flash-success') ? 'success' : 'info');
        showToast(el.innerText, type);
        el.remove();
    });

    // Theme initialization
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    // Keyboard accessibility for toggle
    const themeBtn = document.querySelector('.theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }
    // Poster entrance animation
    var posterImg = document.querySelector('.poster-card img');
    if (posterImg && window.anime) {
        window.anime({
            targets: posterImg,
            opacity: [0, 1],
            scale: [0.96, 1],
            translateY: [24, 0],
            duration: 700,
            easing: 'easeOutCubic'
        });
    }
    // Toggle login/signup containers
    toggleLoginSignup();
    // Forgot password modal
    showForgotPasswordModal();
    // Password strength meter
    checkPasswordStrength();
}); 