from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_aggregated(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def mode_rows(rows, mode: str):
    m = [r for r in rows if r["data_mode"] == mode]
    m.sort(key=lambda r: int(r["n"]))
    x = [int(r["n"]) for r in m]
    y = {
        "bst_insert": [float(r["bst_insert_total_s_mean"]) for r in m],
        "avl_insert": [float(r["avl_insert_total_s_mean"]) for r in m],
        "bst_search": [float(r["bst_search_per_op_s_mean"]) for r in m],
        "avl_search": [float(r["avl_search_per_op_s_mean"]) for r in m],
        "arr_search": [float(r["array_search_per_op_s_mean"]) for r in m],
        "bst_delete": [float(r["bst_delete_per_op_s_mean"]) for r in m],
        "avl_delete": [float(r["avl_delete_per_op_s_mean"]) for r in m],
    }
    return x, y


def plot_mode(rows, mode: str, out_file: Path):
    x, y = mode_rows(rows, mode)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    ru_mode = "случайный" if mode == "random" else "отсортированный"
    fig.suptitle(f"Сравнение BST и AVL ({ru_mode} набор)")

    axes[0].plot(x, y["bst_insert"], marker="o", label="BST")
    axes[0].plot(x, y["avl_insert"], marker="o", label="AVL")
    axes[0].set_title("Вставка: время всей операции")
    axes[0].set_xlabel("Количество элементов")
    axes[0].set_ylabel("Время, с")
    axes[0].grid(True)
    axes[0].legend()

    axes[1].plot(x, y["bst_search"], marker="o", label="BST")
    axes[1].plot(x, y["avl_search"], marker="o", label="AVL")
    axes[1].plot(x, y["arr_search"], marker="o", label="Массив (линейный поиск)")
    axes[1].set_title("Поиск: среднее время 1 операции")
    axes[1].set_xlabel("Количество элементов")
    axes[1].set_ylabel("Время, с")
    axes[1].grid(True)
    axes[1].legend()

    axes[2].plot(x, y["bst_delete"], marker="o", label="BST")
    axes[2].plot(x, y["avl_delete"], marker="o", label="AVL")
    axes[2].set_title("Удаление: среднее время 1 операции")
    axes[2].set_xlabel("Количество элементов")
    axes[2].set_ylabel("Время, с")
    axes[2].grid(True)
    axes[2].legend()

    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot benchmark graphs from aggregated CSV")
    parser.add_argument("--input", default="outputs/aggregated_results.csv")
    parser.add_argument("--plots-dir", default="outputs/plots")
    args = parser.parse_args()

    rows = read_aggregated(Path(args.input))
    plots_dir = Path(args.plots_dir)
    plot_mode(rows, "random", plots_dir / "random_dataset.png")
    plot_mode(rows, "sorted", plots_dir / "sorted_dataset.png")

    print("Plots generated:")
    print(plots_dir / "random_dataset.png")
    print(plots_dir / "sorted_dataset.png")


if __name__ == "__main__":
    main()
