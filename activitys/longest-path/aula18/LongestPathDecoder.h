#pragma once
#include <vector>
#include <utility>
#include <stdexcept>

// Grafo não direcionado: cada aresta aparece nas duas listas de adjacência.
using Graph = std::vector<std::vector<std::pair<unsigned, double>>>;

class LongestPathDecoder {
    const Graph& graph;
public:
    explicit LongestPathDecoder(const Graph& graph) : graph(graph) {}

    std::pair<double, std::vector<unsigned>> path(const std::vector<double>& keys) const {
        const unsigned n = graph.size();
        if (keys.size() != n + 1) throw std::invalid_argument("Cromossomo deve ter n+1 chaves");
        if (n == 0) return {0.0, {}};
        // A última chave escolhe o início; as demais priorizam os vizinhos.
        unsigned current = static_cast<unsigned>(keys[n] * n);
        std::vector<bool> visited(n, false);
        std::vector<unsigned> vertices{current};
        visited[current] = true;
        double cost = 0.0, best_cost = 0.0;
        unsigned best_size = 1;
        while (true) {
            unsigned next = n;
            double weight = 0.0;
            for (const auto& edge : graph[current]) {
                unsigned v = edge.first;
                if (visited[v]) continue;
                if (next == n || keys[v] < keys[next] ||
                    (keys[v] == keys[next] && v < next)) {
                    next = v;
                    weight = edge.second;
                }
            }
            if (next == n) break;
            visited[next] = true;
            vertices.push_back(next);
            cost += weight;
            if (cost > best_cost) {
                best_cost = cost;
                best_size = vertices.size();
            }
            current = next;
        }
        // Preserva o melhor prefixo, inclusive quando existem pesos negativos.
        vertices.resize(best_size);
        return {best_cost, vertices};
    }

    double decode(const std::vector<double>& keys) const {
        // A API minimiza: minimizar -custo equivale a maximizar custo.
        return -path(keys).first;
    }
};
