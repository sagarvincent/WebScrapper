#include <iostream>
#include <fstream>
#include <string>

std::string main() {
    std::ifstream file("filename.html");
    std::string line;

    while(std::getline(file,line)) {
        if(line.find("<") !=std::string::npos) {
            size_t start = line.find("<")+1;
            size_t end = line.find(">");
            std::string tag = line.substr(start, end - start);

        }
    }
}