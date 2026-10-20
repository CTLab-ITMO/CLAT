export function createObjectsListItem(annotationObject, isEditable = true, annotationObjectsManager, availableLabels, availableAttributes) {
    
    const item = document.createElement('div');
    item.className = 'annotation-item';
    item.dataset.id = annotationObject.id;
    
    const labelSelect = createLabelSelect(annotationObject, availableLabels, isEditable, annotationObjectsManager);
    const deleteButton = isEditable ? createDeleteButton() : null;
    const header = createHeader(annotationObject, labelSelect, deleteButton);
    const attrsContainer = createAttributesContainer(annotationObject, availableAttributes, isEditable);
    
    const toggleBtn = header.querySelector('.annotation-toggle-attrs');
    toggleBtn.addEventListener('click', () => {
        attrsContainer.classList.toggle('expanded');
        toggleBtn.innerHTML = attrsContainer.classList.contains('expanded') ? '▲' : '▼';
    });

    deleteButton?.addEventListener('click', () => annotationObjectsManager.remove(annotationObject.id));

    item.append(header, attrsContainer);
    return item;
}

function createLabelSelect(annotationObject, availableLabels, isEditable, annotationObjectsManager) {
    const select = document.createElement('select');
    select.className = 'annotation-label-select';
    select.disabled = !isEditable;
    
    availableLabels.forEach(label => {
        const option = document.createElement('option');
        option.value = label;
        option.textContent = label;
        option.selected = label === annotationObject.label;
        select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
        annotationObject.label = select.value;
        annotationObjectsManager.update(annotationObject.id);
    });
    
    return select;
}

function createDeleteButton() {
    const button = document.createElement('button');
    button.className = 'annotation-delete-btn';
    button.innerHTML = '&times;';
    button.title = 'Удалить аннотацию';
    return button;
}

function createHeader(annotationObject, labelSelect, deleteButton) {
    const header = document.createElement('div');
    header.className = 'annotation-header';
    
    const typeBadge = document.createElement('span');
    typeBadge.className = 'annotation-type-badge';
    typeBadge.textContent = annotationObject.type;
    
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'annotation-toggle-attrs';
    toggleBtn.innerHTML = '▼';
    toggleBtn.title = 'Показать/скрыть атрибуты';
    
    header.append(labelSelect, typeBadge, toggleBtn);
    if (deleteButton) header.append(deleteButton);
    
    return header;
}

function createAttributesContainer(annotationObject, availableAttributes, isEditable) {
    const container = document.createElement('div');
    container.className = 'annotation-attributes';

    // Добавляем существующие атрибуты
    Object.entries(annotationObject.attributes || {}).forEach(([key, value]) => {
        const attr = createAttributeRow(annotationObject, key, value, availableAttributes[key], isEditable, container, availableAttributes);
        container.appendChild(attr);
    });

    if (isEditable) {
        const addAttrWrapper = document.createElement('div');
        addAttrWrapper.className = 'add-attribute-wrapper';

        const attrSelect = document.createElement('select');
        attrSelect.className = 'attribute-select';
        
        updateAttrSelect(attrSelect, annotationObject, availableAttributes);

        const addButton = document.createElement('button');
        addButton.className = 'add-attribute-btn';
        addButton.textContent = '+ Добавить';
        addButton.disabled = attrSelect.options.length === 0;

        attrSelect.addEventListener('change', () => {
            addButton.disabled = attrSelect.value === '';
        });

        addButton.addEventListener('click', () => {
            const selectedKey = attrSelect.value;
            if (selectedKey) {
                const attrInfo = availableAttributes[selectedKey];
                let defaultValue = false; // flag
                if (attrInfo.type === 'text') {
                    defaultValue = '';
                } else if (attrInfo.type === 'number') {
                    defaultValue = 0;
                } else if (attrInfo.type === 'select') {
                    defaultValue = attrInfo.options[0];
                }
                const attr = createAttributeRow(annotationObject, selectedKey, defaultValue, attrInfo, true, container, availableAttributes);
                container.insertBefore(attr, addAttrWrapper);

                // Обновляем список доступных атрибутов
                updateAttrSelect(attrSelect, annotationObject, availableAttributes);
                addButton.disabled = attrSelect.options.length === 0;
            }
        });

        addAttrWrapper.append(attrSelect, addButton);
        container.appendChild(addAttrWrapper);
    }

    return container;
}

function updateAttrSelect(attrSelect, annotationObject, availableAttributes) {
    // Очищаем текущий список
    attrSelect.innerHTML = '';
    
    // Добавляем доступные атрибуты
    Object.entries(availableAttributes).forEach(([key, attrInfo]) => {
        if (!annotationObject.attributes || !annotationObject.attributes.hasOwnProperty(key)) {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `${key} (${attrInfo.type})`;
            option.dataset.type = attrInfo.type;
            attrSelect.appendChild(option);
        }
    });
}

function createAttributeRow(annotationObject, key, value, attrInfo, isEditable, container, availableAttributes) {
    const row = document.createElement('div');
    row.className = 'annotation-attribute';

    const keyWrapper = document.createElement('div');
    keyWrapper.className = 'attribute-key-wrapper';
    
    const keySpan = document.createElement('span');
    keySpan.className = 'attribute-key';
    keySpan.textContent = key;
    keyWrapper.appendChild(keySpan);

    const valueInput = createAttributeInput(key, value, attrInfo, isEditable);
    valueInput.className = 'attribute-value-input';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'attribute-delete-btn';
    deleteBtn.innerHTML = '&minus;';
    deleteBtn.title = 'Удалить атрибут';
    deleteBtn.disabled = !isEditable;

    row.append(keyWrapper, deleteBtn, valueInput);

    const updateAttribute = (vi) => {
        if (attrInfo?.type === 'flag') {
            annotationObject.attributes[key] = vi.checked;
        } else {
            annotationObject.attributes[key] = vi.value;
        }
    } 
    valueInput.addEventListener('change', () => updateAttribute(valueInput));
    updateAttribute(valueInput);

    deleteBtn.addEventListener('click', () => {
        delete annotationObject.attributes[key];
        row.remove();
        
        // Находим select для добавления атрибутов и обновляем его
        const attrSelect = container.querySelector('.attribute-select');
        if (attrSelect) {
            updateAttrSelect(attrSelect, annotationObject, availableAttributes);
            
            // Активируем кнопку добавления, если есть доступные атрибуты
            const addButton = container.querySelector('.add-attribute-btn');
            if (addButton) {
                addButton.disabled = attrSelect.options.length === 0;
            }
        }
    });

    return row;
}

function createAttributeInput(key, value, attrInfo, isEditable) {
    if (!attrInfo || attrInfo.type === 'flag') {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = value;
        checkbox.disabled = !isEditable;
        return checkbox;
    }
    
    if (attrInfo.type === 'number') {
        const input = document.createElement('input');
        input.type = 'number';
        input.value = value;
        input.disabled = !isEditable;
        return input;
    }
    
    if (attrInfo.type === 'categorical' && attrInfo.options) {
        const select = document.createElement('select'); 
        select.disabled = !isEditable;
        
        attrInfo.options.forEach((option, index) => {
            const optElem = document.createElement('option');
            optElem.value = option;
            optElem.textContent = option;
            optElem.selected = option === value;
            select.appendChild(optElem);
        });
        
        return select;
    }
    
    const input = document.createElement('input');
    input.type = 'text';
    input.value = value;
    input.disabled = !isEditable;
    return input;
}
