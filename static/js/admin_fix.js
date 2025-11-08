// === Corrige o link "Encerrar sessão" que o Django estiliza inline ===
document.addEventListener("DOMContentLoaded", function () {
    const logoutLink = document.querySelector('#user-tools a[href*="logout"]');
    if (logoutLink) {
        logoutLink.style.color = "#0b5394";        // Azul escuro OdontoIA
        logoutLink.style.fontWeight = "600";
        logoutLink.style.textDecoration = "none";

        logoutLink.addEventListener("mouseover", function () {
            logoutLink.style.color = "#063769";    // Azul mais forte no hover
            logoutLink.style.textDecoration = "underline";
        });
        logoutLink.addEventListener("mouseout", function () {
            logoutLink.style.color = "#0b5394";
            logoutLink.style.textDecoration = "none";
        });
    }

    // Também ajusta todos os outros links do topo
    const userLinks = document.querySelectorAll("#user-tools a, #user-tools strong, #user-tools span");
    userLinks.forEach(link => {
        link.style.color = "#0b5394";
        link.style.fontWeight = "600";
        link.style.textShadow = "none";
    });
});
