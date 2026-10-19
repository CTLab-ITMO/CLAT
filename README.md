## Запуск в docker

Перед запуском необходимо создать и настроить:
- `.env` (пример в `example.env`)
- Конфиг `resources/configs/docker-config.yaml` (пути фич резолвятся от `storages.default.path`, который в контейнере = `/app/data`)
- Настроить папку с данными, которые надо разметить (`DATA_VOLUME_PATH` в `.env`): 

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

После настройки `.env` и `resources/configs/docker-config.yaml`, запустить docker:
```bash
docker compose up --build
```
После успешного запуска, приложение будет доступно по ссылке `http://127.0.0.1:3333/assess/main/` 

## Запуск без docker
- Запустить postgres и создать базу данных
- Установить переменную окружения POSTGRES_PASSWORD
- Добавить репозиторий в PYTHONPATH
- Настроить `resources/configs/local.yaml`
- Запустить image_assessment_service/cli.py


```bash
export POSTGRES_PASSWORD=mypassword
export PYTHONPATH="${PYTHONPATH}:path/to/light-data-assessment"
python image_assessment_service/cli.py --config resources/configs/local.yaml
```

## Тесты
```bash
export PYTHONPATH="${PYTHONPATH}:path/to/light-data-assessment"
pytest --cov=image_assessment_service --cov-config=.coveragerc
```