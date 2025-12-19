// textarea autogrow on input
function autoGrow(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}

// move tooltips to top-level of DOM to ensure visible on top
// tooltips are ChatGPT generated
let tooltipLayer;
let tooltipBubble;
let tooltipObserver;
let currentTooltipTarget;

function createTooltipLayer() {
    if (tooltipBubble) {
        return tooltipBubble;
    }
    tooltipLayer = document.createElement('div');
    tooltipLayer.className = 'tooltip-layer';
    tooltipBubble = document.createElement('span');
    tooltipBubble.className = 'tooltip-text';
    tooltipBubble.style.visibility = 'hidden';
    tooltipLayer.appendChild(tooltipBubble);
    document.body.appendChild(tooltipLayer);
    return tooltipBubble;
}

function attachTooltips() {
    const bubble = createTooltipLayer();

    const hide = () => {
        bubble.style.visibility = 'hidden';
        currentTooltipTarget = null;
    };

    if (!tooltipObserver) {
        tooltipObserver = new MutationObserver((mutations) => {
            if (!currentTooltipTarget) {
                return;
            }
            mutations.forEach((mutation) => {
                mutation.removedNodes.forEach((node) => {
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        return;
                    }
                    if (node === currentTooltipTarget || node.contains(currentTooltipTarget)) {
                        hide();
                    }
                });
            });
        });
        tooltipObserver.observe(document.body, { childList: true, subtree: true });
    }

    document.querySelectorAll('[data-tooltip]').forEach((element) => {
        if (element.dataset.tooltipBound) {
            return;
        }
        element.dataset.tooltipBound = 'true';

        const show = () => {
            const content = element.dataset.tooltip || '';
            if (!content) {
                hide();
                return;
            }
            const rect = element.getBoundingClientRect();
            currentTooltipTarget = element;
            bubble.innerHTML = content;
            bubble.style.left = `${rect.left + rect.width / 2}px`;
            bubble.style.top = `${rect.top}px`;
            bubble.style.visibility = 'visible';
        };

        element.addEventListener('mouseenter', show);
        element.addEventListener('focusin', show);
        element.addEventListener('mouseleave', hide);
        element.addEventListener('focusout', hide);
        element.addEventListener('click', hide);
    });
}

function updateTooltip(text, element) {
    element.dataset.tooltip = text;
    if (element.matches(':hover')) {
        element.dispatchEvent(new Event('mouseenter'));
    }
}

function wrapButtons() {
    const targets = Array.from(document.querySelectorAll('[data-button]'));
    targets.forEach((element) => {
        const parentButton = element.parentElement;
        if (parentButton.tagName === 'BUTTON') {
            parentButton.replaceWith(element);
        }

        const button = document.createElement('button');
        button.type = 'button';

        Object.entries(element.dataset).forEach(([key, value]) => {
            if (key !== 'button') {
                button.dataset[key] = value;
            }
        });

        const label = document.createElement('span');
        label.textContent = element.getAttribute('data-button');
        element.parentNode.replaceChild(button, element);
        button.appendChild(label);
        button.appendChild(element);
    });
}

function updateButton(text, element, icon) {
    if (element.tagName === 'BUTTON') {
        element = element.querySelector('[data-button]');
    }
    element.dataset.button = text;
    if (icon !== undefined) {
        element.textContent = icon;
    }

    wrapButtons();
}

// roughly adapted from https://www.w3schools.com/howto/howto_js_tabs.asp
function setActiveTab(tabBar, targetId) {
    const tabs = Array.from(tabBar.querySelectorAll('[data-tab-target]'));
    tabs.forEach((tab) => {
        const isActive = tab.dataset.tabTarget === targetId;
        tab.classList.toggle('is-active', isActive);
        const panel = document.getElementById(tab.dataset.tabTarget);
        panel.hidden = !isActive;
    });
}

function setupTabs() {
    document.querySelectorAll('.tab-bar').forEach((tabBar) => {
        const tabs = Array.from(tabBar.querySelectorAll('[data-tab-target]'));
        const activeTab = tabBar.querySelector('.tab-button.is-active');
        setActiveTab(tabBar, activeTab.dataset.tabTarget);
        tabs.forEach((tab) => {
            tab.addEventListener('click', () => setActiveTab(tabBar, tab.dataset.tabTarget));
        });
    });
}

// attach UI utilities
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea').forEach((textarea) => {
        textarea.addEventListener('input', () => autoGrow(textarea));
        autoGrow(textarea); // size for initial content
    });

    attachTooltips();
    wrapButtons();
    setupTabs();
});
