cmake_minimum_required(VERSION 3.20)
project(matpath LANGUAGES CXX)
include(FetchContent)

option(BUILD_MATPATH_SDL "Add the SDL executable to the build?" ON)
option(BUILD_PYTHON_MODULE "Add the Python dll to the build?" ON)
option(USE_OPENMP "Enable OpenMP acceleration" ON) ## Only used in python module build

## =================== CONFIGURE COMMON DEPENDENCIES ===================
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
    src/glm_support.cpp
)

add_library(matpathlib STATIC ${MATPATH_SOURCES})

FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0
)
FetchContent_MakeAvailable(glm)

target_link_libraries(matpathlib PUBLIC glm::glm)

target_include_directories(matpathlib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_definitions(matpathlib PUBLIC TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../testdata/")

target_compile_features(matpathlib PUBLIC cxx_std_17)

## =================== CONFIGURE matpath ===================
add_executable(matpath
    src/main.cpp
)
target_link_libraries(matpath PRIVATE
    matpathlib
)

## =================== CONFIGURE matpath_sdl ===================
if (BUILD_MATPATH_SDL) 

# Deal with SDL3
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

## =================== CONFIGURE py_matpath ===================
if(BUILD_PYTHON_MODULE)
#set(PYBIND11_FINDPYTHON OLD)

function(set_python_output target)
    set_target_properties(${target} PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
        ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    )
endfunction()

if(DEFINED ENV{MATPATH_TARGET_PYTHON_ENV})
    set(Python_ROOT_DIR
        "$ENV{MATPATH_TARGET_PYTHON_ENV}"
        CACHE PATH ""
        FORCE #!!!!
    )
else()
    message(WARNING
        "Attemping to find a default python directory.\n"
        "Please define MATPATH_TARGET_PYTHON_ENV in environment variables\n"
    )
endif()
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11
    GIT_TAG        v3.0
)

FetchContent_MakeAvailable(pybind11)

# pybind11 method:
pybind11_add_module(py_matpath python/matpath_module.cpp)
set_python_output(py_matpath)

pybind11_add_module(py_rays python/rays_module.cpp)
set_python_output(py_rays)

if(USE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_CXX_FOUND)
        message(STATUS "OpenMP enabled")
        target_link_libraries(py_matpath PRIVATE OpenMP::OpenMP_CXX)
        target_compile_definitions(py_matpath PRIVATE USE_OPENMP)
    else()
        message(WARNING "OpenMP not found. Building single-threaded.")
    endif()
endif()

target_link_libraries(py_matpath PRIVATE
    matpathlib
)

target_link_libraries(py_rays PRIVATE
    matpathlib
)

# Copy over python modules
function(copy_python_module target dest)
    add_custom_command(TARGET ${target} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${dest}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:${target}>
            "${dest}"
    )
endfunction()
copy_python_module(py_matpath "${CMAKE_SOURCE_DIR}/../cpp2p")
copy_python_module(py_rays "${CMAKE_SOURCE_DIR}/../cpp2p")

endif()

get_property(allTargets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
message(STATUS "Targets: ${allTargets}\n")

