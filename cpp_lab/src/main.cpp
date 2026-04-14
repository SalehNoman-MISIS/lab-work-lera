#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <stack>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;

struct BenchmarkConfig {
    int series_count = 10;
    int cycles_per_series = 20;
    int random_cycles = 10;
    int search_ops = 1000;
    int delete_ops = 1000;
    int min_exponent = 10;
    uint32_t seed = 42;
    fs::path output_dir = "outputs";
};

struct CycleResult {
    int series_index{};
    int n{};
    std::string data_mode;
    int cycle_index{};

    double bst_insert_total_s{};
    double bst_search_total_s{};
    double bst_search_per_op_s{};
    double bst_delete_total_s{};
    double bst_delete_per_op_s{};

    double avl_insert_total_s{};
    double avl_search_total_s{};
    double avl_search_per_op_s{};
    double avl_delete_total_s{};
    double avl_delete_per_op_s{};

    double array_search_total_s{};
    double array_search_per_op_s{};
};

struct AggRow {
    int series_index{};
    int n{};
    std::string data_mode;

    double bst_insert_total_s_mean{};
    double bst_insert_total_s_std{};
    double avl_insert_total_s_mean{};
    double avl_insert_total_s_std{};

    double bst_search_per_op_s_mean{};
    double bst_search_per_op_s_std{};
    double avl_search_per_op_s_mean{};
    double avl_search_per_op_s_std{};
    double array_search_per_op_s_mean{};
    double array_search_per_op_s_std{};

    double bst_delete_per_op_s_mean{};
    double bst_delete_per_op_s_std{};
    double avl_delete_per_op_s_mean{};
    double avl_delete_per_op_s_std{};
};

class BinarySearchTree {
public:
    void insert(int key) {
        if (!root_) {
            root_ = new Node(key);
            ++size_;
            return;
        }

        Node* current = root_;
        while (current) {
            if (key < current->key) {
                if (!current->left) {
                    current->left = new Node(key);
                    ++size_;
                    return;
                }
                current = current->left;
            } else if (key > current->key) {
                if (!current->right) {
                    current->right = new Node(key);
                    ++size_;
                    return;
                }
                current = current->right;
            } else {
                return;
            }
        }
    }

    bool search(int key) const {
        Node* current = root_;
        while (current) {
            if (key < current->key) {
                current = current->left;
            } else if (key > current->key) {
                current = current->right;
            } else {
                return true;
            }
        }
        return false;
    }

    void erase(int key) {
        Node* parent = nullptr;
        Node* current = root_;

        while (current && current->key != key) {
            parent = current;
            current = (key < current->key) ? current->left : current->right;
        }
        if (!current) {
            return;
        }

        if (current->left && current->right) {
            Node* succ_parent = current;
            Node* succ = current->right;
            while (succ->left) {
                succ_parent = succ;
                succ = succ->left;
            }
            current->key = succ->key;
            parent = succ_parent;
            current = succ;
        }

        Node* child = current->left ? current->left : current->right;
        if (!parent) {
            root_ = child;
        } else if (parent->left == current) {
            parent->left = child;
        } else {
            parent->right = child;
        }

        delete current;
        --size_;
    }

    ~BinarySearchTree() { clear(root_); }

private:
    struct Node {
        explicit Node(int k) : key(k) {}
        int key;
        Node* left = nullptr;
        Node* right = nullptr;
    };

    Node* root_ = nullptr;
    size_t size_ = 0;

    void clear(Node* n) {
        if (!n) {
            return;
        }
        std::stack<Node*> st;
        st.push(n);
        while (!st.empty()) {
            Node* cur = st.top();
            st.pop();
            if (cur->left) {
                st.push(cur->left);
            }
            if (cur->right) {
                st.push(cur->right);
            }
            delete cur;
        }
    }
};

class AVLTree {
public:
    void insert(int key) {
        bool inserted = false;
        root_ = insert_rec(root_, key, inserted);
        if (inserted) {
            ++size_;
        }
    }

