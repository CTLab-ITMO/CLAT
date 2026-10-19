export async function setLabelsElements(toolName, task, selectAction) {
    const labelsList = document.getElementById('labels-list');

    let labels = [];
    if (toolName == 'bbox') {
        labels = task.bbox_labels;
    } else if (toolName == 'segment') {
        labels = task.segmentation_labels;
    } else {
        labelsList.innerHTML = '';
        return;
    }
    
    labelsList.innerHTML = labels.map(label => `
        <button class="tool-label-btn label-btn" data-label="${label}">${label}</button>
    `).join('');

    document.querySelectorAll('.label-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.label-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectAction(btn.dataset.label);
        });
    });

    const firstLabelBtn = document.querySelectorAll('.label-btn')[0];
    firstLabelBtn.classList.add('active');
    selectAction(firstLabelBtn.dataset.label);
}