// textarea autogrow on input
function autoGrow(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}

// move tooltips to top-level of DOM to ensure visible on top
// tooltips and warnings are ChatGPT generated
let tooltipLayer;
let tooltipBubble;
let tooltipObserver;
let currentTooltipTarget;
let warningLayer;
let overlayUpdateHandle;

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
            currentTooltipTarget = element;
            positionTooltip();
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

function positionTooltip() {
    if (!tooltipBubble || !currentTooltipTarget) {
        return;
    }
    if (!currentTooltipTarget.isConnected) {
        tooltipBubble.style.visibility = 'hidden';
        currentTooltipTarget = null;
        return;
    }
    const content = currentTooltipTarget.dataset.tooltip || '';
    if (!content) {
        tooltipBubble.style.visibility = 'hidden';
        currentTooltipTarget = null;
        return;
    }
    const rect = currentTooltipTarget.getBoundingClientRect();
    tooltipBubble.innerHTML = content;
    tooltipBubble.style.left = `${rect.left + rect.width / 2}px`;
    tooltipBubble.style.top = `${rect.top}px`;
}

function createWarningLayer() {
    if (warningLayer) {
        return warningLayer;
    }
    warningLayer = document.createElement('div');
    warningLayer.className = 'warning-layer';
    document.body.appendChild(warningLayer);
    return warningLayer;
}

function attachWarnings(scope) {
    const layer = createWarningLayer();
    layer.replaceChildren();
    const targets = Array.from((scope || document).querySelectorAll('[data-warning]'));
    targets.forEach((element) => {
        const content = element.dataset.warning || '';
        if (!content) {
            return;
        }
        const bubble = document.createElement('span');
        bubble.className = 'warning-text';
        bubble.textContent = content;
        bubble._target = element;
        layer.appendChild(bubble);
        positionWarning(bubble, element);
    });
}

function clearWarnings(scope) {
    const target = scope || document;
    target.querySelectorAll('[data-warning]').forEach((element) => {
        delete element.dataset.warning;
    });
    if (warningLayer) {
        warningLayer.replaceChildren();
    }
}

function positionWarning(bubble, element) {
    if (!bubble || !element) {
        return;
    }
    const rect = element.getBoundingClientRect();
    bubble.style.left = `${rect.left + rect.width / 2}px`;
    bubble.style.top = `${rect.top}px`;
}

function positionWarnings() {
    if (!warningLayer) {
        return;
    }
    warningLayer.querySelectorAll('.warning-text').forEach((bubble) => {
        const target = bubble._target;
        if (!target || !target.isConnected) {
            bubble.remove();
            return;
        }
        const content = target.dataset.warning || '';
        if (!content) {
            bubble.remove();
            return;
        }
        if (bubble.textContent !== content) {
            bubble.textContent = content;
        }
        positionWarning(bubble, target);
    });
}

function scheduleOverlayUpdate() {
    if (overlayUpdateHandle) {
        return;
    }
    overlayUpdateHandle = window.requestAnimationFrame(() => {
        overlayUpdateHandle = null;
        positionTooltip();
        positionWarnings();
    });
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

    window.addEventListener('scroll', scheduleOverlayUpdate, { passive: true, capture: true });
    window.addEventListener('resize', scheduleOverlayUpdate, { passive: true });
});
