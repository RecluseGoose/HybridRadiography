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
	template <typename T> void writeValues(Buffer <T> &buffer);
	bool waitForUserQuit();
private:
	void setPixel(int xy, Uint8 red, Uint8 green, Uint8 blue);	
	void setPixel(int xy, Uint8 val);	
	void setPixel(int x, int y, Uint8 red, Uint8 green, Uint8 blue);
	void setPixel(int x, int y, Uint8 val);	
	bool SDLinit();
private:
	SDL_Window *window_ = nullptr;
	SDL_Renderer *renderer_ = nullptr;
	SDL_Texture *texture_ = nullptr;
	Buffer<uint> buffer;
	bool initSuccess_ = false;	
};

template <typename T>
void RenWin::writeValues(Buffer <T> &buffer){
	if constexpr(std::is_same_v<T, double>){
		for (unsigned long i = 0; i < buffer.wh; ++i){
			setPixel(i, 255*buffer.buf[i]);
		}
	}
	else{
		static_assert(false, "Unsupported Buffer type loaded into buffer");
	}	
}