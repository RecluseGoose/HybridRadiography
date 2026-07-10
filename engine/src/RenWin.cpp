#include "_definitions.h"
#include "RenWin.h"
#include <iostream>
#include <SDL3/SDL_events.h>

RenWin::RenWin(uint w, uint h) :
	window_(NULL), renderer_(NULL), texture_(NULL){
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
	SDL_DestroyRenderer(renderer_);
	SDL_DestroyTexture(texture_);
	SDL_DestroyWindow(window_);
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
	window_ = SDL_CreateWindow("hi!", WIDTH, HEIGHT, SDL_WINDOW_KEYBOARD_GRABBED);
	if (window_ == NULL) {
		SDL_DestroyWindow(window_);
		SDL_Quit();
		std::cout << "SDL_CreateWindow failed" << std::endl;
		return false;
	}
	renderer_ = SDL_CreateRenderer(window_, NULL); // -1 means...?
	if (renderer_ == NULL) {
		SDL_DestroyRenderer(renderer_);
		SDL_DestroyWindow(window_);
		SDL_Quit();
		std::cout << "SDL_CreateRenderer failed" << std::endl;
		return false;
	}
	texture_ = SDL_CreateTexture(renderer_, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_STATIC, WIDTH, HEIGHT);
	if (texture_ == NULL) {
		SDL_DestroyRenderer(renderer_);
		SDL_DestroyTexture(texture_);
		SDL_DestroyWindow(window_);
		SDL_Quit();
		std::cout << "SDL_CreateTexture failed" << std::endl;
		return false;
	}
	return true;
}

void RenWin::update(){
	SDL_UpdateTexture(texture_, NULL, buffer.buf, WIDTH * sizeof(Uint32));
	SDL_RenderClear(renderer_);
	SDL_RenderTexture(renderer_, texture_, NULL, NULL);
	SDL_RenderPresent(renderer_);
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
		const bool *key_states = SDL_GetKeyboardState(NULL);
		if (event.type == SDL_EVENT_QUIT || (key_states[SDL_SCANCODE_ESCAPE])) {
			return false;			
		}
		SDL_Delay(10);
	}
	return true;
}

void RenWin::show() {
	update();
	const int FPS = 60;
	const int framePeriod = 1000 / FPS; // frame period in ms
}