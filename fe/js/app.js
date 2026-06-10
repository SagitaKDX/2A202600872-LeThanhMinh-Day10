// Core Application Router & Coordinator
document.addEventListener("DOMContentLoaded", () => {
    // Route mapping
    const routes = {
        "#chat": {
            template: "components/chat.html",
            title: "RAG Chatbot",
            navId: "nav-chat",
            init: initChat
        },
        "#observability": {
            template: "components/observability.html",
            title: "Observability",
            navId: "nav-observability",
            init: initObservability
        },
        "#corruption": {
            template: "components/corruption.html",
            title: "Data Reliability",
            navId: "nav-corruption",
            init: initCorruption
        }
    };

    const appContent = document.getElementById("app-content");
    const viewTitle = document.getElementById("view-title");

    // Dynamic Route Switcher
    async function loadView() {
        const hash = window.location.hash || "#chat";
        const route = routes[hash];
        
        if (!route) {
            window.location.hash = "#chat";
            return;
        }

        // 1. Update Navigation Links Active States
        document.querySelectorAll(".menu-item").forEach(item => item.classList.remove("active"));
        const activeNav = document.getElementById(route.navId);
        if (activeNav) activeNav.classList.add("active");

        // 2. Set view header title
        viewTitle.innerText = route.title;

        // 3. Render Loading Spinner
        appContent.innerHTML = `
            <div class="loading-spinner">
                <i class="fa-solid fa-circle-notch fa-spin"></i>
                <span>Loading ${route.title.toLowerCase()} view...</span>
            </div>
        `;

        // 4. Fetch and Inject HTML Component Template
        try {
            const response = await fetch(route.template);
            if (!response.ok) throw new Error(`Could not load view template: ${route.template}`);
            const html = await response.text();
            appContent.innerHTML = html;
            
            // 5. Initialize Page Controller
            if (route.init) route.init();
        } catch (error) {
            appContent.innerHTML = `
                <div class="loading-spinner">
                    <i class="fa-solid fa-circle-exclamation" style="color: var(--warning);"></i>
                    <span>Error loading page: ${error.message}</span>
                </div>
            `;
        }
    }

    // Router Listeners
    window.addEventListener("hashchange", loadView);
    
    // Initial Routing Load
    loadView();

    // Periodically poll pipeline status to update status badge globally
    pollPipelineStatusGlobal();
    setInterval(pollPipelineStatusGlobal, 5000);
});

// Global Pipeline Status Badge Updater
async function pollPipelineStatusGlobal() {
    const indicator = document.getElementById("pipeline-indicator");
    if (!indicator) return;

    try {
        const [resBase, resCorr] = await Promise.all([
            fetch("/api/observability/status"),
            fetch("/api/corruption/status")
        ]);
        const dataBase = await resBase.json();
        const dataCorr = await resCorr.json();
        
        if (dataBase.pipeline_running || dataCorr.corruption_running) {
            indicator.className = "status-indicator running";
            indicator.innerHTML = `<i class="fa-solid fa-arrows-rotate fa-spin"></i> Pipeline Running...`;
        } else {
            indicator.className = "status-indicator fresh";
            indicator.innerHTML = `<i class="fa-solid fa-circle-check"></i> Pipeline Normal`;
        }
    } catch (e) {
        console.error("Error polling global pipeline status:", e);
    }
}
