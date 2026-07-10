/* ============================================
   Vault Glass — Login Page Logic
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initPasswordToggle();
  initFormValidation();
});

/* ============================================
   Floating Particles
   ============================================ */
function initParticles() {
  const canvas = document.getElementById('particles');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let particles = [];
  let animationId;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticles() {
    particles = [];
    const count = Math.floor((canvas.width * canvas.height) / 18000);
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.8 + 0.4,
        speedX: (Math.random() - 0.5) * 0.3,
        speedY: (Math.random() - 0.5) * 0.3,
        opacity: Math.random() * 0.4 + 0.1,
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: Math.random() * 0.01 + 0.005,
        color: Math.random() > 0.7
          ? `rgba(124, 156, 255, VAR_OPACITY)`  // Periwinkle
          : Math.random() > 0.5
            ? `rgba(52, 211, 153, VAR_OPACITY)` // Emerald
            : `rgba(224, 226, 230, VAR_OPACITY)` // White
      });
    }
  }

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      p.x += p.speedX;
      p.y += p.speedY;
      p.pulse += p.pulseSpeed;

      // Wrap around
      if (p.x < -10) p.x = canvas.width + 10;
      if (p.x > canvas.width + 10) p.x = -10;
      if (p.y < -10) p.y = canvas.height + 10;
      if (p.y > canvas.height + 10) p.y = -10;

      const currentOpacity = p.opacity * (0.6 + 0.4 * Math.sin(p.pulse));
      const color = p.color.replace('VAR_OPACITY', currentOpacity.toFixed(3));

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });

    animationId = requestAnimationFrame(drawParticles);
  }

  // Respect reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  resize();
  createParticles();

  if (!prefersReducedMotion) {
    drawParticles();
  } else {
    // Draw once, static
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      const color = p.color.replace('VAR_OPACITY', p.opacity.toFixed(3));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });
  }

  window.addEventListener('resize', () => {
    resize();
    createParticles();
  });
}

/* ============================================
   Password Visibility Toggle
   ============================================ */
function initPasswordToggle() {
  const toggle = document.getElementById('passwordToggle');
  const passwordInput = document.getElementById('password');
  if (!toggle || !passwordInput) return;

  const eyeOpen = toggle.querySelector('.eye-open');
  const eyeClosed = toggle.querySelector('.eye-closed');

  toggle.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    eyeOpen.style.display = isPassword ? 'none' : 'block';
    eyeClosed.style.display = isPassword ? 'block' : 'none';
    passwordInput.focus();
  });
}

/* ============================================
   Form Validation & Submission
   ============================================ */
function initFormValidation() {
  const form = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const emailError = document.getElementById('emailError');
  const passwordError = document.getElementById('passwordError');
  const emailGroup = document.getElementById('emailGroup');
  const passwordGroup = document.getElementById('passwordGroup');
  const signInBtn = document.getElementById('signInBtn');

  if (!form) return;

  // Clear errors on input
  emailInput.addEventListener('input', () => {
    clearError(emailGroup, emailError);
  });

  passwordInput.addEventListener('input', () => {
    clearError(passwordGroup, passwordError);
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    let valid = true;

    // Validate email
    const email = emailInput.value.trim();
    if (!email) {
      showError(emailGroup, emailError, 'Email is required');
      valid = false;
    } else if (!isValidEmail(email)) {
      showError(emailGroup, emailError, 'Please enter a valid email');
      valid = false;
    }

    // Validate password
    const password = passwordInput.value;
    if (!password) {
      showError(passwordGroup, passwordError, 'Password is required');
      valid = false;
    } else if (password.length < 6) {
      showError(passwordGroup, passwordError, 'Password must be at least 6 characters');
      valid = false;
    }

    if (!valid) return;

    // Simulate login
    signInBtn.classList.add('loading');
    signInBtn.disabled = true;

    await simulateLogin();

    signInBtn.classList.remove('loading');
    signInBtn.disabled = false;

    // Success feedback
    const card = document.getElementById('loginCard');
    card.classList.add('success');
    showToast('Welcome back! Redirecting to dashboard...', 'success');

    setTimeout(() => {
      card.classList.remove('success');
    }, 3000);
  });
}

function showError(group, errorEl, message) {
  group.classList.add('error');
  errorEl.textContent = message;
  errorEl.classList.add('visible');

  // Shake animation
  group.style.animation = 'shake 0.4s ease-in-out';
  setTimeout(() => {
    group.style.animation = '';
  }, 400);
}

function clearError(group, errorEl) {
  group.classList.remove('error');
  errorEl.textContent = '';
  errorEl.classList.remove('visible');
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function simulateLogin() {
  return new Promise(resolve => setTimeout(resolve, 1800));
}

/* ============================================
   Social Login Buttons
   ============================================ */
function initSocialButtons() {
  const buttons = ['googleLogin', 'appleLogin', 'githubLogin'];

  buttons.forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;

    btn.addEventListener('click', () => {
      const provider = id.replace('Login', '');
      showToast(`Redirecting to ${provider.charAt(0).toUpperCase() + provider.slice(1)}...`, 'info');
    });
  });
}

/* ============================================
   Toast Notifications
   ============================================ */
function showToast(message, type = 'info') {
  // Remove existing toasts
  document.querySelectorAll('.toast').forEach(t => t.remove());

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <div class="toast__icon">
      ${type === 'success'
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7C9CFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`
      }
    </div>
    <span class="toast__message">${message}</span>
  `;

  // Inline styles for the toast
  Object.assign(toast.style, {
    position: 'fixed',
    bottom: '24px',
    left: '50%',
    transform: 'translateX(-50%) translateY(20px)',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 22px',
    background: 'rgba(29, 32, 35, 0.92)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: `1px solid ${type === 'success' ? 'rgba(52, 211, 153, 0.25)' : 'rgba(124, 156, 255, 0.25)'}`,
    borderRadius: '16px',
    color: '#E0E2E6',
    fontFamily: "'Inter', sans-serif",
    fontSize: '14px',
    fontWeight: '500',
    zIndex: '9999',
    opacity: '0',
    transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
  });

  document.body.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
  });

  // Auto-remove
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(20px)';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

/* ============================================
   Shake Animation (injected)
   ============================================ */
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-6px); }
    40% { transform: translateX(5px); }
    60% { transform: translateX(-4px); }
    80% { transform: translateX(3px); }
  }
`;
document.head.appendChild(shakeStyle);
