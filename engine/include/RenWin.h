#pragma once
#include "_definitions.h"
#include "Buffer.h"
#ifdef INCLUDE_SDL
#include <SDL.h>


class RenWin {
public:
	RenWin(uint w, uint h);
	~RenWin();
	uint WIDTH, HEIGHT;
	void update();
	void setPixel(int x, int y, Uint8 red, Uint8 green, Uint8 blue);
	void show();
	void loadIntoBuffer(Buffer <double> &buffer);
	void loadIntoBuffer(Buffer <uint> &buffer);
	void loadIntoBuffer(Buffer <int> &buffer);
	bool trueUntilQuit();
public:
	bool init();
private:
	bool initialised;
	bool failedInit = false;
	SDL_Window *m_window;
	SDL_Renderer *m_renderer;
	SDL_Texture *m_texture;
	Buffer<uint> buffer;
private:
	bool SDLinit();
};
#else
class RenWin {
public:
	RenWin(uint w, uint h) {};
	~RenWin() {};
	uint WIDTH, HEIGHT;
	void update() {};
	void show() {};
	void loadIntoBuffer(Buffer <double> &buffer) {};
	void loadIntoBuffer(Buffer <uint> &buffer) {};
	void loadIntoBuffer(Buffer <int> &buffer) {};
	bool trueUntilQuit() { return false; };
public:
	bool init() { return true; };
};
#endif