import os
import tempfile
import unittest

import yaml
from image_assessment_service.core.services.task_service import Attribute, TaskSpec


class TestAttribute(unittest.TestCase):
    def test_attribute_creation(self):
        attr = Attribute(key="age", type="number", options=[])
        self.assertEqual(attr.key, "age")
        self.assertEqual(attr.type, "number")
        self.assertEqual(attr.options, [])

    def test_to_dict_with_options(self):
        attr = Attribute(key="gender", type="categorical", options=["Male", "Female"])
        expected = {
            "key": "gender",
            "type": "categorical",
            "options": ["Male", "Female"],
        }
        self.assertDictEqual(attr.to_dict(), expected)

    def test_to_dict_without_options(self):
        attr = Attribute(key="notes", type="text", options=[])
        expected = {"key": "notes", "type": "text"}
        self.assertDictEqual(attr.to_dict(), expected)

    def test_from_dict(self):
        data = {"key": "isActive", "type": "flag", "options": []}
        attr = Attribute.from_dict(data)
        self.assertEqual(attr.key, "isActive")
        self.assertEqual(attr.type, "flag")
        self.assertEqual(attr.options, [])


class TestTaskSpec(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "test_task.yaml")

        self.sample_attributes = [
            Attribute(key="age", type="number", options=[]),
            Attribute(key="gender", type="categorical", options=["Male", "Female"]),
        ]

        self.sample_task = TaskSpec(
            title=1,
            description="Test task",
            num_images=10,
            bbox_labels=["person", "car"],
            segmentation_labels=["road", "sidewalk"],
            image_labels=["outdoor", "daytime"],
            attributes=self.sample_attributes,
            image_names=["img1.jpg", "img2.jpg"],
            instructions="Do something",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_task_creation(self):
        self.assertEqual(self.sample_task.title, 1)
        self.assertEqual(len(self.sample_task.attributes), 2)
        self.assertEqual(self.sample_task.bbox_labels, ["person", "car"])

    def test_to_dict(self):
        task_dict = self.sample_task.to_dict()
        self.assertEqual(task_dict["title"], 1)
        self.assertEqual(len(task_dict["attributes"]), 2)
        self.assertIsInstance(task_dict["attributes"][0], dict)

    def test_yaml_roundtrip(self):
        # Сохраняем задачу в YAML
        self.sample_task.save_to_yaml(self.test_file)

        # Проверяем что файл создан
        self.assertTrue(os.path.exists(self.test_file))

        # Загружаем обратно
        loaded_task = TaskSpec.from_yaml(self.test_file)

        # Проверяем что данные совпадают
        self.assertEqual(loaded_task.title, self.sample_task.title)
        self.assertEqual(loaded_task.description, self.sample_task.description)
        self.assertEqual(len(loaded_task.attributes), len(self.sample_task.attributes))
        self.assertEqual(loaded_task.attributes[1].options, ["Male", "Female"])

    def test_from_dict_with_missing_fields(self):
        data = {
            "title": 2,
            "description": "Partial task",
            "num_images": 5,
            "instructions": "Do less",
        }
        task = TaskSpec.from_dict(data)
        self.assertEqual(task.title, 2)
        self.assertEqual(task.bbox_labels, [])
        self.assertEqual(task.attributes, [])

    def test_from_yaml_error_handling(self):
        # Тестируем обработку ошибок
        with self.assertRaises(FileNotFoundError):
            TaskSpec.from_yaml("nonexistent_file.yaml")

        # Создаем невалидный YAML
        with open(self.test_file, "w") as f:
            f.write("invalid: yaml: file: [")

        with self.assertRaises(yaml.YAMLError):
            TaskSpec.from_yaml(self.test_file)

        # Создаем YAML без обязательных полей
        with open(self.test_file, "w") as f:
            yaml.dump({"description": "Missing title"}, f)

        with self.assertRaises(ValueError):
            TaskSpec.from_yaml(self.test_file)

    def test_explicit_yaml_content(self):
        """Тестирует чтение явно заданного YAML-контента"""
        yaml_content = """\
title: 42
description: Тестовая задача с явным YAML
num_images: 3
bbox_labels: [dog, cat]
segmentation_labels: []
image_labels: [animal]
attributes:
- key: pet_type
  type: categorical
  options: [dog, cat, parrot]
- key: age
  type: number
image_names: [test1.jpg, test2.jpg]
instructions: Проаннотируйте животных на изображениях
"""

        # Записываем явный YAML во временный файл
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # Читаем и проверяем
        task = TaskSpec.from_yaml(self.test_file)

        # Основные проверки
        self.assertEqual(task.title, 42)
        self.assertEqual(task.description, "Тестовая задача с явным YAML")
        self.assertEqual(task.num_images, 3)

        # Проверка атрибутов
        self.assertEqual(len(task.attributes), 2)
        self.assertEqual(task.attributes[0].key, "pet_type")
        self.assertEqual(task.attributes[0].options, ["dog", "cat", "parrot"])
        self.assertEqual(task.attributes[1].type, "number")
        self.assertNotIn(
            "options", task.attributes[1].to_dict()
        )  # options пустой - не должен быть в dict

        # Проверка labels
        self.assertEqual(task.bbox_labels, ["dog", "cat"])
        self.assertEqual(task.segmentation_labels, [])
        self.assertEqual(task.image_labels, ["animal"])

        # Проверка имён файлов
        self.assertEqual(task.image_names, ["test1.jpg", "test2.jpg"])

    def test_yaml_output_format(self):
        """Тестирует точный формат выходного YAML файла"""
        expected_yaml = """\
title: 1
description: Test task
instructions: Do something
num_images: 10
bbox_labels:
- person
- car
segmentation_labels:
- road
- sidewalk
image_labels:
- outdoor
- daytime
attributes:
- key: age
  type: number
- key: gender
  type: categorical
  options:
  - Male
  - Female
image_names:
- img1.jpg
- img2.jpg
"""

        self.sample_task.save_to_yaml(self.test_file)

        with open(self.test_file, "r", encoding="utf-8") as f:
            actual_content = f.read()

        self.assertEqual(
            expected_yaml,
            actual_content,
            "Сгенерированный YAML не соответствует ожидаемому формату",
        )

        loaded_task = TaskSpec.from_yaml(self.test_file)
        self.assertEqual(loaded_task.title, 1)
        self.assertEqual(loaded_task.attributes[1].options, ["Male", "Female"])


if __name__ == "__main__":
    unittest.main()