    bool search(int key) const {
        Node* cur = root_;
        while (cur) {
            if (key < cur->key) {
                cur = cur->left;
            } else if (key > cur->key) {
                cur = cur->right;
            } else {
                return true;
            }
        }
        return false;
    }

    void erase(int key) {
        bool erased = false;
        root_ = erase_rec(root_, key, erased);
        if (erased) {
            --size_;
        }
    }

    ~AVLTree() { clear(root_); }

private:
    struct Node {
        explicit Node(int k) : key(k) {}
        int key;
        int height = 1;
        Node* left = nullptr;
        Node* right = nullptr;
    };

    Node* root_ = nullptr;
    size_t size_ = 0;

    static int h(Node* n) { return n ? n->height : 0; }

    static void update_height(Node* n) {
        n->height = 1 + std::max(h(n->left), h(n->right));
    }

    static int balance_factor(Node* n) {
        return h(n->left) - h(n->right);
    }

    static Node* rotate_left(Node* z) {
        Node* y = z->right;
        Node* t2 = y->left;

        y->left = z;
        z->right = t2;

        update_height(z);
        update_height(y);
        return y;
    }

    static Node* rotate_right(Node* z) {
        Node* y = z->left;
        Node* t3 = y->right;

        y->right = z;
        z->left = t3;

        update_height(z);
        update_height(y);
        return y;
    }

    static Node* rebalance(Node* node) {
        const int bf = balance_factor(node);
        if (bf > 1) {
            if (balance_factor(node->left) < 0) {
                node->left = rotate_left(node->left);
            }
            return rotate_right(node);
        }
        if (bf < -1) {
            if (balance_factor(node->right) > 0) {
                node->right = rotate_right(node->right);
            }
            return rotate_left(node);
        }
        return node;
    }

    static Node* insert_rec(Node* node, int key, bool& inserted) {
        if (!node) {
            inserted = true;
            return new Node(key);
        }

        if (key < node->key) {
            node->left = insert_rec(node->left, key, inserted);
        } else if (key > node->key) {
            node->right = insert_rec(node->right, key, inserted);
        } else {
            return node;
        }

        update_height(node);
        return rebalance(node);
    }

    static Node* min_node(Node* node) {
        Node* cur = node;
        while (cur->left) {
            cur = cur->left;
        }
        return cur;
    }

    static Node* erase_rec(Node* node, int key, bool& erased) {
        if (!node) {
            return nullptr;
        }

        if (key < node->key) {
            node->left = erase_rec(node->left, key, erased);
        } else if (key > node->key) {
            node->right = erase_rec(node->right, key, erased);
        } else {
            erased = true;
            if (!node->left || !node->right) {
                Node* child = node->left ? node->left : node->right;
                delete node;
                return child;
            }
            Node* succ = min_node(node->right);
            node->key = succ->key;
            bool removed_succ = false;
            node->right = erase_rec(node->right, succ->key, removed_succ);
        }

        update_height(node);
        return rebalance(node);
    }

    void clear(Node* n) {
        if (!n) {
            return;
        }
        std::stack<Node*> st;
        st.push(n);
        while (!st.empty()) {
            Node* cur = st.top();
            st.pop();
            if (cur->left) {
                st.push(cur->left);
            }
            if (cur->right) {
                st.push(cur->right);
            }
            delete cur;
        }
    }
};

template <typename Fn>
double measure_total(Fn&& fn) {
    const auto start = Clock::now();
    fn();
    const auto end = Clock::now();
    return std::chrono::duration<double>(end - start).count();
}

bool linear_search(const std::vector<int>& values, int target) {
    for (int x : values) {
        if (x == target) {
            return true;
        }
    }
    return false;
}

std::vector<int> build_dataset(int n, bool sorted_mode, std::mt19937& rng) {
    std::vector<int> values(n);
    if (sorted_mode) {
        std::iota(values.begin(), values.end(), 0);
        return values;
    }

    std::iota(values.begin(), values.end(), 0);
    std::shuffle(values.begin(), values.end(), rng);
    return values;
}

