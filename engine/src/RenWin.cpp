#include "_definitions.h"
#include "RenWin.h"
#include <iostream>
#include <SDL3/SDL_events.h>

RenWin::RenWin(uint w, uint h)
: 	window_(NULL),
	renderer_(NULL),
	texture_(NULL),
	buffer(w, h)
{
	width_ = w;
	height_ = h;
	if (!SDLinit()) {
		std::cout << "SDL Init failed with message:" << std::endl;
		std::cout << SDL_GetError() << std::endl;
	}
	buffer.init();
}

RenWin::~RenWin() {
	SDL_DestroyRenderer(renderer_);
	SDL_DestroyTexture(texture_);
	SDL_DestroyWindow(window_);
	SDL_Quit();
}

bool RenWin::SDLinit(){
	if (!SDL_Init(SDL_INIT_VIDEO)) {
		return false;
	}
	window_ = SDL_CreateWindow("hi!", width_, height_, SDL_WINDOW_KEYBOARD_GRABBED);
	if (window_ == NULL) {
		SDL_DestroyWindow(window_);
		SDL_Quit();
		return false;
	}
	renderer_ = SDL_CreateRenderer(window_, NULL); // use default driver
	if (renderer_ == NULL) {
		SDL_DestroyRenderer(renderer_);
		SDL_DestroyWindow(window_);
		SDL_Quit();
		return false;
	}
	texture_ = SDL_CreateTexture(renderer_, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_STATIC, width_, height_);
	if (texture_ == NULL) {
		SDL_DestroyRenderer(renderer_);
		SDL_DestroyTexture(texture_);
		SDL_DestroyWindow(window_);
		SDL_Quit();
		return false;
	}
	return true;
}

void RenWin::update(){
	SDL_UpdateTexture(texture_, NULL, buffer.buf, width_ * sizeof(Uint32));
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
	setPixel(x + y * width_, red, green, blue);
}

void RenWin::setPixel(int x, int y, Uint8 val){
	setPixel(x + y * width_, val);
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