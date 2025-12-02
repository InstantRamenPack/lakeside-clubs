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

    document.querySelectorAll('.tooltip').forEach((tooltip) => {
        const text = tooltip.querySelector('.tooltip-text');
        if (!text) {
            return;
        }

        const show = () => {
            const rect = tooltip.getBoundingClientRect();
            bubble.innerHTML = text.innerHTML;
            bubble.style.left = `${rect.left + rect.width / 2}px`;
            bubble.style.top = `${rect.top}px`;
            bubble.style.visibility = 'visible';
        };

        tooltip.addEventListener('mouseenter', show);
        tooltip.addEventListener('focusin', show);
        tooltip.addEventListener('mouseleave', hide);
        tooltip.addEventListener('focusout', hide);
    });
}

// attach UI utilities
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea').forEach((textarea) => {
        textarea.addEventListener('input', () => autoGrow(textarea));
        autoGrow(textarea); // size for initial content
    });

    attachTooltips();
});
