#ifndef TELEPLOT_HPP
#define TELEPLOT_HPP
#include <iostream>
#include <vector>
namespace teleplot {
    void plot(std::vector<double> y) {
        std::cout << "{\"datasets\":[{\"name\":\"fig1\",\"data\":[";
        for(int i=0;i<y.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << i << "," << y[i] << "]"; }
        std::cout << "]}]}" << std::endl;
    }
    void plotxy(std::vector<double> x,std::vector<double> y) {
        std::cout << "{\"datasets\":[{\"name\":\"fig1\",\"data\":[";
        for(int i=0;i<y.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << x[i] << "," << y[i] << "]"; }
        std::cout << "]}]}" << std::endl;
    }
    void plot(std::vector<double> y,std::vector<double> y2) {
        std::cout << "{\"datasets\":[";
	std::cout << "{\"name\":\"fig1\",\"data\":[";
        for(int i=0;i<y.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << i << "," << y[i] << "]"; }
        std::cout << "]},";
	std::cout << "{\"name\":\"fig2\",\"data\":[";
        for(int i=0;i<y2.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << i << "," << y2[i] << "]"; }
        std::cout << "]}]}" << std::endl;
    }
    void plotxy(std::vector<double> x,std::vector<double> y,std::vector<double> x2,std::vector<double> y2) {
        std::cout << "{\"datasets\":[{\"name\":\"fig1\",\"data\":[";
        for(int i=0;i<y.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << x[i] << "," << y[i] << "]"; }
        std::cout << "]},";
	std::cout << "{\"name\":\"fig2\",\"data\":[";
        for(int i=0;i<y2.size();i++) {
               if(i>0) std::cout << ",";
               std::cout << "[" << x2[i] << "," << y2[i] << "]"; }
        std::cout << "]}]}" << std::endl;
    }
}
#endif
