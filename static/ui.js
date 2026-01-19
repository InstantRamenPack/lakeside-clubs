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
let lastOverlayEventAt = 0;
let lastTooltipContent = '';

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
    if (lastTooltipContent !== content) {
        tooltipBubble.innerHTML = content;
        lastTooltipContent = content;
    }
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

function hasOverlays() {
    return Boolean(currentTooltipTarget || (warningLayer && warningLayer.childElementCount));
}

function scheduleOverlayUpdate() {
    lastOverlayEventAt = window.performance.now();
    if (!hasOverlays()) {
        return;
    }
    positionTooltip();
    positionWarnings();
    if (overlayUpdateHandle) {
        return;
    }
    const tick = () => {
        positionTooltip();
        positionWarnings();
        if (window.performance.now() - lastOverlayEventAt < 200) {
            overlayUpdateHandle = window.requestAnimationFrame(tick);
        } else {
            overlayUpdateHandle = null;
        }
    };
    overlayUpdateHandle = window.requestAnimationFrame(tick);
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

function updateButton(text, element, icon) {
    const button = element.tagName === 'BUTTON' ? element : element?.closest('button');
    button.querySelector('.button-label').textContent = text;
    if (icon !== undefined) {
        button.querySelector('.material-symbol').textContent = icon;
    }
}

function setupSearchBar() {
    const searchInput = document.getElementById('club-search');
    const searchResults = document.getElementById('search-results');
    const searchIcon = document.getElementById('search-icon');
    const overlay = document.getElementById('search-overlay');

    if (!searchInput || !searchResults || !searchIcon) {
        return;
    }

    const emptyHtml = '<div class="search-placeholder">Search to find new clubs!</div>';
    let debounceHandle;
    let blurHandle;
    let requestId = 0;
    let cachedResultsHtml = searchResults.innerHTML;
    let lastQuery = '';

    const setActive = (active) => {
        document.body.classList.toggle('search-active', active);
        searchResults.hidden = !active;
    };

    const updateIcon = () => {
        const hasText = searchInput.value.trim().length > 0;
        const focused = document.activeElement === searchInput;
        if (focused && hasText) {
            searchIcon.textContent = 'cancel';
            searchIcon.dataset.action = 'clear-search';
        } else {
            searchIcon.textContent = 'search';
            delete searchIcon.dataset.action;
        }
    };

    const renderEmpty = () => {
        searchResults.innerHTML = emptyHtml;
        cachedResultsHtml = searchResults.innerHTML;
    };

    const renderLoading = () => {
        searchResults.innerHTML = '<div class="search-loading"><span class="material-symbol spin">progress_activity</span></div>';
    };

    const scheduleSearch = () => {
        const query = searchInput.value.trim();
        window.clearTimeout(debounceHandle);
        debounceHandle = window.setTimeout(() => {
            if (!query) {
                requestId += 1;
                lastQuery = '';
                renderEmpty();
                return;
            }

            if (query === lastQuery && cachedResultsHtml && cachedResultsHtml !== emptyHtml) {
                return;
            }

            const currentId = ++requestId;
            const previousResults = cachedResultsHtml;
            renderLoading();

            fetch(`/search?query=${encodeURIComponent(query)}`)
                .then((response) => (response.ok ? response.json() : null))
                .then((payload) => {
                    if (currentId !== requestId || !payload) {
                        return;
                    }
                    const rendered = payload.rendered || [];
                    searchResults.innerHTML = rendered.join('');
                    cachedResultsHtml = searchResults.innerHTML;
                    lastQuery = query;
                })
                .catch(() => {
                    if (currentId !== requestId) {
                        return;
                    }
                    searchResults.innerHTML = previousResults || '';
                    cachedResultsHtml = searchResults.innerHTML;
                });
        }, 250);
    };

    searchInput.addEventListener('focus', () => {
        if (blurHandle) {
            window.clearTimeout(blurHandle);
        }
        setActive(true);
        updateIcon();
        if (!searchInput.value.trim()) {
            renderEmpty();
        } else if (searchInput.value.trim() !== lastQuery) {
            scheduleSearch();
        }
    });

    searchInput.addEventListener('blur', () => {
        updateIcon();
        blurHandle = window.setTimeout(() => {
            setActive(false);
            updateIcon();
        }, 150);
    });

    searchInput.addEventListener('input', () => {
        updateIcon();
        scheduleSearch();
    });

    searchResults.addEventListener('mousedown', () => {
        if (blurHandle) {
            window.clearTimeout(blurHandle);
        }
    });

    searchIcon.addEventListener('click', () => {
        if (searchIcon.dataset.action !== 'clear-search') {
            return;
        }
        requestId += 1;
        searchInput.value = '';
        renderEmpty();
        searchInput.focus();
        updateIcon();
    });

    if (overlay) {
        overlay.addEventListener('click', () => {
            searchInput.blur();
        });
    }

    renderEmpty();
    setActive(false);
    updateIcon();
}

// attach UI utilities
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea').forEach((textarea) => {
        textarea.addEventListener('input', () => autoGrow(textarea));
        autoGrow(textarea); // size for initial content
    });

    attachTooltips();
    setupTabs();
    setupSearchBar();

    window.addEventListener('scroll', scheduleOverlayUpdate, { passive: true, capture: true });
    window.addEventListener('resize', scheduleOverlayUpdate, { passive: true });
});
