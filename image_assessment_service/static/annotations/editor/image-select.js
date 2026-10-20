export function createImageSelect() {
    const topPanelContent = document.getElementById('top-panel-content');

    topPanelContent.innerHTML = `
    <div class="image-navigator">
        <button class="nav-btn prev-btn" id="prev-image" title="Предыдущее изображение">
            <span>◄</span>
        </button>
        
        <div class="image-info">
            <select id="image-select" class="minimal-select">
                <!-- Опции будут заполнены скриптом -->
            </select>
        </div>
        
        <button class="nav-btn next-btn" id="next-image" title="Следующее изображение">
            <span>►</span>
        </button>
    </div>`;

    return {
        element: document.getElementById('image-select'),
        prevBtn: document.getElementById('prev-image'),
        nextBtn: document.getElementById('next-image')
    };
}
