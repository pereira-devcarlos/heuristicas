#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
#include "LongestPathDecoder.h"
#include <brkgaAPI/BRKGA.h>
#include <brkgaAPI/MTRand.h>

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 4) {
            std::cerr << "Uso: ./brkga instancia [geracoes=100] [semente=0]\n";
            return 1;
        }
        int generations = argc > 2 ? std::stoi(argv[2]) : 100;
        if (generations < 0) throw std::invalid_argument("Geracoes negativas");
        unsigned long seed = argc > 3 ? std::stoul(argv[3]) : 0;
        std::ifstream input(argv[1]);
        int n, m;
        if (!(input >> n >> m) || n < 0 || m < 0)
            throw std::runtime_error("Cabecalho de instancia invalido");
        Graph graph(n);
        for (int i = 0; i < m; ++i) {
            int u, v;
            double weight;
            if (!(input >> u >> v >> weight) || u < 0 || v < 0 || u >= n || v >= n)
                throw std::runtime_error("Aresta invalida; vertices devem estar em [0,n)");
            graph[u].push_back({static_cast<unsigned>(v), weight});
            graph[v].push_back({static_cast<unsigned>(u), weight});
        }
        LongestPathDecoder decoder(graph);
        MTRand rng(seed);
        // 100 indivíduos: 20 elites, 10 mutantes e 70 descendentes.
        BRKGA<LongestPathDecoder, MTRand> algorithm(n + 1, 100, 0.20, 0.10, 0.70, decoder, rng, 1, 1);
        for (int g = 0; g < generations; ++g) algorithm.evolve();
        auto result = decoder.path(algorithm.getBestChromosome());
        std::cout << std::setprecision(17) << "Custo final: " << result.first << "\nCaminho:";
        for (unsigned v : result.second) std::cout << ' ' << v;
        std::cout << "\nNumero de arestas: " << (result.second.empty() ? 0 : result.second.size() - 1) << '\n';
    } catch (const std::exception& error) {
        std::cerr << "Erro: " << error.what() << '\n';
        return 1;
    }
}
