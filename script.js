document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in effect to the container
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    setTimeout(() => {
        container.style.transition = 'opacity 1s ease-in-out';
        container.style.opacity = '1';
    }, 100);

    // Add smooth transition for page navigation (excluding the directions button)
    document.querySelectorAll('a:not(.directions-button)').forEach(link => {
        link.addEventListener('click', function(e) {
            // Only prevent default for internal navigation
            if (!this.hasAttribute('target')) {
                e.preventDefault();
                const href = this.getAttribute('href');
                document.body.style.opacity = '0';
                setTimeout(() => {
                    window.location.href = href;
                }, 500);
            }
        });
    });
});