CycleResult run_one_cycle(
    int series_index,
    int cycle_index,
    int n,
    bool sorted_mode,
    const BenchmarkConfig& cfg,
    std::mt19937& rng
) {
    const std::string mode = sorted_mode ? "sorted" : "random";
    auto values = build_dataset(n, sorted_mode, rng);

    BinarySearchTree bst;
    AVLTree avl;

    const double bst_insert_total = measure_total([&]() {
        for (int v : values) {
            bst.insert(v);
        }
    });

    const double avl_insert_total = measure_total([&]() {
        for (int v : values) {
            avl.insert(v);
        }
    });

    std::uniform_int_distribution<int> dist(0, n - 1);
    std::vector<int> search_targets;
    search_targets.reserve(static_cast<size_t>(cfg.search_ops));
    for (int i = 0; i < cfg.search_ops; ++i) {
        search_targets.push_back(dist(rng));
    }

    const double bst_search_total = measure_total([&]() {
        for (int x : search_targets) {
            bst.search(x);
        }
    });

    const double avl_search_total = measure_total([&]() {
        for (int x : search_targets) {
            avl.search(x);
        }
    });

    const double array_search_total = measure_total([&]() {
        for (int x : search_targets) {
            linear_search(values, x);
        }
    });

    const int delete_count = std::min(cfg.delete_ops, static_cast<int>(values.size()));
    std::vector<int> delete_targets = values;
    std::shuffle(delete_targets.begin(), delete_targets.end(), rng);
    delete_targets.resize(static_cast<size_t>(delete_count));

    const double bst_delete_total = measure_total([&]() {
        for (int x : delete_targets) {
            bst.erase(x);
        }
    });

    const double avl_delete_total = measure_total([&]() {
        for (int x : delete_targets) {
            avl.erase(x);
        }
    });

    CycleResult r;
    r.series_index = series_index;
    r.n = n;
    r.data_mode = mode;
    r.cycle_index = cycle_index;

    r.bst_insert_total_s = bst_insert_total;
    r.bst_search_total_s = bst_search_total;
    r.bst_search_per_op_s = bst_search_total / static_cast<double>(cfg.search_ops);
    r.bst_delete_total_s = bst_delete_total;
    r.bst_delete_per_op_s = bst_delete_total / static_cast<double>(delete_count);

    r.avl_insert_total_s = avl_insert_total;
    r.avl_search_total_s = avl_search_total;
    r.avl_search_per_op_s = avl_search_total / static_cast<double>(cfg.search_ops);
    r.avl_delete_total_s = avl_delete_total;
    r.avl_delete_per_op_s = avl_delete_total / static_cast<double>(delete_count);

    r.array_search_total_s = array_search_total;
    r.array_search_per_op_s = array_search_total / static_cast<double>(cfg.search_ops);

    return r;
}

std::string to_key(int series_index, int n, const std::string& mode) {
    return std::to_string(series_index) + "|" + std::to_string(n) + "|" + mode;
}

std::pair<double, double> mean_std(const std::vector<double>& values) {
    if (values.empty()) {
        return {0.0, 0.0};
    }
    const double mean = std::accumulate(values.begin(), values.end(), 0.0) / static_cast<double>(values.size());
    double var = 0.0;
    for (double x : values) {
        const double d = x - mean;
        var += d * d;
    }
    var /= static_cast<double>(values.size());
    return {mean, std::sqrt(var)};
}

void write_raw_results(const std::vector<CycleResult>& rows, const fs::path& out_file) {
    std::ofstream out(out_file);
    out << std::setprecision(15);
    out << "series_index,n,data_mode,cycle_index,"
        << "bst_insert_total_s,bst_search_total_s,bst_search_per_op_s,"
        << "bst_delete_total_s,bst_delete_per_op_s,"
        << "avl_insert_total_s,avl_search_total_s,avl_search_per_op_s,"
        << "avl_delete_total_s,avl_delete_per_op_s,"
        << "array_search_total_s,array_search_per_op_s\n";

    for (const auto& r : rows) {
        out << r.series_index << ',' << r.n << ',' << r.data_mode << ',' << r.cycle_index << ','
            << r.bst_insert_total_s << ',' << r.bst_search_total_s << ',' << r.bst_search_per_op_s << ','
            << r.bst_delete_total_s << ',' << r.bst_delete_per_op_s << ','
            << r.avl_insert_total_s << ',' << r.avl_search_total_s << ',' << r.avl_search_per_op_s << ','
            << r.avl_delete_total_s << ',' << r.avl_delete_per_op_s << ','
            << r.array_search_total_s << ',' << r.array_search_per_op_s << '\n';
    }
}

