cmake_minimum_required(VERSION 3.20)
project(matpath LANGUAGES CXX)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

set(MATPATH_SOURCES
    src/main.cpp
    src/Buffer.cpp
    src/Detector.cpp
    src/Euler.cpp
    src/FileChecks.cpp
    src/ICPIntersectCaster.cpp
    src/InspecTest.cpp
    src/LengthCalc.cpp
    src/Mesh.cpp
    src/Rasterisation.cpp
    src/RenWin.cpp
    src/STLReader.cpp
    src/VectorMaths.cpp
#    src/material_path.cpp
#    src/material_path2.cpp
#    src/py_module.cpp
)

# Deal with SDL2
include(FetchContent)
FetchContent_Declare(
    SDL
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-2.32.x
)

FetchContent_MakeAvailable(SDL)

# Make both matpath and matpath_sdl projects
foreach (tgt matpath matpath_sdl)
    add_executable(${tgt} ${MATPATH_SOURCES})    
    target_include_directories(${tgt} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_compile_features(${tgt} PRIVATE cxx_std_17)
    set_target_properties(${tgt} PROPERTIES
        CXX_STANDARD 17
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS OFF
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )
endforeach()

target_compile_definitions(matpath_sdl PRIVATE INCLUDE_SDL)
target_compile_definitions(matpath_sdl PRIVATE SDL_MAIN_HANDLED)
target_link_libraries(matpath_sdl PRIVATE SDL2::SDL2)


# Optional: Enable multi-threading if needed
#find_package(Threads REQUIRED)
#target_link_libraries(matpath PRIVATE Threads::Threads)

get_property(allTargets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
message(STATUS "Targets: ${allTargets}")