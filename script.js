document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in effect to the container
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    
    // Ensure the page is visible when using browser navigation
    if (document.startViewTransition) {
        document.startViewTransition(() => {
            container.style.opacity = '1';
        });
    } else {
        requestAnimationFrame(() => {
            container.style.transition = 'opacity 0.5s ease-in-out';
            container.style.opacity = '1';
        });
    }

    // Add smooth transition for page navigation (excluding the directions button)
    document.querySelectorAll('a:not(.directions-button)').forEach(link => {
        link.addEventListener('click', function(e) {
            // Only handle internal navigation
            if (!this.hasAttribute('target')) {
                const href = this.getAttribute('href');
                
                // Don't prevent default on mobile devices
                if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))) {
                    e.preventDefault();
                    container.style.opacity = '0';
                    setTimeout(() => {
                        window.location.href = href;
                    }, 300);
                }
            }
        });
    });

    // Handle browser back/forward navigation
    window.addEventListener('popstate', () => {
        container.style.opacity = '1';
    });

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            container.style.opacity = '1';
        }
    });
});