std::vector<AggRow> aggregate_results(const std::vector<CycleResult>& rows) {
    struct Bucket {
        int series_index{};
        int n{};
        std::string mode;
        std::vector<double> bst_insert;
        std::vector<double> avl_insert;
        std::vector<double> bst_search;
        std::vector<double> avl_search;
        std::vector<double> array_search;
        std::vector<double> bst_delete;
        std::vector<double> avl_delete;
    };

    std::unordered_map<std::string, Bucket> buckets;
    for (const auto& r : rows) {
        const std::string key = to_key(r.series_index, r.n, r.data_mode);
        auto& b = buckets[key];
        b.series_index = r.series_index;
        b.n = r.n;
        b.mode = r.data_mode;

        b.bst_insert.push_back(r.bst_insert_total_s);
        b.avl_insert.push_back(r.avl_insert_total_s);
        b.bst_search.push_back(r.bst_search_per_op_s);
        b.avl_search.push_back(r.avl_search_per_op_s);
        b.array_search.push_back(r.array_search_per_op_s);
        b.bst_delete.push_back(r.bst_delete_per_op_s);
        b.avl_delete.push_back(r.avl_delete_per_op_s);
    }

    std::vector<AggRow> out;
    out.reserve(buckets.size());

    for (auto& kv : buckets) {
        const auto& b = kv.second;
        AggRow row;
        row.series_index = b.series_index;
        row.n = b.n;
        row.data_mode = b.mode;

        std::tie(row.bst_insert_total_s_mean, row.bst_insert_total_s_std) = mean_std(b.bst_insert);
        std::tie(row.avl_insert_total_s_mean, row.avl_insert_total_s_std) = mean_std(b.avl_insert);

        std::tie(row.bst_search_per_op_s_mean, row.bst_search_per_op_s_std) = mean_std(b.bst_search);
        std::tie(row.avl_search_per_op_s_mean, row.avl_search_per_op_s_std) = mean_std(b.avl_search);
        std::tie(row.array_search_per_op_s_mean, row.array_search_per_op_s_std) = mean_std(b.array_search);

        std::tie(row.bst_delete_per_op_s_mean, row.bst_delete_per_op_s_std) = mean_std(b.bst_delete);
        std::tie(row.avl_delete_per_op_s_mean, row.avl_delete_per_op_s_std) = mean_std(b.avl_delete);

        out.push_back(row);
    }

    std::sort(out.begin(), out.end(), [](const AggRow& a, const AggRow& b) {
        if (a.series_index != b.series_index) {
            return a.series_index < b.series_index;
        }
        return a.data_mode < b.data_mode;
    });

    return out;
}

void write_aggregated_results(const std::vector<AggRow>& rows, const fs::path& out_file) {
    std::ofstream out(out_file);
    out << std::setprecision(15);
    out << "series_index,n,data_mode,"
        << "bst_insert_total_s_mean,bst_insert_total_s_std,"
        << "avl_insert_total_s_mean,avl_insert_total_s_std,"
        << "bst_search_per_op_s_mean,bst_search_per_op_s_std,"
        << "avl_search_per_op_s_mean,avl_search_per_op_s_std,"
        << "array_search_per_op_s_mean,array_search_per_op_s_std,"
        << "bst_delete_per_op_s_mean,bst_delete_per_op_s_std,"
        << "avl_delete_per_op_s_mean,avl_delete_per_op_s_std\n";

    for (const auto& r : rows) {
        out << r.series_index << ',' << r.n << ',' << r.data_mode << ','
            << r.bst_insert_total_s_mean << ',' << r.bst_insert_total_s_std << ','
            << r.avl_insert_total_s_mean << ',' << r.avl_insert_total_s_std << ','
            << r.bst_search_per_op_s_mean << ',' << r.bst_search_per_op_s_std << ','
            << r.avl_search_per_op_s_mean << ',' << r.avl_search_per_op_s_std << ','
            << r.array_search_per_op_s_mean << ',' << r.array_search_per_op_s_std << ','
            << r.bst_delete_per_op_s_mean << ',' << r.bst_delete_per_op_s_std << ','
            << r.avl_delete_per_op_s_mean << ',' << r.avl_delete_per_op_s_std << '\n';
    }
}

