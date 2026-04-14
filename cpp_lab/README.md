# BST vs AVL Lab (C++)

Этот каталог содержит полную C++ реализацию лабораторной работы:
- BST (обычное бинарное дерево поиска),
- AVL (самобалансирующееся дерево),
- стенд экспериментов по ТЗ,
- экспорт CSV и авто-отчёт,
- скрипт построения графиков.

## Структура
- `src/main.cpp` — реализации деревьев + бенчмарк.
- `scripts/plot_results.py` — построение графиков из `aggregated_results.csv`.
- `CMakeLists.txt` — сборка проекта.

## Сборка (Windows, PowerShell)

Требуется установленный C++ toolchain и CMake (например, Visual Studio Build Tools + CMake).

```powershell
Set-Location "c:\Users\saleh\OneDrive - НИТУ МИСиС\Desktop\Lab Work Lera\cpp_lab"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Или одной командой:

```powershell
.\build.ps1
```

## Полный запуск по ТЗ

```powershell
Set-Location "c:\Users\saleh\OneDrive - НИТУ МИСиС\Desktop\Lab Work Lera\cpp_lab"
.\build\Release\lab_benchmark.exe --series 10 --cycles 20 --random-cycles 10 --search-ops 1000 --delete-ops 1000 --min-exponent 10 --output-dir outputs
```

Или скриптом (запуск бенчмарка + графики):

```powershell
.\run_full.ps1
```

Если бинарник собран не в `Release`, путь может быть:
- `build\lab_benchmark.exe`.

## Построение графиков

```powershell
python scripts/plot_results.py --input outputs/aggregated_results.csv --plots-dir outputs/plots
```

## Результаты
После выполнения появляются:
- `outputs/raw_results.csv`
- `outputs/aggregated_results.csv`
- `outputs/REPORT.md`
- `outputs/plots/random_dataset.png`
- `outputs/plots/sorted_dataset.png`

## Быстрый проверочный запуск

```powershell
.\build\Release\lab_benchmark.exe --series 2 --cycles 2 --random-cycles 1 --search-ops 100 --delete-ops 100 --output-dir test_outputs
python scripts/plot_results.py --input test_outputs/aggregated_results.csv --plots-dir test_outputs/plots
```
