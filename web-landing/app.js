// SportSync AI - Frontend JavaScript
// ==========================================

// Particles.js Configuration
particlesJS('particles-js', {
    particles: {
        number: { value: 80, density: { enable: true, value_area: 800 } },
        color: { value: '#00ff88' },
        shape: { type: 'circle' },
        opacity: { value: 0.5, random: false },
        size: { value: 3, random: true },
        line_linked: {
            enable: true,
            distance: 150,
            color: '#00ff88',
            opacity: 0.4,
            width: 1
        },
        move: {
            enable: true,
            speed: 2,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false
        }
    },
    interactivity: {
        detect_on: 'canvas',
        events: {
            onhover: { enable: true, mode: 'repulse' },
            onclick: { enable: true, mode: 'push' },
            resize: true
        }
    },
    retina_detect: true
});

// Animated Counter
function animateCounter(element) {
    const target = parseFloat(element.getAttribute('data-target'));
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target % 1 === 0 ? target : target.toFixed(1);
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Intersection Observer for Counters
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number').forEach(counter => {
    observer.observe(counter);
});

// Live Users Counter (Simulated)
function updateLiveUsers() {
    const element = document.getElementById('live-users');
    if (element) {
        const base = 1247;
        const variation = Math.floor(Math.random() * 20) - 10;
        element.textContent = (base + variation).toLocaleString();
    }
}
setInterval(updateLiveUsers, 5000);

// Start Quiz Function
function startQuiz() {
    // Redirect to quiz page (Render backend)
    window.location.href = 'https://sportsync-ai-quiz.onrender.com';
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Navbar Scroll Effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.background = 'rgba(0, 0, 0, 0.98)';
        navbar.style.boxShadow = '0 5px 30px rgba(0, 255, 136, 0.1)';
    } else {
        navbar.style.background = 'rgba(0, 0, 0, 0.95)';
        navbar.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

console.log('🚀 SportSync AI Loaded Successfully!');
// ==========================================
// Modal Functions
// ==========================================

function showAuthModal() {
    document.getElementById('authModal').style.display = 'block';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
}

function openFeedback() {
    document.getElementById('feedbackModal').style.display = 'block';
}

function closeFeedbackModal() {
    document.getElementById('feedbackModal').style.display = 'none';
}

// Close modal on outside click
window.onclick = function(event) {
    const authModal = document.getElementById('authModal');
    const feedbackModal = document.getElementById('feedbackModal');
    if (event.target == authModal) {
        closeAuthModal();
    }
    if (event.target == feedbackModal) {
        closeFeedbackModal();
    }
}

// ==========================================
// Google OAuth (Placeholder - needs Supabase)
// ==========================================

function loginWithGoogle() {
    // TODO: Replace with actual Supabase OAuth
    // For now: Redirect directly to quiz
    closeAuthModal();
    window.location.href = '/quiz.html';
}

// ==========================================
// Feedback Submission
// ==========================================

function submitFeedback(event) {
    event.preventDefault();
    
    const feedbackText = document.getElementById('feedbackText').value;
    const feedbackEmail = document.getElementById('feedbackEmail').value;
    
    // TODO: Send to backend
    console.log('Feedback:', { text: feedbackText, email: feedbackEmail });
    
    // Show success message
    alert('✅ شكراً لمشاركة رأيك!\n\nسنراجع ملاحظاتك ونحسّن التجربة.');
    
    // Reset form and close
    document.getElementById('feedbackForm').reset();
    closeFeedbackModal();
}

console.log('🚀 SportSync AI - Auth & Feedback Ready!');
// ==========================================
// Language Switcher
// ==========================================

const translations = {
    ar: {
        mission: 'نخترع لك رياضتك الخاصة',
        title: 'اكتشف رياضتك المثالية',
        subtitle: 'بذكاء اصطناعي متقدم',
        vision: 'الرؤية: كل شخص يستحق رياضة تناسب DNA شخصيته الفريدة',
        goal: 'الهدف: نحلل 141 طبقة نفسية لنخترع لك تجربة رياضية لا تتكرر',
        cta: '🚀 ابدأ الآن - سجّل دخول مجاناً',
        liveUsers: 'اكتشفوا رياضتهم اليوم'
    },
    en: {
        mission: 'We invent your unique sport',
        title: 'Discover Your Perfect Sport',
        subtitle: 'With Advanced AI',
        vision: 'Vision: Everyone deserves a sport that matches their unique personality DNA',
        goal: 'Goal: We analyze 141 psychological layers to invent a unique sports experience for you',
        cta: '🚀 Start Now - Sign In Free',
        liveUsers: 'discovered their sport today'
    }
};

let currentLang = 'ar';

function switchLanguage(lang) {
    currentLang = lang;
    
    // Update active button
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('active');
        }
    });
    
    // Update direction
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    
    // TODO: Update all text content
    // For now, just show alert
    if (lang === 'en') {
        alert('🚧 English version coming soon!\n\nCurrently in development.');
    }
}

// Event listeners
document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchLanguage(btn.getAttribute('data-lang'));
    });
});

console.log('🌐 Language Switcher Ready!');