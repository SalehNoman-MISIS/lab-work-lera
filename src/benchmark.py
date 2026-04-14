from __future__ import annotations

import argparse
import csv
import random
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable

import matplotlib.pyplot as plt

from trees import AVLTree, BinarySearchTree


@dataclass(frozen=True)
class BenchmarkConfig:
    series_count: int = 10
    cycles_per_series: int = 20
    random_cycles: int = 10
    search_ops: int = 1000
    delete_ops: int = 1000
    min_exponent: int = 10
    seed: int = 42


@dataclass
class CycleResult:
    series_index: int
    n: int
    data_mode: str
    cycle_index: int
    bst_insert_total_s: float
    bst_search_total_s: float
    bst_search_per_op_s: float
    bst_delete_total_s: float
    bst_delete_per_op_s: float
    avl_insert_total_s: float
    avl_search_total_s: float
    avl_search_per_op_s: float
    avl_delete_total_s: float
    avl_delete_per_op_s: float
    array_search_total_s: float
    array_search_per_op_s: float


def linear_search(values: list[int], target: int) -> bool:
    for item in values:
        if item == target:
            return True
    return False


def measure_total(func: Callable[[], None]) -> float:
    start = time.perf_counter()
    func()
    end = time.perf_counter()
    return end - start


def batch_insert_bst(tree: BinarySearchTree, values: list[int]) -> None:
    for v in values:
        tree.insert(v)


def batch_insert_avl(tree: AVLTree, values: list[int]) -> None:
    for v in values:
        tree.insert(v)


def batch_search_bst(tree: BinarySearchTree, targets: list[int]) -> None:
    for x in targets:
        tree.search(x)


def batch_search_avl(tree: AVLTree, targets: list[int]) -> None:
    for x in targets:
        tree.search(x)


def batch_search_array(values: list[int], targets: list[int]) -> None:
    for x in targets:
        linear_search(values, x)


def batch_delete_bst(tree: BinarySearchTree, targets: list[int]) -> None:
    for x in targets:
        tree.delete(x)


def batch_delete_avl(tree: AVLTree, targets: list[int]) -> None:
    for x in targets:
        tree.delete(x)


def build_dataset(n: int, sorted_mode: bool, rng: random.Random) -> list[int]:
    if sorted_mode:
        return list(range(n))
    # Unique random values avoid duplicate-skew in insertion/deletion counts.
    return rng.sample(range(n * 10), n)


def run_one_cycle(
    series_index: int,
    cycle_index: int,
    n: int,
    sorted_mode: bool,
    cfg: BenchmarkConfig,
    rng: random.Random,
) -> CycleResult:
    mode = "sorted" if sorted_mode else "random"
    values = build_dataset(n, sorted_mode, rng)

    bst = BinarySearchTree()
    avl = AVLTree()

    bst_insert_total = measure_total(lambda: batch_insert_bst(bst, values))
    avl_insert_total = measure_total(lambda: batch_insert_avl(avl, values))

    min_v = min(values)
    max_v = max(values)
    search_targets = [rng.randint(min_v, max_v) for _ in range(cfg.search_ops)]

    bst_search_total = measure_total(lambda: batch_search_bst(bst, search_targets))
    avl_search_total = measure_total(lambda: batch_search_avl(avl, search_targets))
    array_search_total = measure_total(lambda: batch_search_array(values, search_targets))

    delete_count = min(cfg.delete_ops, len(values))
    delete_targets = rng.sample(values, delete_count)

    bst_delete_total = measure_total(lambda: batch_delete_bst(bst, delete_targets))
    avl_delete_total = measure_total(lambda: batch_delete_avl(avl, delete_targets))

    return CycleResult(
        series_index=series_index,
        n=n,
        data_mode=mode,
        cycle_index=cycle_index,
        bst_insert_total_s=bst_insert_total,
        bst_search_total_s=bst_search_total,
        bst_search_per_op_s=bst_search_total / cfg.search_ops,
        bst_delete_total_s=bst_delete_total,
        bst_delete_per_op_s=bst_delete_total / delete_count,
        avl_insert_total_s=avl_insert_total,
        avl_search_total_s=avl_search_total,
        avl_search_per_op_s=avl_search_total / cfg.search_ops,
        avl_delete_total_s=avl_delete_total,
        avl_delete_per_op_s=avl_delete_total / delete_count,
        array_search_total_s=array_search_total,
        array_search_per_op_s=array_search_total / cfg.search_ops,
    )


