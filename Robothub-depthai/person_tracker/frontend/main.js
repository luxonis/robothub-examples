window.addEventListener("DOMContentLoaded", alwaysShiftLogoFromSidebar);

function alwaysShiftLogoFromSidebar() {
  const sidebar = document
    .querySelector(".numbers")
    .shadowRoot.querySelector(".rh-tile-wrapper");

  const logo = document
    .querySelector("rh-promo-bar")
    .shadowRoot.querySelector(".rh-promo-bar")
    .shadowRoot.querySelector(".rh-bar")
    .querySelector("slot")
    .assignedElements()
    .find((it) => it.classList.contains("rh-promo-logo"));

  new ResizeObserver(
    () => (logo.style.marginRight = `${sidebar.offsetWidth}px`)
  ).observe(sidebar);
}
