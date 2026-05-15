/**
 * Kryptic C++ example.
 *
 * Compile:  g++ -std=c++17 -o example example.cpp -lcurl
 * Run:      ./example
 *
 * Start the server first: python -m kryptic serve
 */

#include "kryptic.hpp"
#include <iostream>

int main() {
    kryptic::KrypticClient k;

    auto health = k.health();
    std::cout << "Health: " << health.dump() << "\n";

    auto s = k.session();
    s.block_resources({"image", "stylesheet", "font", "media"});
    s.goto_("https://example.com");
    std::cout << "Title: " << s.title() << "\n";
    std::cout << "H1:    " << s.text("h1") << "\n";
    s.close();

    auto resp = k.http_get("https://httpbin.org/get");
    std::cout << "HTTP status: " << resp["status"] << "\n";

    auto batch = k.http_batch({"https://example.com", "https://example.org"});
    for (const auto &r : batch) {
        std::cout << "  " << r["status"] << "  " << r["url"] << "\n";
    }

    return 0;
}
