cmake_minimum_required(VERSION 3.20)
project(matpath LANGUAGES CXX)

option(BUILD_MATPATH_SDL "Add the SDL executable to the build?" ON)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

set(MATPATH_SOURCES
    src/Buffer.cpp
    src/Detector.cpp
    src/Euler.cpp
    src/FileChecks.cpp
    src/ICPIntersectCaster.cpp
    src/InspecTest.cpp
    src/LengthCalc.cpp
    src/Mesh.cpp
    src/Rasterisation.cpp
    src/STLReader.cpp
    src/VectorMaths.cpp
#    src/material_path.cpp
#    src/material_path2.cpp
#    src/py_module.cpp
)

add_library(matpathlib STATIC ${MATPATH_SOURCES})

target_include_directories(matpathlib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_definitions(matpathlib PUBLIC TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../testdata/")

target_compile_features(matpathlib PUBLIC cxx_std_17)

# Make two projects: one with SDL and one without (for use without GUI)
add_executable(matpath
    src/main.cpp
)
target_link_libraries(matpath PRIVATE
    matpathlib
)

if (BUILD_MATPATH_SDL)

# Deal with SDL3
include(FetchContent)
FetchContent_Declare(
    SDL
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-3.4.x
)
FetchContent_MakeAvailable(SDL)

add_executable(matpath_sdl
    src/main_sdl.cpp 
    src/RenWin.cpp
)
target_link_libraries(matpath_sdl PRIVATE
    matpathlib
    SDL3::SDL3
)
target_compile_definitions(matpath_sdl PRIVATE
    INCLUDE_SDL
    SDL_MAIN_HANDLED
)
endif()

# Optional: Enable multi-threading if needed
#find_package(Threads REQUIRED)
#target_link_libraries(matpath PRIVATE Threads::Threads)

get_property(allTargets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
message(STATUS "Targets: ${allTargets}")