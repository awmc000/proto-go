cmake_minimum_required(VERSION 3.23)
project(PrimeTime LANGUAGES CXX)
include(FetchContent)

FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.12.0
)

FetchContent_MakeAvailable(nlohmann_json)

add_executable(PrimeTime 1.cpp)
target_link_libraries(PrimeTime PRIVATE nlohmann_json::nlohmann_json)
target_compile_features(PrimeTime PRIVATE cxx_std_17)