void write_report(const std::vector<AggRow>& rows, const fs::path& out_file) {
    auto best_line = [&](const std::string& mode, auto getter_a, auto getter_b, const std::string& a_name, const std::string& b_name) {
        std::vector<AggRow> filtered;
        for (const auto& r : rows) {
            if (r.data_mode == mode) {
                filtered.push_back(r);
            }
        }
        if (filtered.empty()) {
            return std::string("Недостаточно данных.");
        }
        auto it = std::max_element(filtered.begin(), filtered.end(), [](const AggRow& x, const AggRow& y) {
            return x.n < y.n;
        });
        const double a = getter_a(*it);
        const double b = getter_b(*it);
        const std::string better = (a < b) ? a_name : b_name;
        const double ratio = (std::min(a, b) > 0.0) ? (std::max(a, b) / std::min(a, b)) : 0.0;

        std::ostringstream oss;
        oss << "Для n=" << it->n << ": быстрее " << better << ", разница примерно в " << std::fixed
            << std::setprecision(2) << ratio << "x.";
        return oss.str();
    };

    std::ofstream out(out_file);
    out << "# Отчёт по лабораторной работе: BST и AVL (C++)\n\n";
    out << "## Что сделано\n";
    out << "- Реализованы BST и AVL на C++.\n";
    out << "- Проведены серии тестов согласно параметрам запуска.\n";
    out << "- Получены CSV-результаты и подготовлены данные для графиков.\n\n";

    out << "## Краткие выводы по агрегированным данным\n";
    out << "### Случайный набор\n";
    out << "- Вставка: "
        << best_line("random", [](const AggRow& r) { return r.bst_insert_total_s_mean; },
                     [](const AggRow& r) { return r.avl_insert_total_s_mean; }, "BST", "AVL") << "\n";
    out << "- Поиск: "
        << best_line("random", [](const AggRow& r) { return r.bst_search_per_op_s_mean; },
                     [](const AggRow& r) { return r.avl_search_per_op_s_mean; }, "BST", "AVL") << "\n";
    out << "- Удаление: "
        << best_line("random", [](const AggRow& r) { return r.bst_delete_per_op_s_mean; },
                     [](const AggRow& r) { return r.avl_delete_per_op_s_mean; }, "BST", "AVL") << "\n\n";

    out << "### Отсортированный набор\n";
    out << "- Вставка: "
        << best_line("sorted", [](const AggRow& r) { return r.bst_insert_total_s_mean; },
                     [](const AggRow& r) { return r.avl_insert_total_s_mean; }, "BST", "AVL") << "\n";
    out << "- Поиск: "
        << best_line("sorted", [](const AggRow& r) { return r.bst_search_per_op_s_mean; },
                     [](const AggRow& r) { return r.avl_search_per_op_s_mean; }, "BST", "AVL") << "\n";
    out << "- Удаление: "
        << best_line("sorted", [](const AggRow& r) { return r.bst_delete_per_op_s_mean; },
                     [](const AggRow& r) { return r.avl_delete_per_op_s_mean; }, "BST", "AVL") << "\n\n";

    out << "## Артефакты\n";
    out << "- outputs/raw_results.csv\n";
    out << "- outputs/aggregated_results.csv\n";
    out << "- outputs/plots/random_dataset.png\n";
    out << "- outputs/plots/sorted_dataset.png\n";
    out << "- outputs/REPORT.md\n";
}

