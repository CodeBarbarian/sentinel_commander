document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', function (e) {
        // Ignore if focused on input/textarea or contenteditable
        if (["INPUT", "TEXTAREA"].includes(e.target.tagName) || e.target.isContentEditable) return;

        switch (e.key.toLowerCase()) {
            case 'd':
                if (e.shiftKey) {
                    window.location.href = "/web/v1/dashboard";
                }
                break;
            case 'a':
                if (e.shiftKey) {
                    window.location.href = "/web/v1/alerts";
                }
                break;
            case 'c':
                if (e.shiftKey) {
                    window.location.href = "/web/v1/cases";
                }
                break;
            case '/':
                if (e.shiftKey) {
                    e.preventDefault();
                    const search = document.getElementById("global-search");
                    if (search) search.focus();
                }
                break;
            case '?':
                if (e.shiftKey) {
                    const modal = new bootstrap.Modal(document.getElementById('shortcutsModal'));
                    modal.show();
                }
                break;
            case 'escape':
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    bootstrap.Modal.getInstance(openModal).hide();
                }
                break;
        }
    });
});