def run_benchmark(cfg: BenchmarkConfig) -> list[CycleResult]:
    rng = random.Random(cfg.seed)
    all_results: list[CycleResult] = []

    total_cycles = cfg.series_count * cfg.cycles_per_series
    completed = 0

    for i in range(cfg.series_count):
        n = 2 ** (cfg.min_exponent + i)
        for cycle in range(cfg.cycles_per_series):
            sorted_mode = cycle >= cfg.random_cycles
            started = time.perf_counter()
            result = run_one_cycle(i + 1, cycle + 1, n, sorted_mode, cfg, rng)
            all_results.append(result)
            completed += 1
            elapsed = time.perf_counter() - started
            mode = "sorted" if sorted_mode else "random"
            print(
                f"[progress] cycle {completed}/{total_cycles}: series={i + 1}, cycle={cycle + 1}, "
                f"n={n}, mode={mode}, elapsed={elapsed:.3f}s",
                flush=True,
            )
    return all_results


def write_raw_results(results: list[CycleResult], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "series_index",
            "n",
            "data_mode",
            "cycle_index",
            "bst_insert_total_s",
            "bst_search_total_s",
            "bst_search_per_op_s",
            "bst_delete_total_s",
            "bst_delete_per_op_s",
            "avl_insert_total_s",
            "avl_search_total_s",
            "avl_search_per_op_s",
            "avl_delete_total_s",
            "avl_delete_per_op_s",
            "array_search_total_s",
            "array_search_per_op_s",
        ])
        for row in results:
            writer.writerow([
                row.series_index,
                row.n,
                row.data_mode,
                row.cycle_index,
                row.bst_insert_total_s,
                row.bst_search_total_s,
                row.bst_search_per_op_s,
                row.bst_delete_total_s,
                row.bst_delete_per_op_s,
                row.avl_insert_total_s,
                row.avl_search_total_s,
                row.avl_search_per_op_s,
                row.avl_delete_total_s,
                row.avl_delete_per_op_s,
                row.array_search_total_s,
                row.array_search_per_op_s,
            ])


def aggregate_results(results: list[CycleResult]) -> list[dict[str, float | int | str]]:
    grouped: dict[tuple[int, int, str], list[CycleResult]] = {}
    for row in results:
        key = (row.series_index, row.n, row.data_mode)
        grouped.setdefault(key, []).append(row)

    aggregated: list[dict[str, float | int | str]] = []
    for (series_index, n, mode), rows in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][2])):
        def m(attr: str) -> float:
            return mean(getattr(r, attr) for r in rows)

        def s(attr: str) -> float:
            values = [getattr(r, attr) for r in rows]
            return pstdev(values) if len(values) > 1 else 0.0

        aggregated.append(
            {
                "series_index": series_index,
                "n": n,
                "data_mode": mode,
                "bst_insert_total_s_mean": m("bst_insert_total_s"),
                "bst_insert_total_s_std": s("bst_insert_total_s"),
                "avl_insert_total_s_mean": m("avl_insert_total_s"),
                "avl_insert_total_s_std": s("avl_insert_total_s"),
                "bst_search_per_op_s_mean": m("bst_search_per_op_s"),
                "bst_search_per_op_s_std": s("bst_search_per_op_s"),
                "avl_search_per_op_s_mean": m("avl_search_per_op_s"),
                "avl_search_per_op_s_std": s("avl_search_per_op_s"),
                "array_search_per_op_s_mean": m("array_search_per_op_s"),
                "array_search_per_op_s_std": s("array_search_per_op_s"),
                "bst_delete_per_op_s_mean": m("bst_delete_per_op_s"),
                "bst_delete_per_op_s_std": s("bst_delete_per_op_s"),
                "avl_delete_per_op_s_mean": m("avl_delete_per_op_s"),
                "avl_delete_per_op_s_std": s("avl_delete_per_op_s"),
            }
        )

    return aggregated


