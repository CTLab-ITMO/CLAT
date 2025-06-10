## Запуск в docker

Перед запуском необходимо создать и настроить:
- .env (пример: example.env)
- Создать и настроить под себя config.yaml (пример - example.config.yaml) . Есть  image_assessment_service/resources/config.yaml - его трогать не нужно
- Настроить папку с данными, которые надо разметить (DATA_VOLUME_PATH в .ENV): 

```fish
 need_assess/
  │
  ├── folder_1/                   
  │   ├── some_img1.ext     
  │   ├── some_img2.ext  
  │  ...
  │   └── last_img.ext
 ... 
  └── folder_n/ 
      ├── some_img1.ext  
      ├── some_img2.ext                       
     ...
      └── last_img.ext
```

После настройки .env и image_assessment_service/resources/config.yaml, запустить docker
```bash
docker composec up -d
```

## Запуск без docker
- Запустить postgres и создать базу данных
- Установить переменную окружения POSTGRES_PASSWORD
- Добавить репозиторий в PYTHONPATH
- Настроить local.config.yaml (пример - example.local.config.yaml)
- Запустить image_assessment_service/cli.py


```bash
export POSTGRES_PASSWORD=mypassword
export PYTHONPATH="${PYTHONPATH}:path/to/light-data-assessment"
python image_assessment_service/cli.py --config local.config.yaml
```

## Тесты
```bash
export PYTHONPATH="${PYTHONPATH}:path/to/light-data-assessment"
pytest --cov=image_assessment_service --cov-config=.coveragerc
```