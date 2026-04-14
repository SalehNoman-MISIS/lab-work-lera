# Лабораторная работа: BST и AVL

В проекте реализованы:
- обычное бинарное дерево поиска (BST),
- самобалансирующееся AVL-дерево,
- скрипт для серии экспериментов по условиям задания,
- автоматическое построение графиков и генерация отчёта.

## Структура
- `src/trees.py` — реализации BST и AVL.
- `src/benchmark.py` — запуск экспериментов, сохранение CSV, построение графиков, генерация отчёта.
- `requirements.txt` — зависимости.

## Быстрый старт
1. Установите зависимости:

```powershell
python -m pip install -r requirements.txt
```

2. Запустите полный эксперимент (как в задании):

```powershell
python src/benchmark.py
```

Результаты появятся в папке `outputs`:
- `outputs/raw_results.csv`
- `outputs/aggregated_results.csv`
- `outputs/plots/random_dataset.png`
- `outputs/plots/sorted_dataset.png`
- `outputs/REPORT.md`

## Параметры запуска
Скрипт поддерживает настройку параметров:

```powershell
python src/benchmark.py --series 10 --cycles 20 --random-cycles 10 --search-ops 1000 --delete-ops 1000 --min-exponent 10 --seed 42 --output-dir outputs
```

Для быстрого smoke-теста:

```powershell
python src/benchmark.py --series 2 --cycles 2 --random-cycles 1 --search-ops 100 --delete-ops 100 --min-exponent 10 --output-dir demo_outputs
```

## Соответствие заданию
- 10 серий тестов: по умолчанию `--series 10`.
- 20 циклов в серии: по умолчанию `--cycles 20`.
- Первые 10 циклов — случайный массив: `--random-cycles 10`.
- Вторые 10 циклов — отсортированный массив.
- Размер массива: `2^(10 + i)`.
- Для каждого цикла:
  - замер вставки всего массива в BST и AVL,
  - 1000 поисков в BST и AVL + среднее время 1 поиска,
  - 1000 поисков в массиве (линейный поиск) + среднее время,
  - 1000 удалений в BST и AVL + среднее время 1 удаления.
- Раздельные графики для random/sorted и отдельная линия поиска по массиву.
