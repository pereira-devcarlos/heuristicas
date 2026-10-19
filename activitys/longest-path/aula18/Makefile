CXX = g++
CXXFLAGS = -O2 -std=c++11 -Wall -Wextra -Wno-unknown-pragmas
BRKGA_DIR ?= external/brkgaAPI

brkga: brkga.cpp LongestPathDecoder.h $(BRKGA_DIR)/brkgaAPI/BRKGA.h $(BRKGA_DIR)/brkgaAPI/Population.h $(BRKGA_DIR)/brkgaAPI/Population.cpp $(BRKGA_DIR)/brkgaAPI/MTRand.h
	$(CXX) $(CXXFLAGS) -I$(BRKGA_DIR) brkga.cpp $(BRKGA_DIR)/brkgaAPI/Population.cpp -o brkga
