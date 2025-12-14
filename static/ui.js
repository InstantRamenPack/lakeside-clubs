// textarea autogrow on input
function autoGrow(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}

// move tooltips to top-level of DOM to ensure visible on top
// ChatGPT generated
let tooltipLayer;
let tooltipBubble;

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
    };

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
            bubble.innerHTML = content;
            bubble.style.left = `${rect.left + rect.width / 2}px`;
            bubble.style.top = `${rect.top}px`;
            bubble.style.visibility = 'visible';
        };

        element.addEventListener('mouseenter', show);
        element.addEventListener('focusin', show);
        element.addEventListener('mouseleave', hide);
        element.addEventListener('focusout', hide);
    });
}

function updateTooltip(text, element) {
    element.dataset.tooltip = text;
    if (element.matches(':hover')) {
        element.dispatchEvent(new Event('mouseenter'));
    }
}

// attach UI utilities
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea').forEach((textarea) => {
        textarea.addEventListener('input', () => autoGrow(textarea));
        autoGrow(textarea); // size for initial content
    });

    attachTooltips();
});
