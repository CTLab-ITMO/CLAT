const MIN_ANNOTATIONS_FOR_AGGREGATION = 2;

// Настраиваем кнопку удаления
document.startup = async function () {
    const footer = document.getElementById('action-footer');
    let button = document.createElement('button');
    button.id = 'delete-btn';
    button.className = 'btn-annotate btn-delete';
    button.textContent = `Удалить задание`;
    button.onclick = async function() {
        if (confirm('Вы уверены, что хотите УДАЛИТЬ ЗАДАНИЕ И ВСЕ РАЗМЕТКИ для него?')) {
            const response = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
            if (!response.ok) throw new Error('Ошибка удаления задания');

            window.location.href = `/profile`;
        }
    };
    footer.appendChild(button);
}

document.addEventListener('DOMContentLoaded', function() {
    const annotationsContainer = document.getElementById('annotations-container');
    const aggregateBtn = document.getElementById('aggregate-btn');
    const selectAllBtn = document.getElementById('select-all-btn');
    const iouThreshold = document.getElementById('iou-threshold');
    const overlapInput = document.getElementById('overlap');
    const loadingIndicator = document.getElementById('loading');

    var userId;
    (async function() {
        const response = await fetch("/api/admin/myid");
        userId = await response.json();
    })()
    
    let annotations = [];
    let selectedAnnotations = new Set();
    
    // Load annotations from API
    async function loadAnnotations() {
        try {
            const response = await fetch(`/api/tasks/${taskId}/annotations`);
            if (!response.ok) throw new Error('Failed to fetch annotations');
            
            annotations = await response.json();
            renderAnnotations();
        } catch (error) {
            console.error('Error loading annotations:', error);
            annotationsContainer.innerHTML = `<p class="error">Error loading annotations: ${error.message}</p>`;
        }
    }

    async function deleteAnnotation(annotationId) {
        if (confirm('Вы уверены, что хотите удалить разметку?')) {
            const response = await fetch(`/api/annotations/${annotationId}`, {method: 'DELETE'});
            if (!response.ok) throw new Error('Ошибка удаления разметки');
            loadAnnotations()
        }
    }
    
    // Render annotations to the DOM
    function renderAnnotations() {
        annotationsContainer.innerHTML = '';
        
        if (annotations.length === 0) {
            annotationsContainer.innerHTML = '<p>No annotations found</p>';
            return;
        }
        
        annotations.forEach(annotation => {
            const card = document.createElement('div');
            card.className = `annotation-card ${selectedAnnotations.has(annotation.id) ? 'selected' : ''}`;
            
            const statusClass = getStatusClass(annotation.status);
            
            card.innerHTML = `
                <div class="checkbox-container">
                    <input type="checkbox" ${selectedAnnotations.has(annotation.id) ? 'checked' : ''} 
                            data-id="${annotation.id}">
                </div>
                <div class="annotation-id">ID: ${annotation.id}</div>
                <div class="annotation-description">${annotation.description || 'Без описания'}</div>
                <div class="annotation-user">
                    userId: ${annotation.user.id} ${annotation.user.id == userId ? "<b>(ВЫ)</b>" : ""}<br>
                    nickname: ${annotation.user.nickname} <br>
                    email: ${annotation.user.email} <br>
                </div>
                <br><hr>
                <div class="annotation-meta">
                    <div>
                        <span>${formatDate(annotation.created_at)}</span>
                        ${annotation.deadline ? `<br><span>Дедлайн: ${formatDate(annotation.deadline)}</span>` : ''}
                    </div>
                    <span class="status-badge ${statusClass}">${annotation.status}</span>
                </div>
                
                <div class="annotation-actions">
                    <button class="view-markup-btn" onclick="event.stopPropagation(); window.location.href ='/annotations/${annotation.id}'">
                        Посмотреть разметку
                    </button>
                    ${annotation.has_scores ? `<button class="view-markup-btn" onclick="event.stopPropagation(); window.location.href ='/annotations/${annotation.id}/scores'">
                        Оценки
                    </button>` : ""}
                    <button class="delete-markup-btn" data-id="${annotation.id}">
                        Удалить
                    </button>
                </div>
            `;
            
            // Add click handler for the entire card
            card.addEventListener('click', function(e) {
                // Don't toggle if checkbox was clicked (it has its own handler)
                if (e.target.tagName === 'INPUT') return;
                
                const checkbox = this.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
                toggleAnnotationSelection(checkbox);
            });
            
            // Add change handler for the checkbox
            const checkbox = card.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', function() {
                toggleAnnotationSelection(this);
            });

            const deleteBtn = card.querySelector('.delete-markup-btn');
            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await deleteAnnotation(annotation.id);
            });
            
            annotationsContainer.appendChild(card);
        });
        
        updateAggregateButton();
    }
    
    // Toggle annotation selection
    function toggleAnnotationSelection(checkbox) {
        const annotationId = parseInt(checkbox.dataset.id);
        
        if (checkbox.checked) {
            selectedAnnotations.add(annotationId);
            checkbox.closest('.annotation-card').classList.add('selected');
        } else {
            selectedAnnotations.delete(annotationId);
            checkbox.closest('.annotation-card').classList.remove('selected');
        }
        
        updateAggregateButton();
        updateSelectAllButton();
    }
    
    // Update aggregate button state
    function updateAggregateButton() {
        aggregateBtn.disabled = selectedAnnotations.size < MIN_ANNOTATIONS_FOR_AGGREGATION;
    }
    
    // Format date for display
    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    // Get CSS class for status badge
    function getStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'completed': return 'status-completed';
            case 'pending': return 'status-pending';
            case 'rejected': return 'status-rejected';
            default: return '';
        }
    }

    function updateSelectAllButton() {
        selectAllBtn.textContent = (selectedAnnotations.size === annotations.length)
            ? 'Снять выделение' : 'Выбрать все';
        
    }

    selectAllBtn.addEventListener('click', async function() {
        const checkboxes = document.querySelectorAll('.annotation-card input[type="checkbox"]');

        const hasUnchecked = Array.from(checkboxes).some(checkbox => !checkbox.checked);

        checkboxes.forEach(checkbox => {
            checkbox.checked = hasUnchecked;
            // Триггерим событие change, чтобы обновить selectedAnnotations
            const event = new Event('change');
            checkbox.dispatchEvent(event);
        });
    })
    
    // Handle aggregation
    aggregateBtn.addEventListener('click', async function() {
        if (selectedAnnotations.size < MIN_ANNOTATIONS_FOR_AGGREGATION) return;
        
        const params = {
            annotation_ids: Array.from(selectedAnnotations),
            threshold_iou: parseFloat(iouThreshold.value),
            min_overlap: parseInt(overlapInput.value)
        };

        try {
            loadingIndicator.style.display = 'block';
            
            const response = await fetch('/api/annotations/aggregate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            if (!response.ok) throw new Error('Aggregation failed');
            
            // Clear selection and reload annotations
            selectedAnnotations.clear();
            await loadAnnotations();
        } catch (error) {
            console.error('Aggregation error:', error);
            alert(`Aggregation failed: ${error.message}`);
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });
    
    // Initial load
    loadAnnotations();
});