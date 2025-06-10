from fastapi import HTTPException

image_name_forbidden_symbols = {'/', '\\', ':', '*', '?', '"', '<', '>', '|'}

def validate_image_name(name: str):
    if not name:
        raise HTTPException(400, "Имя изображения не может быть пустым")
    
    if len(name) > 255:
        raise HTTPException(400, "Слишком длинное имя изображения (макс. 255 символов)")
    
    if set(name).intersection(image_name_forbidden_symbols):
        raise HTTPException(400, f"Некорректное имя изображения: {name}")