def write_aggregated_results(rows: list[dict[str, float | int | str]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    headers = list(rows[0].keys())
    with output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _extract_mode_rows(
    aggregated_rows: list[dict[str, float | int | str]],
    mode: str,
) -> tuple[list[int], dict[str, list[float]]]:
    filtered = [r for r in aggregated_rows if r["data_mode"] == mode]
    filtered.sort(key=lambda r: int(r["n"]))

    xs = [int(r["n"]) for r in filtered]
    ys = {
        "bst_insert_total_s_mean": [float(r["bst_insert_total_s_mean"]) for r in filtered],
        "avl_insert_total_s_mean": [float(r["avl_insert_total_s_mean"]) for r in filtered],
        "bst_search_per_op_s_mean": [float(r["bst_search_per_op_s_mean"]) for r in filtered],
        "avl_search_per_op_s_mean": [float(r["avl_search_per_op_s_mean"]) for r in filtered],
        "array_search_per_op_s_mean": [float(r["array_search_per_op_s_mean"]) for r in filtered],
        "bst_delete_per_op_s_mean": [float(r["bst_delete_per_op_s_mean"]) for r in filtered],
        "avl_delete_per_op_s_mean": [float(r["avl_delete_per_op_s_mean"]) for r in filtered],
    }
    return xs, ys


def plot_mode(aggregated_rows: list[dict[str, float | int | str]], mode: str, out_file: Path) -> None:
    xs, ys = _extract_mode_rows(aggregated_rows, mode)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(f"Сравнение BST и AVL ({'случайный' if mode == 'random' else 'отсортированный'} набор)")

    axes[0].plot(xs, ys["bst_insert_total_s_mean"], marker="o", label="BST")
    axes[0].plot(xs, ys["avl_insert_total_s_mean"], marker="o", label="AVL")
    axes[0].set_title("Вставка: время всей операции")
    axes[0].set_xlabel("Количество элементов")
    axes[0].set_ylabel("Время, с")
    axes[0].grid(True)
    axes[0].legend()

    axes[1].plot(xs, ys["bst_search_per_op_s_mean"], marker="o", label="BST")
    axes[1].plot(xs, ys["avl_search_per_op_s_mean"], marker="o", label="AVL")
    axes[1].plot(xs, ys["array_search_per_op_s_mean"], marker="o", label="Массив (линейный поиск)")
    axes[1].set_title("Поиск: среднее время 1 операции")
    axes[1].set_xlabel("Количество элементов")
    axes[1].set_ylabel("Время, с")
    axes[1].grid(True)
    axes[1].legend()

    axes[2].plot(xs, ys["bst_delete_per_op_s_mean"], marker="o", label="BST")
    axes[2].plot(xs, ys["avl_delete_per_op_s_mean"], marker="o", label="AVL")
    axes[2].set_title("Удаление: среднее время 1 операции")
    axes[2].set_xlabel("Количество элементов")
    axes[2].set_ylabel("Время, с")
    axes[2].grid(True)
    axes[2].legend()

    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=170)
    plt.close(fig)


def write_report(aggregated_rows: list[dict[str, float | int | str]], out_md: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)

    def best_line(mode: str, key_a: str, key_b: str, label_a: str, label_b: str) -> str:
        rows = [r for r in aggregated_rows if r["data_mode"] == mode]
        if not rows:
            return "Недостаточно данных."
        last = max(rows, key=lambda r: int(r["n"]))
        a = float(last[key_a])
        b = float(last[key_b])
        better = label_a if a < b else label_b
        ratio = (max(a, b) / min(a, b)) if min(a, b) > 0 else float("inf")
        return f"Для n={int(last['n'])}: быстрее {better}, разница примерно в {ratio:.2f}x."

    text = f"""# Отчёт по лабораторной работе: BST и AVL

## Что сделано
- Реализованы две структуры: обычное бинарное дерево поиска (BST) и AVL-дерево.
- Проведены серии тестов в соответствии с методикой задания.
- Построены графики для случайного и отсортированного наборов данных.

## Методика эксперимента
- Количество серий: 10.
- В каждой серии: 20 циклов.
- Размер массива в серии i: 2^(10 + i), где i от 0 до 9.
- Первые 10 циклов: случайный массив.
- Следующие 10 циклов: отсортированный массив (по возрастанию).
- В каждом цикле:
  - Вставка всего массива в BST и AVL (измеряется общее время вставки).
  - 1000 операций поиска случайных значений в BST и AVL (измеряется общее и среднее время 1 операции).
  - 1000 операций поиска в массиве (линейный поиск) для сравнения.
  - 1000 операций удаления из BST и AVL (измеряется общее и среднее время 1 операции).

## Краткие выводы по агрегированным данным
### Случайный набор
- Вставка (BST vs AVL): {best_line('random', 'bst_insert_total_s_mean', 'avl_insert_total_s_mean', 'BST', 'AVL')}
- Поиск (BST vs AVL): {best_line('random', 'bst_search_per_op_s_mean', 'avl_search_per_op_s_mean', 'BST', 'AVL')}
- Удаление (BST vs AVL): {best_line('random', 'bst_delete_per_op_s_mean', 'avl_delete_per_op_s_mean', 'BST', 'AVL')}

### Отсортированный набор
- Вставка (BST vs AVL): {best_line('sorted', 'bst_insert_total_s_mean', 'avl_insert_total_s_mean', 'BST', 'AVL')}
- Поиск (BST vs AVL): {best_line('sorted', 'bst_search_per_op_s_mean', 'avl_search_per_op_s_mean', 'BST', 'AVL')}
- Удаление (BST vs AVL): {best_line('sorted', 'bst_delete_per_op_s_mean', 'avl_delete_per_op_s_mean', 'BST', 'AVL')}

## Интерпретация
- AVL поддерживает логарифмическую высоту дерева за счёт балансировок, поэтому в неблагоприятных входных данных обычно выигрывает в поиске и удалении.
- Обычный BST без балансировки на отсортированном наборе деградирует к структуре, близкой к списку, что ухудшает асимптотику.
- Поиск по массиву линейным проходом растёт пропорционально размеру данных и служит контрольным сравнением.

## Артефакты
- Таблица сырых результатов: outputs/raw_results.csv
- Таблица агрегированных результатов: outputs/aggregated_results.csv
- Графики случайного набора: outputs/plots/random_dataset.png
- Графики отсортированного набора: outputs/plots/sorted_dataset.png
"""
    out_md.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark BST vs AVL according to lab assignment")
    parser.add_argument("--series", type=int, default=10, help="Number of series")
    parser.add_argument("--cycles", type=int, default=20, help="Cycles per series")
    parser.add_argument("--random-cycles", type=int, default=10, help="Random-mode cycles per series")
    parser.add_argument("--search-ops", type=int, default=1000, help="Search operations per cycle")
    parser.add_argument("--delete-ops", type=int, default=1000, help="Delete operations per cycle")
    parser.add_argument("--min-exponent", type=int, default=10, help="Minimum exponent for 2^(min_exponent + i)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", default="outputs", help="Directory for CSV, plots and report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    cfg = BenchmarkConfig(
        series_count=args.series,
        cycles_per_series=args.cycles,
        random_cycles=args.random_cycles,
        search_ops=args.search_ops,
        delete_ops=args.delete_ops,
        min_exponent=args.min_exponent,
        seed=args.seed,
    )

    if cfg.random_cycles > cfg.cycles_per_series:
        raise ValueError("random-cycles cannot exceed cycles")

    output_dir = Path(args.output_dir)

    results = run_benchmark(cfg)
    raw_csv = output_dir / "raw_results.csv"
    write_raw_results(results, raw_csv)

    aggregated = aggregate_results(results)
    agg_csv = output_dir / "aggregated_results.csv"
    write_aggregated_results(aggregated, agg_csv)

    plots_dir = output_dir / "plots"
    plot_mode(aggregated, "random", plots_dir / "random_dataset.png")
    plot_mode(aggregated, "sorted", plots_dir / "sorted_dataset.png")

    write_report(aggregated, output_dir / "REPORT.md")

    print("Benchmark completed.")
    print(f"Raw results: {raw_csv}")
    print(f"Aggregated results: {agg_csv}")
    print(f"Plots: {plots_dir}")
    print(f"Report: {output_dir / 'REPORT.md'}")


if __name__ == "__main__":
    main()