BenchmarkConfig parse_args(int argc, char** argv) {
    BenchmarkConfig cfg;

    auto read_int = [&](int& idx) -> int {
        if (idx + 1 >= argc) {
            throw std::runtime_error("Missing value for argument " + std::string(argv[idx]));
        }
        ++idx;
        return std::stoi(argv[idx]);
    };

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--series") {
            cfg.series_count = read_int(i);
        } else if (arg == "--cycles") {
            cfg.cycles_per_series = read_int(i);
        } else if (arg == "--random-cycles") {
            cfg.random_cycles = read_int(i);
        } else if (arg == "--search-ops") {
            cfg.search_ops = read_int(i);
        } else if (arg == "--delete-ops") {
            cfg.delete_ops = read_int(i);
        } else if (arg == "--min-exponent") {
            cfg.min_exponent = read_int(i);
        } else if (arg == "--seed") {
            cfg.seed = static_cast<uint32_t>(read_int(i));
        } else if (arg == "--output-dir") {
            if (i + 1 >= argc) {
                throw std::runtime_error("Missing value for --output-dir");
            }
            ++i;
            cfg.output_dir = argv[i];
        } else {
            throw std::runtime_error("Unknown argument: " + arg);
        }
    }

    if (cfg.random_cycles > cfg.cycles_per_series) {
        throw std::runtime_error("--random-cycles cannot exceed --cycles");
    }
    if (cfg.search_ops <= 0 || cfg.delete_ops <= 0 || cfg.series_count <= 0 || cfg.cycles_per_series <= 0) {
        throw std::runtime_error("All count arguments must be positive");
    }

    return cfg;
}

int main(int argc, char** argv) {
    try {
        const BenchmarkConfig cfg = parse_args(argc, argv);
        fs::create_directories(cfg.output_dir);

        std::mt19937 rng(cfg.seed);
        std::vector<CycleResult> raw_rows;
        raw_rows.reserve(static_cast<size_t>(cfg.series_count * cfg.cycles_per_series));

        const int total_cycles = cfg.series_count * cfg.cycles_per_series;
        int completed = 0;

        for (int s = 0; s < cfg.series_count; ++s) {
            const int n = 1 << (cfg.min_exponent + s);
            for (int c = 0; c < cfg.cycles_per_series; ++c) {
                const bool sorted_mode = (c >= cfg.random_cycles);
                const auto t0 = Clock::now();

                raw_rows.push_back(run_one_cycle(s + 1, c + 1, n, sorted_mode, cfg, rng));

                ++completed;
                const auto t1 = Clock::now();
                const double elapsed = std::chrono::duration<double>(t1 - t0).count();
                std::cout << "[progress] cycle " << completed << "/" << total_cycles
                          << ": series=" << (s + 1)
                          << ", cycle=" << (c + 1)
                          << ", n=" << n
                          << ", mode=" << (sorted_mode ? "sorted" : "random")
                          << ", elapsed=" << std::fixed << std::setprecision(3) << elapsed << "s\n";
                std::cout.flush();
            }
        }

        const fs::path raw_csv = cfg.output_dir / "raw_results.csv";
        write_raw_results(raw_rows, raw_csv);

        const auto agg_rows = aggregate_results(raw_rows);
        const fs::path agg_csv = cfg.output_dir / "aggregated_results.csv";
        write_aggregated_results(agg_rows, agg_csv);

        const fs::path report_md = cfg.output_dir / "REPORT.md";
        write_report(agg_rows, report_md);

        std::cout << "Benchmark completed.\n";
        std::cout << "Raw results: " << raw_csv.string() << "\n";
        std::cout << "Aggregated results: " << agg_csv.string() << "\n";
        std::cout << "Report: " << report_md.string() << "\n";
        std::cout << "Use scripts/plot_results.py to generate PNG plots from aggregated CSV.\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << "\n";
        return 1;
    }
}
