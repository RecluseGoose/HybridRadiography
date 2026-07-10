#include "_definitions.h"
#include "RenWin.h"
#include <iostream>

RenWin::RenWin(uint w, uint h) :
	m_window(NULL), m_renderer(NULL), m_texture(NULL){
	if ((SDL_Init(SDL_INIT_VIDEO)) != 0) {
		failedInit = true;
		std::cout << "SDL Init failed :(" << std::endl;
	}
	std::cout << SDL_GetError() << std::endl;
	std::cout << "SDL Init attempted" << std::endl;
	WIDTH = w;
	HEIGHT = h;
	buffer = Buffer<uint>(w, h);
}

RenWin::~RenWin() {
	SDL_DestroyRenderer(m_renderer);
	SDL_DestroyTexture(m_texture);
	SDL_DestroyWindow(m_window);
	SDL_Quit();
}

bool RenWin::init(){
	std::cout << "init level 0" << std::endl;

	if (!initialised) {
		std::cout << "init level 1" << std::endl;
		if (SDLinit()) 
		{
			std::cout << "init level 2" << std::endl;
			buffer.init();
			initialised = true;
			return true;
		}
	}
	return false;	
}

bool RenWin::SDLinit(){
	if (SDL_INIT_VIDEO < 0) {
		std::cout << "SDL_INIT_VIDEO failed" << std::endl;
		return false;
	}
	m_window = SDL_CreateWindow("Inspec", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, WIDTH, HEIGHT, SDL_WINDOW_SHOWN);
	if (m_window == NULL) {
		SDL_DestroyWindow(m_window);
		SDL_Quit();
		std::cout << "SDL_CreateWindow failed" << std::endl;
		return false;
	}
	m_renderer = SDL_CreateRenderer(m_window, -1, SDL_RENDERER_PRESENTVSYNC); // -1 means...?
	if (m_renderer == NULL) {
		SDL_DestroyRenderer(m_renderer);
		SDL_DestroyWindow(m_window);
		SDL_Quit();
		std::cout << "SDL_CreateRenderer failed" << std::endl;
		return false;
	}
	m_texture = SDL_CreateTexture(m_renderer, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_STATIC, WIDTH, HEIGHT);
	if (m_texture == NULL) {
		SDL_DestroyRenderer(m_renderer);
		SDL_DestroyTexture(m_texture);
		SDL_DestroyWindow(m_window);
		SDL_Quit();
		std::cout << "SDL_CreateTexture failed" << std::endl;
		return false;
	}
	return true;
}

void RenWin::update(){
	SDL_UpdateTexture(m_texture, NULL, buffer.buf, WIDTH * sizeof(Uint32));
	SDL_RenderClear(m_renderer);
	SDL_RenderCopy(m_renderer, m_texture, NULL, NULL);
	SDL_RenderPresent(m_renderer);
}


void RenWin::setPixel(int xy, Uint8 red, Uint8 green, Uint8 blue){
	Uint32 color = 0;
	color += red;
	color <<= 8;
	color += green;
	color <<= 8;
	color += blue;
	color <<= 8;
	color += 0xFF;
	buffer.buf[xy] = color;
}

void RenWin::setPixel(int xy, Uint8 val){
	setPixel(xy, val, val, val);
}

void RenWin::setPixel(int x, int y, Uint8 red, Uint8 green, Uint8 blue){
	setPixel(x + y * WIDTH, red, green, blue);
}

void RenWin::setPixel(int x, int y, Uint8 val){
	setPixel(x + y * WIDTH, val);
}

bool RenWin::trueUntilQuit() {
	SDL_Event event;
	while (SDL_PollEvent(&event)) {
		const Uint8 *state = SDL_GetKeyboardState(NULL);
		if ((event.type == SDL_QUIT) || state[SDL_SCANCODE_KP_ENTER] || state[SDL_SCANCODE_RETURN]) {
			return false;			
		}
	}
	return true;
}

void RenWin::show() {
	update();
	const int FPS = 60;
	const int framePeriod = 1000 / FPS; // frame period in ms
}