#pragma once
#include "_definitions.h"
#include "Buffer.h"
#include <SDL3/SDL.h>

class RenWin {
public:
	RenWin(uint w, uint h);
	~RenWin();
	void update();
	template <typename T> void writeValues(Buffer <T> &buffer);
	bool waitForUserQuit();
private:
	void setPixel(int i, Uint8 red, Uint8 green, Uint8 blue);	
	void setPixel(int i, Uint8 val);	
	void setPixel(int x, int y, Uint8 red, Uint8 green, Uint8 blue);
	void setPixel(int x, int y, Uint8 val);	
	bool SDLinit();
private:
	uint width_, height_;
	SDL_Window *window_ = nullptr;
	SDL_Renderer *renderer_ = nullptr;
	SDL_Texture *texture_ = nullptr;
	Buffer<uint> buffer;
	bool initSuccess_ = false;	
};

template <typename T>
void RenWin::writeValues(Buffer <T> &buffer){
	if constexpr(std::is_same_v<T, double>){
		for (unsigned long i = 0; i < buffer.getLength(); ++i){
			setPixel(i, 255*buffer[i]);
		}
	}
	else{
		static_assert(false, "Unsupported Buffer type loaded into buffer");
	}	
}
