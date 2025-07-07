/**
 * Homepage Interactions - SonoUno
 * Animaciones e interacciones para la página de inicio
 */

// Configuración de animaciones
const ANIMATION_CONFIG = {
    fadeDelay: 100,         // Delay entre animaciones de elementos
    hoverScale: 1.02,       // Escala al hacer hover
    hoverElevation: -5,     // Elevación en hover (px)
    rippleDuration: 600     // Duración del efecto ripple (ms)
};

// Clase principal para manejar las interacciones de la homepage
class HomepageInteractions {
    constructor() {
        this.init();
    }

    init() {
        this.setupFadeInAnimations();
        this.setupHoverEffects();
        this.setupRippleEffects();
        this.setupLogoAnimation();
    }

    /**
     * Configura las animaciones de aparición gradual
     */
    setupFadeInAnimations() {
        // Observer para detectar elementos que entran en viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Aplicar animaciones a elementos principales
        const animatedElements = document.querySelectorAll(
            '.brand-wrapper, .apps-title-wrapper, .app-button-large'
        );
        
        animatedElements.forEach((el, index) => {
            // Estado inicial
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = `all 0.6s ease ${index * ANIMATION_CONFIG.fadeDelay}ms`;
            
            // Observar elemento
            observer.observe(el);
        });
    }

    /**
     * Configura efectos hover mejorados para botones
     */
    setupHoverEffects() {
        const appButtons = document.querySelectorAll('.app-button-large');
        
        appButtons.forEach(button => {
            // Mouse enter
            button.addEventListener('mouseenter', (e) => {
                e.target.style.transform = `translateY(${ANIMATION_CONFIG.hoverElevation}px) scale(${ANIMATION_CONFIG.hoverScale})`;
                
                // Añadir clase para efectos CSS adicionales
                e.target.classList.add('button-hovered');
            });
            
            // Mouse leave
            button.addEventListener('mouseleave', (e) => {
                e.target.style.transform = 'translateY(0) scale(1)';
                e.target.classList.remove('button-hovered');
            });

            // Focus para accesibilidad
            button.addEventListener('focus', (e) => {
                e.target.style.outline = '2px solid rgba(0, 33, 71, 0.5)';
                e.target.style.outlineOffset = '4px';
            });

            button.addEventListener('blur', (e) => {
                e.target.style.outline = 'none';
            });
        });
    }

    /**
     * Configura efectos ripple al hacer clic
     */
    setupRippleEffects() {
        const appButtons = document.querySelectorAll('.app-button-large');
        
        appButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.createRipple(e, button);
            });
        });
    }

    /**
     * Crea el efecto ripple en un elemento
     */
    createRipple(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        // Estilos del ripple
        Object.assign(ripple.style, {
            width: size + 'px',
            height: size + 'px',
            left: x + 'px',
            top: y + 'px',
            position: 'absolute',
            borderRadius: '50%',
            background: 'rgba(0, 33, 71, 0.3)',
            transform: 'scale(0)',
            animation: `ripple ${ANIMATION_CONFIG.rippleDuration}ms linear`,
            pointerEvents: 'none',
            zIndex: '10'
        });
        
        element.appendChild(ripple);
        
        // Remover después de la animación
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.remove();
            }
        }, ANIMATION_CONFIG.rippleDuration);
    }

    /**
     * Configura animación especial para el logo
     */
    setupLogoAnimation() {
        const logo = document.querySelector('.brand-logo');
        if (!logo) return;

        let rotationAngle = 0;
        
        logo.addEventListener('mouseenter', () => {
            logo.style.filter = 'brightness(1.1) contrast(1.1)';
            logo.style.transform = `scale(1.05) rotate(${rotationAngle}deg)`;
            rotationAngle += 5; // Pequeña rotación acumulativa
        });

        logo.addEventListener('mouseleave', () => {
            logo.style.filter = 'brightness(1) contrast(1)';
            logo.style.transform = 'scale(1) rotate(0deg)';
        });
    }
}

// Clase para efectos de texto dinámicos
class TextEffects {
    constructor() {
        this.init();
    }

    init() {
        this.setupTypingEffect();
        this.setupTextGlow();
    }

    /**
     * Efecto de typing para el subtítulo
     */
    setupTypingEffect() {
        const subtitle = document.querySelector('.apps-subtitle');
        if (!subtitle) return;

        const originalText = subtitle.textContent;
        subtitle.textContent = '';
        
        let charIndex = 0;
        const typingSpeed = 50;

        const typeText = () => {
            if (charIndex < originalText.length) {
                subtitle.textContent += originalText.charAt(charIndex);
                charIndex++;
                setTimeout(typeText, typingSpeed);
            }
        };

        // Iniciar typing cuando el elemento es visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(typeText, 800); // Delay inicial
                    observer.unobserve(entry.target);
                }
            });
        });

        observer.observe(subtitle);
    }

    /**
     * Efecto de brillo en títulos
     */
    setupTextGlow() {
        const titles = document.querySelectorAll('.brand-title, .apps-title');
        
        titles.forEach(title => {
            title.addEventListener('mouseenter', () => {
                title.style.textShadow = '0 0 20px rgba(255, 255, 255, 0.5), 2px 2px 4px rgba(0, 0, 0, 0.3)';
            });

            title.addEventListener('mouseleave', () => {
                title.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.3)';
            });
        });
    }
}

// Utilidades adicionales
class Utils {
    /**
     * Detecta si el usuario prefiere animaciones reducidas
     */
    static prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /**
     * Throttle function para optimizar performance
     */
    static throttle(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Detecta si es dispositivo táctil
     */
    static isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    // Solo inicializar si estamos en la página de inicio
    if (document.querySelector('.homepage-container')) {
        
        // Verificar si el usuario prefiere animaciones reducidas
        if (!Utils.prefersReducedMotion()) {
            new HomepageInteractions();
            new TextEffects();
        } else {
            // Versión simplificada sin animaciones
            console.log('Animaciones reducidas activadas');
            document.querySelectorAll('.brand-wrapper, .apps-title-wrapper, .app-button-large')
                .forEach(el => {
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                });
        }

        // Ajustes para dispositivos táctiles
        if (Utils.isTouchDevice()) {
            document.body.classList.add('touch-device');
        }
    }
});

// Añadir CSS para el efecto ripple
const rippleCSS = `
@keyframes ripple {
    to {
        transform: scale(2);
        opacity: 0;
    }
}

.button-hovered {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.touch-device .app-button-large:hover {
    transform: none !important;
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
`;

// Inyectar CSS
const style = document.createElement('style');
style.textContent = rippleCSS;
document.head.appendChild(style);

// Exportar para posible uso externo
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HomepageInteractions, TextEffects, Utils };
}
