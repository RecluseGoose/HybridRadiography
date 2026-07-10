#pragma once
#include "_definitions.h"
#include "Buffer.h"
#include <SDL3/SDL.h>



class RenWin {
public:
	RenWin(uint w, uint h);
	~RenWin();
	uint width_, height_;
	void update();
	void show();
	template <typename T> void loadIntoBuffer(Buffer <T> &buffer);
	bool trueUntilQuit();
private:
	void setPixel(int xy, Uint8 red, Uint8 green, Uint8 blue);	
	void setPixel(int xy, Uint8 val);	
	void setPixel(int x, int y, Uint8 red, Uint8 green, Uint8 blue);
	void setPixel(int x, int y, Uint8 val);	
private:
	SDL_Window *window_;
	SDL_Renderer *renderer_;
	SDL_Texture *texture_;
	Buffer<uint> buffer;
private:
	bool SDLinit();
};

template <typename T>
void RenWin::loadIntoBuffer(Buffer <T> &buffer){
	if constexpr(std::is_same_v<T, double>){
		for (unsigned long i = 0; i < buffer.wh; ++i){
			setPixel(i, 255*buffer.buf[i]);
		}
	}
	else{
		static_assert(false, "Unsupported Buffer type loaded into buffer");
	}	
}